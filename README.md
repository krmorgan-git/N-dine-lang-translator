# N-dine-lang-translator

**Author:** Kelly R. Morgan, Assistant Professor of Information Technology  
**Affiliation:** Navajo Technical University (Crownpoint, NM)  
**Created:** November 20, 2026  
**Status:** Beta (limited lexicon coverage and minimal reference sentence examples)

**Main starter project** for N-dine-lang. The language specification and original reference engine live in [`N-dine-lang`](https://github.com/krmorgan-git/N-dine-lang); this repository is the Flask application built on top of it and is the starting point for further work.

---

## Overview

**`N-dine-lang`** is a simple, structured format inspired by **Diné Bizaad** (the Navajo language) that breaks a sentence into clear, labeled parts (such as time, subject, verb, object, and location).

Translating directly between English and Diné Bizaad can be difficult for AI models because of word order, spelling, and accent-mark differences. `N-dine-lang` acts as an easy-to-read bridge between **English**, **Diné Bizaad**, **AI models**, and a **SQLite word database** by putting each word into a fixed, predictable slot.

This repository provides a local Flask web app to test that workflow using a local Gemma 3 1B model and the `db/dine_lex.db` lexicon.

---

## Core Architecture (`T S V O L`)

Every `N-dine-lang` expression follows a fixed left-to-right slot order:

```text
T-[time]  S-[subject]  V-[verb]  O-[object]  L-[location]
```

| Prefix | Role | Plain-English Meaning | Example |
| :--- | :--- | :--- | :--- |
| **`T-`** | Time | `pst` (past), `prs` (present), `fut` (future) | `T-pst`, `T-fut-tomorrow` |
| **`S-`** | Subject | Who does the action (`1sg` = I, `2sg` = you, `1pl` = we, or a noun) | `S-1sg`, `S-boy` |
| **`V-`** | Verb | The action or state (`un-` means *not*) | `V-drink`, `V-un-like` |
| **`O-`** | Object | What receives the action | `O-water`, `O-coffee` |
| **`L-`** | Location | Where it happens or where someone is going | `L-home`, `L-flagstaff` |

---

## Two-Way Language Bridge Examples

`N-dine-lang` acts as a neutral pivot layer between **English (SVO)** and plain-ASCII **Diné Bizaad (SOV)**—eliminating the need for glottal stops (`ʼ`) or accent marks during processing:

* **Example 1 (Past Action + Location)**
  * **`N-dine-lang`:** `T-pst S-boy V-see O-dog L-home.`
  * **English:** The boy saw the dog at home.
  * **Diné (Plain ASCII):** `Hooghandi ashkii leechai yiyiiltsa.`

* **Example 2 (Present Action)**
  * **`N-dine-lang`:** `T-prs S-1sg V-drink O-cold-water.`
  * **English:** I am drinking cold water.
  * **Diné (Plain ASCII):** `To sikazi yishdla.`

* **Example 3 (Future Action + Time & Location)**
  * **`N-dine-lang`:** `T-fut-tomorrow S-1pl V-go L-flagstaff.`
  * **English:** Tomorrow we will go to Flagstaff.
  * **Diné (Plain ASCII):** `Yiskaago kinlanigoo diikah.`

---

## Requirements

* **Operating System:** Linux, WSL (Windows Subsystem for Linux), macOS, or Windows.
* **Python 3.8 or newer** (`python3 --version` on Linux/macOS/WSL, or `python --version` on Windows).  
  *(On Ubuntu/Debian/WSL, make sure `venv` is installed: `sudo apt update && sudo apt install -y python3 python3-venv`)*
* **RAM & Disk:** ~1.5 GB free RAM and ~1 GB free disk space (for the local ~777 MB AI model).

---

## Setup & Installation

### Option A: One-Command Install & Run (Recommended)

**Linux / macOS / WSL:**
```bash
git clone https://github.com/krmorgan-git/N-dine-lang-translator.git
cd N-dine-lang-translator
bash start.sh
```

**Windows (Command Prompt / PowerShell):**
```bat
git clone https://github.com/krmorgan-git/N-dine-lang-translator.git
cd N-dine-lang-translator
start.bat
```

The script automatically sets up the project, installs dependencies, downloads the AI model (~777 MB) on first run, and starts the web app at **<http://127.0.0.1:5000>**.

> **How to use the app:** Open <http://127.0.0.1:5000> in your browser. Choose **Single word** for a `db/dine_lex.db` dictionary lookup, or **Two or more words** (12 words max) for two-step translation (**English → `N-dine-lang` → Diné ASCII**). Press `Ctrl+C` in the terminal to stop.

### Option B: Manual Setup (Advanced)

1. **Bootstrap & create virtual environment:**
   ```bash
   python3 bootstrap.py
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Run the web app:**
   ```bash
   python app.py
   ```

---

## Repository Structure

After running **Setup & Installation** and `python app.py`:

```text
N-dine-lang-translator/
├── .env                              # Local secret: GEMINI_API_KEY (bootstrap.py)
├── .gitignore                        # Excludes caches, environment files, and local-only data
├── .venv/                            # Python virtual environment (Setup, Step 2)
├── CITATION.cff                      # Academic citation metadata for GitHub & Zenodo
├── LICENSE                           # Dual MIT (code) & CC BY 4.0 (specification/docs)
├── README.md                         # Specification overview, setup steps, and citation
├── csv/
│   └── ex_sents.csv                  # 30 reference sentence pairs (English / Dine ASCII / N-dine-lang)
├── db/
│   └── dine_lex.db                   # SQLite lexicon, 8,611 entries (~1.4 MB), shipped with the repo
├── md/                               # Markdown notes/output workspace (bootstrap.py)
├── models/
│   └── gemma3-1b-ndine-Q4_K_M.gguf   # Local GGUF model (~777 MB), downloaded on first run (app.py)
├── static/
│   └── styles.css                    # Stylesheet for the Flask web UI
├── templates/
│   └── index.html                    # Jinja2 HTML template for the Flask web UI
├── requirements.txt                  # Dependencies: flask, llama-cpp-python, huggingface_hub, google-genai, python-dotenv
├── bootstrap.py                      # Creates md/, .env, and requirements.txt (Setup, Step 1)
└── app.py                            # Flask web app: DB lookup + two-step English -> N-dine-lang -> Dine (ASCII)
```

---

## Citation

If you use **`N-dine-lang`**, its specification, this Flask application, or the reference Python engine in academic research, curriculum development, or software projects, please cite:

> Morgan, K. R. (2026). *N-dine-lang: A Deterministic Slot-Tag Intermediate Representation for Diné Bizaad, English, and Computational Pipelines*. Navajo Technical University, Crownpoint, NM.

---

## License

* **Software & Source Code (`*.py`):** Licensed under the [MIT License](LICENSE).
* **Specification, Documentation & Linguistic Datasets (`*.md`, `*.csv`, `*.db`):** Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE).
