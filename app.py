import csv
import re
import sqlite3
import unicodedata
from pathlib import Path
from flask import Flask, request, render_template # type: ignore
from huggingface_hub import hf_hub_download # type: ignore
from llama_cpp import Llama # type: ignore

app = Flask(__name__)

# Anchored directly to the N-dine-lang-translator/ directory
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
DB_DIR = BASE_DIR / "db"
CSV_DIR = BASE_DIR / "csv"
DB_PATH = DB_DIR / "dine_lex.db"

for folder in (MODEL_DIR, DB_DIR, CSV_DIR):
    folder.mkdir(parents=True, exist_ok=True)

# Stringent testing constraints aligned with official Core Architecture (T S V O L)
MAX_SENTENCE_WORDS = 12
VALID_OPENING_PREFIXES = ("T-", "Q-", "C-", "M-")
VALID_SLOT_PREFIXES = ("T-", "Q-", "C-", "M-", "S-", "V-", "O-", "L-")
SLOT_ORDER = {
    "T-": 1, "Q-": 1, "C-": 1, "M-": 1,
    "S-": 2,
    "V-": 3,
    "O-": 4,
    "L-": 5,
}

# Offline-first GGUF loading
MODEL_FILENAME = "gemma3-1b-ndine-Q4_K_M.gguf"
model_path = MODEL_DIR / MODEL_FILENAME
if not model_path.exists():
    raise FileNotFoundError(
        f"Missing model file: {model_path}\n"
        f"Copy {MODEL_FILENAME} from N-dine-lang-studio/models/ into {MODEL_DIR}/ and restart app.py."
    )

llm = Llama(
    model_path=str(model_path),
    n_ctx=2048,
    n_threads=4,
    verbose=False
)


def strip_diacritics_ascii(text):
    if not text:
        return ""
    for k, v in {"ł": "l", "Ł": "L", "’": "", "'": "", "ʼ": "", "`": ""}.items():
        text = text.replace(k, v)
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").strip()


def normalize_gloss(text):
    return re.sub(r"[.,;!?\"\'()]+", " ", text.lower()).strip()


def validate_tsvol_slots(ndine_text):
    """Validates canonical T S V O L structure: [T/Q/C/M] -> S -> V -> (O) -> (L)."""
    cleaned = (ndine_text or "").strip().rstrip(".")
    if not cleaned:
        return False, "N-dine-lang sequence is empty."

    tokens = cleaned.split()
    if not tokens[0].upper().startswith(VALID_OPENING_PREFIXES):
        return False, f"Must begin with [T/Q/C/M]- tag. Got: '{tokens[0]}'"

    seen_ranks = []
    has_s = False
    has_v = False

    for tok in tokens:
        upper = tok.upper()
        matched_prefix = next((p for p in VALID_SLOT_PREFIXES if upper.startswith(p)), None)
        if not matched_prefix:
            return False, f"Invalid slot tag '{tok}'. Allowed: T-, Q-, C-, M-, S-, V-, O-, L-."

        rank = SLOT_ORDER[matched_prefix]
        if seen_ranks:
            if rank == seen_ranks[-1]:
                return False, f"Duplicate slot role '{matched_prefix}' in '{tok}'."
            if rank < seen_ranks[-1]:
                return False, f"Out-of-order slot '{tok}'. Must follow canonical T S V O L order."

        seen_ranks.append(rank)
        if matched_prefix == "S-":
            has_s = True
        elif matched_prefix == "V-":
            has_v = True

    if not (has_s and has_v):
        return False, "Incomplete clause: N-dine-lang sentence requires both S- (subject) and V- (verb)."

    return True, "Valid canonical T S V O L structure."


def load_csv_examples():
    rows = []
    for csv_file in sorted(CSV_DIR.glob("*.csv")):
        try:
            with open(csv_file, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dine_ascii = (row.get("dine_ascii") or "").strip()
                    english = (row.get("english") or "").strip()
                    n_dine = (row.get("n_dine_lang") or "").strip()
                    if english and n_dine:
                        rows.append({
                            "dine_ascii": dine_ascii,
                            "english": english,
                            "n_dine": n_dine
                        })
        except Exception:
            continue
    return rows


def lookup_lexicon_direct(query_text):
    """Direct DB lookup for single words or standalone noun phrases (e.g., 'Necktie', 'Horse blanket')."""
    clean_query = normalize_gloss(query_text)
    if not clean_query or not DB_PATH.exists():
        return []

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, dine_raw, dine_ascii, english, n_dine_full
        FROM lexicon
        WHERE LOWER(english) LIKE ?
    """, (f"%{clean_query}%",))
    candidates = cur.fetchall()
    conn.close()

    exact_matches = []
    synonym_matches = []
    for row in candidates:
        _, _, _, english, _ = row
        norm_full = normalize_gloss(english)
        segments = [normalize_gloss(seg) for seg in re.split(r"[;,]", english)]
        if norm_full == clean_query:
            exact_matches.append(row)
        elif clean_query in segments:
            synonym_matches.append(row)

    return exact_matches + synonym_matches


def lookup_slot_lexicon_refs(ndine_text):
    """Pulls clean concept -> dine_ascii mappings for Step 2 prompt + full display details for UI."""
    if not DB_PATH.exists():
        return [], []

    ignored = {
        "1sg", "2sg", "3sg", "1pl", "2pl", "3pl",
        "prs", "pst", "fut", "habitual", "imp", "hort", "now", "at", "in", "on", "the"
    }

    concepts = []
    for tok in ndine_text.rstrip(".").split():
        if "-" not in tok:
            continue
        prefix, body = tok.split("-", 1)
        if prefix.upper() in ("T", "Q", "C", "M"):
            continue
        words = [
            re.sub(r"[^a-zA-Z]", "", w).lower()
            for w in body.split("-")
        ]
        words = [w for w in words if len(w) > 2 and w not in ignored]
        if len(words) > 1:
            phrase = " ".join(words)
            if phrase not in concepts:
                concepts.append(phrase)
        for w in words:
            if w not in concepts:
                concepts.append(w)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    prompt_pairs = []
    ui_details = []

    for concept in concepts[:6]:
        cur.execute("""
            SELECT dine_raw, dine_ascii, english
            FROM lexicon
            WHERE LOWER(english) LIKE ?
            ORDER BY is_phrase ASC, LENGTH(english) ASC
            LIMIT 30
        """, (f"%{concept}%",))
        best_match = None
        for dine_raw, dine_ascii, english in cur.fetchall():
            norm = normalize_gloss(english)
            segments = [normalize_gloss(s) for s in re.split(r"[;,]", english)]
            if norm == concept or concept in segments:
                best_match = (dine_raw, dine_ascii, english)
                break
            if best_match is None and re.search(rf"\b{re.escape(concept)}\b", norm):
                best_match = (dine_raw, dine_ascii, english)

        if best_match:
            dine_raw, dine_ascii, english = best_match
            clean_ascii = strip_diacritics_ascii(dine_ascii)
            # Clean mapping only for Gemma so long English glosses never leak into output
            prompt_pairs.append(f"{concept} -> {clean_ascii}")
            # Full detail for UI verification box
            ui_details.append(f"{concept}: {clean_ascii} ({dine_raw}) — {english}")

    conn.close()
    return prompt_pairs, ui_details


def step1_english_to_ndine(english_text):
    prompt = f"""Convert the short English sentence into canonical N-dine-lang T S V O L slots.
Canonical order: [T/Q/C/M]-[time] S-[subject] V-[verb] O-[object] L-[location]
Output ONLY the N-dine-lang slot sequence.

English: {english_text}
N-dine-lang:"""

    resp = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=96,
        temperature=0.0
    )
    raw = resp["choices"][0]["message"]["content"].strip()
    raw = re.sub(r"^(N-dine-lang|Output)\s*:\s*", "", raw, flags=re.IGNORECASE).strip()
    return raw.splitlines()[0].strip()


def step2_ndine_to_dine_ascii(ndine_text):
    prompt_pairs, ui_details = lookup_slot_lexicon_refs(ndine_text)
    lex_block = "\n".join(prompt_pairs) if prompt_pairs else "(None)"

    prompt = f"""Translate the N-dine-lang T S V O L sequence into Diné (ASCII) using the dictionary roots.
Output ONLY the Diné (ASCII) words with no English definitions, no apostrophes, and no diacritics.

Dictionary Roots (concept -> Dine ASCII):
{lex_block}

N-dine-lang: {ndine_text}
Dine ASCII:"""

    resp = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=110,
        temperature=0.0
    )
    raw = resp["choices"][0]["message"]["content"].strip()
    raw = re.sub(r"^(Dine ASCII|Output)\s*:\s*", "", raw, flags=re.IGNORECASE).strip()
    return strip_diacritics_ascii(raw.splitlines()[0].strip()), ui_details


def get_db_count():
    if not DB_PATH.exists():
        return 0
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM lexicon")
    count = cur.fetchone()[0]
    conn.close()
    return count


@app.route("/", methods=["GET", "POST"])
def index():
    mode = request.args.get("mode", "single")
    if mode not in ("single", "sentence"):
        mode = "single"

    action = ""
    english_input = ""
    ndine_output = ""
    dine_ascii_output = ""
    single_matches = None
    lex_refs = []
    error_msg = ""
    slot_check_ok = False
    slot_check_msg = ""

    if request.method == "POST":
        mode = request.form.get("mode", "single")
        action = request.form.get("action", "")
        english_input = request.form.get("english_input", "").strip()
        ndine_output = request.form.get("ndine_output", "").strip()
        words = [w for w in english_input.split() if w.strip()]

        if mode == "single":
            if len(words) < 1 or len(words) > 4:
                error_msg = f"Word / Noun Phrase Mode: Please enter 1 to 4 words (you entered {len(words)})."
            else:
                single_matches = lookup_lexicon_direct(english_input)

        elif mode == "sentence":
            if len(words) < 2 or len(words) > MAX_SENTENCE_WORDS:
                error_msg = f"Short-Sentence Mode: Please enter between 2 and {MAX_SENTENCE_WORDS} words (you entered {len(words)})."
            elif action == "step1":
                direct_hit = lookup_lexicon_direct(english_input) if len(words) <= 4 else []
                if direct_hit:
                    single_matches = direct_hit
                    error_msg = "Found exact noun phrase match in db/dine_lex.db (no T S V O L sentence conversion needed)."
                else:
                    ndine_output = step1_english_to_ndine(english_input)
                    slot_check_ok, slot_check_msg = validate_tsvol_slots(ndine_output)
            elif action == "step2":
                slot_check_ok, slot_check_msg = validate_tsvol_slots(ndine_output)
                if not slot_check_ok:
                    error_msg = f"Step 2 blocked — {slot_check_msg}"
                else:
                    dine_ascii_output, lex_refs = step2_ndine_to_dine_ascii(ndine_output)

    return render_template(
        "index.html",
        mode=mode,
        action=action,
        english_input=english_input,
        ndine_output=ndine_output,
        dine_ascii_output=dine_ascii_output,
        single_matches=single_matches,
        lex_refs=lex_refs,
        error_msg=error_msg,
        slot_check_ok=slot_check_ok,
        slot_check_msg=slot_check_msg,
        max_words=MAX_SENTENCE_WORDS,
        db_count=get_db_count(),
        csv_count=len(load_csv_examples())
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
