# src/hybridmind/fallback.py
from __future__ import annotations

from typing import Optional
import torch
from transformers import pipeline
import re


# -----------------------------------------------------------------------------
# LLM CONFIG
# -----------------------------------------------------------------------------
LLM_MODEL_NAME = "google/flan-t5-base"

# Lazy-loaded HF pipeline
_translator = None

# Allowed canonical command prefixes (must match your grammar keywords)
CANON_PREFIXES = ("sort", "print", "show", "compute", "set", "if")


def set_llm_model_name(model_name: str) -> None:
    """Optional helper if you want to switch model from main.py."""
    global LLM_MODEL_NAME, _translator
    if model_name and model_name != LLM_MODEL_NAME:
        LLM_MODEL_NAME = model_name
        _translator = None  # force reload


def load_llm() -> None:
    """Load local HuggingFace text2text model once (lazy)."""
    global _translator
    if _translator is not None:
        return
    print("[LLM] Loading local model...")
    device = 0 if torch.cuda.is_available() else -1
    _translator = pipeline("text2text-generation", model=LLM_MODEL_NAME, device=device)
    print("[LLM] Ready.")


# -----------------------------------------------------------------------------
# SAFETY / VALIDATION
# -----------------------------------------------------------------------------
def is_safe_candidate(cmd: str) -> bool:
    """
    Ensure the candidate output is:
    - single line
    - not code / injection-ish
    - starts with allowed canonical command keywords
    - not placeholders like 'expr' 'op' 'command'
    """
    cmd = (cmd or "").strip().lower()
    if not cmd:
        return False

    # Reject placeholders that sometimes appear from prompt templates
    bad_placeholders = ["<expr>", "<op>", "<command>", "expr", " op ", "command"]
    if any(b in cmd for b in bad_placeholders):
        return False

    # Reject common code / injection markers
    bad_markers = [
        "__name__", "import", "def ", "class ", "lambda", "exec", "eval",
        "print(", "```", "{", "}", "[", "]"
    ]
    if any(b in cmd for b in bad_markers):
        return False

    # Must be one line only
    if "\n" in cmd or "\r" in cmd:
        return False

    # Must start with a canonical keyword
    if not cmd.startswith(CANON_PREFIXES):
        return False

    return True


# -----------------------------------------------------------------------------
# RULE-BASED FALLBACK (fast + deterministic)
# -----------------------------------------------------------------------------
def rule_fallback(user_text: str) -> Optional[str]:
    """
    Cheap deterministic mapping for common ambiguous phrases.
    This runs BEFORE calling the LLM (saves time + avoids hallucination).
    """
    t = (user_text or "").lower().strip()
    
    # --- set variable patterns ---
    m = re.search(r"\b(store|put|save)\s+(\d+(?:\.\d+)?)\s+(in|into)\s+(variable|var)\s+([a-z_]\w*)\b", t)
    if m:
        value = m.group(2)
        name = m.group(5)
        return f"set {name} = {value}"

    # --- calculate patterns (word-ops → symbols, keep parentheses) ---
    if t.startswith("calculate "):
        expr = t[len("calculate "):].strip()
        expr = (expr
            .replace("plus", "+")
            .replace("minus", "-")
            .replace("times", "*")
            .replace("multiplied by", "*")
            .replace("divided by", "/")
        )
        # normalize spaces
        expr = re.sub(r"\s+", " ", expr)
        return f"compute {expr}"

    # --- show/print result (catch 'show the result', 'show me the result') ---
    if "result" in t and any(w in t for w in ["print", "show", "display"]):
        return "print result"

    # Key demo: sort + progress concurrently
    if "while" in t and ("progress" in t or "status" in t):
        if any(w in t for w in ["sort", "arrange", "organize"]):
            return "sort numbers while show progress"

    # Single sort
    if any(w in t for w in ["sort", "arrange", "organize"]) and any(w in t for w in ["list", "numbers", "number"]):
        return "sort numbers"

    # Print/show result
    if any(w in t for w in ["print", "show", "display"]) and "result" in t:
        return "print result"

    # "show progress" synonym
    if any(w in t for w in ["progress", "status"]) and any(w in t for w in ["show", "display", "print"]):
        return "show progress"

    return None


# -----------------------------------------------------------------------------
# LLM REWRITE (semantic mapping -> grammar-valid command)
# -----------------------------------------------------------------------------
def llm_rewrite(user_text: str) -> str:
    """
    Use the LLM ONLY to rewrite natural/ambiguous input into ONE canonical command
    that your grammar can parse.

    Returns:
      - rewritten canonical command (string), OR
      - "FAIL" if it cannot produce a safe/valid command.
    """
    load_llm()

    prompt = f"""Task:
- Convert the input into ONE single-line command ONLY.
- Fix typos/ambiguity.
- Output MUST match the command patterns shown below.

Allowed patterns:
1) compute <expr>
2) set <id> = <expr>
3) if <expr> <op> <expr> then <command>
4) sort numbers
5) print result
6) show progress
7) sort numbers while show progress

Rules:
- Output ONE line only
- Output ONLY the command (no explanation)
- No bullet points, no markdown
- If you cannot convert, output: FAIL

Examples:
Input: add 5 and 10
Output: compute 5 + 10

Input: put 99 into variable score
Output: set score = 99

Input: check if score is big then show it
Output: if score > 50 then print score

Input: sort this list while showing progress
Output: sort numbers while show progress

Input: {user_text}
Output:
""".strip()

    out = _translator(
        prompt,
        max_new_tokens=32,
        do_sample=False,
        num_beams=1
    )[0]["generated_text"].strip().lower()

    # Keep only first line and normalize punctuation
    out = out.splitlines()[0].strip()
    out = (
    out.replace(":", "")
       .replace(";", "")
       .replace(",", "")
       .replace(" plus ", " + ")
       .replace(" minus ", " - ")
       .replace(" times ", " * ")
       .replace(" divided by ", " / ")
       )


    # If model says FAIL or output unsafe, try rules, else FAIL
    if out == "fail" or not is_safe_candidate(out):
        rb = rule_fallback(user_text)
        if rb:
            return rb
        return "FAIL"

    return out
