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

Every `N-dine-lang` expression follows a strict, unchanging canonical slot order:

```text
[T/Q/C/M]-[time]  S-[subject]  V-[verb]  O-[object]  L-[location]
```

| Prefix | Role | Description | Example |
| :--- | :--- | :--- | :--- |
| **`T-`** | Tense / Time | `pst` (past), `prs` (present), `fut` (future) | `T-pst`, `T-fut-tomorrow` |
| **`Q-`** | Question | Interrogative marker with tense | `Q-prs` |
| **`C-`** | Condition | Conditional clause (`if`) | `C-prs` |
| **`M-`** | Mode / Command | Imperative execution trigger | `M-now` |
| **`S-`** | Subject | Actor or pronoun (`1sg`, `2sg`, `3sg`, `1pl`, `3pl`) | `S-1sg`, `S-admin` |
| **`V-`** | Verb | Core action root (`un-` for negation) | `V-drink`, `V-un-allow` |
| **`O-`** | Object | Direct receiver or target argument | `O-water`, `O-rout-tul` |
| **`L-`** | Location | Physical or logical destination/environment | `L-home`, `L-serv-dom` |

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

This project targets **Linux and WSL (Windows Subsystem for Linux)**.

* **Python 3.6 or newer** (tested with Python 3.12 in WSL2). Confirm with:

  ```bash
  python3 --version
  ```

* **The `venv` module.** On Debian/Ubuntu/WSL, install Python and venv support with:

  ```bash
  sudo apt update
  sudo apt install -y python3 python3-venv
  ```

* **Dependencies:** `flask`, `llama-cpp-python`, and `huggingface_hub` power the web interface and the local Gemma model. All are listed in the generated `requirements.txt` and installed in Setup, Step 4. The same file also lists `google-genai` and `python-dotenv` for optional Gemini-backed features; `app.py` does not use them yet.
* **Optional:** a **Google Gemini API key** for future Gemini-backed features. `app.py` does not read it yet — the key and the `.env` entry are reserved for when that support lands. Create one at [Google AI Studio](https://aistudio.google.com/apikey) and set `GEMINI_API_KEY` in `.env` (see Setup, Step 2).

---

## Repository Structure

```text
N-dine-lang-translator/
├── .gitignore        # Excludes caches, environment files, and local-only data
├── CITATION.cff      # Academic citation metadata for GitHub & Zenodo
├── LICENSE           # Dual MIT (code) & CC BY 4.0 (specification/docs)
├── README.md         # Specification overview, setup steps, and citation
├── csv/
│   └── ex_sents.csv  # 30 reference sentence pairs (English / Dine ASCII / N-dine-lang)
├── db/
│   └── dine_lex.db   # SQLite lexicon, 8,611 entries (~1.4 MB), shipped with the repo
├── static/
│   └── styles.css    # Stylesheet for the Flask web UI
├── templates/
│   └── index.html    # Jinja2 HTML template for the Flask web UI
├── bootstrap.py      # Creates md/, .env, and requirements.txt (Setup, Step 2)
└── app.py            # Flask web app: DB lookup + two-step English -> N-dine-lang -> Dine (ASCII)
```

The following items are **created locally** when you bootstrap and run the project and are not part of the repository:

```text
N-dine-lang-translator/
├── .venv/               # Python virtual environment (Setup, Step 3)
├── md/                  # Markdown notes/output workspace (bootstrap.py)
├── models/              # Local GGUF model directory, ~769 MB after first run (bootstrap.py)
├── .env                 # Local secret: GEMINI_API_KEY (bootstrap.py)
└── requirements.txt     # Dependencies: flask, llama-cpp-python, huggingface_hub, google-genai, python-dotenv (bootstrap.py)
```

> `__pycache__/` is not present initially. Python creates it on the first run, and it is safe to delete.

---

## Setup & Installation

These steps apply to **Linux and WSL**. In WSL, run every command in your Linux terminal (not PowerShell or `cmd`).

> **WSL tip:** keep the project inside the Linux filesystem — for example `~/projects/` — not under `/mnt/c/...`. Working from the Windows drive is noticeably slower and can cause permission and virtual-environment problems.

### 1. Clone the repository

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/krmorgan-git/N-dine-lang-translator.git
cd N-dine-lang-translator
```

### 2. Initialize the project layout

Immediately after cloning, run the bootstrap script from the project root:

```bash
python3 bootstrap.py
```

This creates `md/` and `.env`, and writes `requirements.txt` if it is missing. `csv/` and `db/` ship with the repository, and `models/` is created by `app.py` when it first loads the model.

> **Optional:** open `.env` and add your Gemini API key — only needed for Gemini-backed features. If you are not using Gemini, skip this step.

```ini
GEMINI_API_KEY=your-api-key-here
```

Get a key from [Google AI Studio](https://aistudio.google.com/apikey). `.env` is git-ignored, so the key stays local and must never be committed. As an alternative, export the variable in your shell — environment variables take precedence over `.env`:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Existing files are preserved; `python bootstrap.py --force` regenerates the templates (and overwrites `.env`, so only use it before adding a real key).

### 3. Create and activate a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should now show the environment name, for example `(.venv) user@host:~/projects/N-dine-lang-translator$`.

If this fails with an `ensurepip is not available` error, install the venv package and retry:

```bash
sudo apt install -y python3-venv
```

### 4. Install dependencies

Upgrade `pip`, then install the dependencies declared in `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the web app

From the project root (`N-dine-lang-translator/`), with the virtual environment active:

```bash
python app.py
```

On the first start the app downloads `gemma3-1b-ndine-Q4_K_M.gguf` (~777 MB) from the `v1.0` GitHub Release into `models/` and loads it, so expect a delay and roughly 1.5 GB of RAM in use. Once it is running you will see:

```text
 * Running on http://127.0.0.1:5000
```

Open <http://127.0.0.1:5000> in a browser. Choose **Single word** for a direct `lexicon` lookup, or **Two or more words** (12 words max) to run Step 1 (English → N-dine-lang), edit the slot line if needed, then Step 2 (N-dine-lang → Diné ASCII). Stop the server with `Ctrl+C`.

`db/dine_lex.db` ships with the repository (8,611 lexicon entries), so there is nothing to generate before the first run. `db/` is git-ignored except for that file, so any other SQLite files you create stay local.

### 6. Deactivate when finished

```bash
deactivate
```

### Other platforms (brief)

* **macOS:** the same commands work (`python3` is provided by the system or Homebrew).
* **Windows (native):** use `python -m venv .venv` and activate with `.venv\Scripts\Activate.ps1` in PowerShell. WSL is the path documented above.

---

## Citation

If you use **`N-dine-lang`**, its specification, this Flask application, or the reference Python engine in academic research, curriculum development, or software projects, please cite:

> Morgan, K. R. (2026). *N-dine-lang: A Deterministic Slot-Tag Intermediate Representation for Diné Bizaad, English, and Computational Pipelines*. Navajo Technical University, Crownpoint, NM.

---

## License

* **Software & Source Code (`*.py`):** Licensed under the [MIT License](LICENSE).
* **Specification, Documentation & Linguistic Datasets (`*.md`, `*.csv`, `*.db`):** Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE).
