# HybridMind  
**Grammar-Driven, LLM-Assisted Natural Language Interpreter**

HybridMind is a prototype natural-language programming system that combines a **formal grammar-based interpreter** with an **LLM fallback mechanism** to balance correctness and flexibility. The system interprets simple natural-language commands such as arithmetic computation, conditional execution, and concurrent actions, while ensuring **deterministic and verifiable execution**.

This project is developed as part of the **WIF3010 Programming Language Paradigms** coursework.

---

## Project Motivation

Natural-language interfaces are increasingly used to express computational tasks. However:

- **Pure grammar-based systems** are strict and fail when users use synonyms or informal phrasing.
- **Pure LLM-based systems** are flexible but may hallucinate, misinterpret intent, or produce logically incorrect results.

Based on literature review and interview insights from a practising data analyst, we observed that users often struggle with:
- Ambiguous natural-language commands
- Missing or unclear context
- Over-trusting LLM outputs without verification

HybridMind addresses this gap using a **two-tier hybrid architecture**:

1. **Tier 1 — Grammar-first parsing** for correctness and control  
2. **Tier 2 — LLM-assisted rewriting** only when Tier 1 fails, followed by re-verification

**Key principle:** the **grammar is the final authority**. The LLM never executes commands directly.

---

## Project Objectives

- Design a **context-free grammar (CFG)** using EBNF for structured commands
- Implement a **recursive-descent parser** and interpreter in Python
- Construct a **two-tier hybrid interpreter**:
  - Tier 1: Grammar-based parsing and deterministic execution
  - Tier 2: LLM fallback to resolve ambiguity and synonyms
- Extend the language with a **concurrency paradigm** using natural expressions such as  
  `sort numbers while show progress`
- Evaluate correctness, ambiguity handling, and execution behaviour using metrics

---

## System Overview

### HybridMind Processing Pipeline

HybridMind processes user input through the following steps:

1. User input is tokenized by a **regex-based lexical analyzer**.
2. The token stream is parsed using a **recursive-descent parser** into an AST.
3. If the input conforms to the grammar, the AST is executed by the interpreter.
4. If parsing fails (or is rejected by validation), HybridMind invokes an **LLM (or rule-based mapping)** to rewrite the input into a grammar-compliant command.
5. The rewritten command is **re-parsed and verified** by the grammar before execution.

**Safety & Verification**
- The grammar is the **final authority**
- The LLM **never executes** commands directly
- All rewritten commands are **re-verified** before execution

---

## Supported Language Features

### Core Commands
- **Assignment**  
  `set x = 10 + 5`

- **Arithmetic expressions (with precedence)**  
  `compute x * 2`  
  `compute 1 + 2 * 3`

- **Conditional execution**  
  `if x > 10 then print result`

- **Action commands**  
  `print result`  
  `sort numbers`  
  `show progress`

### Hybrid Extension (Fallback)
HybridMind can interpret informal/ambiguous user phrases via rewriting:

- `pls organize this list` → `sort numbers`
- `organize list while showing status` → `sort numbers while show progress`

### Paradigm Extension: Concurrency
HybridMind supports concurrency using a natural syntax:

- `sort numbers while show progress`

This runs two actions in parallel using Python threads: sorting and progress reporting.

---

## Project Structure (src layout)

```
HybridMind/
├─ requirements.txt
├─ README.md
├─ src/
│  └─ hybridmind/
│     ├─ __init__.py
│     ├─ lexer.py
│     ├─ parser.py
│     ├─ interpreter.py
│     ├─ fallback.py
│     ├─ metrics.py
│     └─ main.py
├─ tests/
│  ├─ __init__.py        (optional but recommended)
│  └─ test_pipeline.py
└─ data/
   └─ eval_input.txt     (or your chosen evaluation file name)
```

> Note: With a `src/` layout, you must either set `PYTHONPATH=src` when running,
> or install the package in editable mode (`pip install -e .`).

---

## Setup

### 1) Create and activate a virtual environment (recommended)

**Windows (PowerShell)**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

---

## How to Run

> Run commands from the **project root** (the folder that contains `src/`, `tests/`, `data/`).

### Option A — Run without installing (using `PYTHONPATH=src`)

#### 1) Start the REPL (interactive mode)

**Windows (PowerShell)**
```bash
$env:PYTHONPATH="src"
python -m hybridmind.main
```

**macOS / Linux**
```bash
PYTHONPATH=src python -m hybridmind.main
```

Type commands such as:
- `compute 1 + 2 * 3`
- `set x = 10`
- `if x > 5 then print result`
- `sort numbers while show progress`

Exit:
- `exit`

#### 2) Run the small evaluation dataset

**Windows (PowerShell)**
```bash
$env:PYTHONPATH="src"
python -c "from hybridmind.main import run_small_dataset; run_small_dataset('data/eval_input.txt')"
```

**macOS / Linux**
```bash
PYTHONPATH=src python -c "from hybridmind.main import run_small_dataset; run_small_dataset('data/eval_input.txt')"
```

### Option B — Install in editable mode (no `PYTHONPATH` needed)

If you want a cleaner “one-command” run experience, install HybridMind as a local package:

1. Add a basic `pyproject.toml` (if not already included)
2. Install editable:

```bash
pip install -e .
```

Then you can run:
```bash
python -m hybridmind.main
python -c "from hybridmind.main import run_small_dataset; run_small_dataset('data/eval_input.txt')"
```

---

## Running Tests

### Recommended: unittest discovery (works even if `tests/` isn’t a package)
**Windows (PowerShell)**
```bash
$env:PYTHONPATH="src"
python -m unittest discover -s tests -p "test_*.py" -v
```

**macOS / Linux**
```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v
```

### Module-style run (requires `tests/__init__.py`)
```bash
python -m unittest -v tests.test_pipeline
```

---

## LLM Fallback Configuration

HybridMind includes an LLM rewriting module in `fallback.py`.

- Default model name is configurable in `fallback.py` (`LLM_MODEL_NAME`)
- The LLM is **lazy-loaded** (only loaded when needed)
- The LLM output is **validated** and **re-parsed** before execution

**Tip for evaluation:** Include at least one input in your dataset that *rules don’t cover* so the LLM path is demonstrated in metrics.

Example lines you can add to `data/eval_input.txt`:
- `store 99 in variable score`
- `calculate 5 times (2 plus 3)`

---

## Metrics and Evaluation

HybridMind tracks:
- Total inputs processed
- Tier-1 (grammar) success vs failure
- Rule fallback usage
- LLM usage, failures, and verified executions

At the end of `run_small_dataset(...)`, metrics are printed like:
- Tier-1 success rate
- Fallback rate
- LLM dependency ratio
- LLM verified + executed count

---

## Example Session

```text
Hybrid>>> compute 1 + 2 * 3
[COMPUTE] result = 7

Hybrid>>> set x = 10
[ASSIGN] x = 10

Hybrid>>> if x > 5 then print result
[IF] condition true → executing body
[PRINT] 7

Hybrid>>> sort numbers while show progress
[CONCURRENCY] Running in parallel...
[SORT] Sorting numbers...
[PROGRESS] progress... 1
...
[SORT] Done sorting numbers.
[CONCURRENCY] Done in ~2.0s

Hybrid>>> pls organize this list
[INFO] Grammar failed → fallback rewriting...
[RULE] Rewritten as: sort numbers
[SORT] Sorting numbers...
[SORT] Done sorting numbers.
```

---

## Notes / Troubleshooting

### “ModuleNotFoundError: No module named 'hybridmind'”
You’re likely running from the root without `PYTHONPATH=src` (or without installing editable).
Use:
```bash
$env:PYTHONPATH="src"
```
or install with:
```bash
pip install -e .
```

### “FileNotFoundError: data/...”
Your working directory matters. Run dataset commands from the **project root** (where `data/` exists).

### Concurrency output looks “messy”
Threaded printing can interleave. This is normal for concurrent console output.

---

## License
For coursework use. Add a license if you plan to publish publicly.

---

## Acknowledgements
- WIF3010 Programming Language Paradigms (coursework)
- Hugging Face Transformers (LLM rewriting)

