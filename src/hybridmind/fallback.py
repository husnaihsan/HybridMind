# src/hybridmind/fallback.py
from __future__ import annotations

from typing import Optional
import re

import torch
from transformers import pipeline

# -----------------------------------------------------------------------------
# LLM CONFIG
# -----------------------------------------------------------------------------
LLM_MODEL_NAME = "google/flan-t5-large"

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

    print(f"[LLM] Loading local model: {LLM_MODEL_NAME} ...")
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

    # Must be one line only
    if "\n" in cmd or "\r" in cmd:
        return False

    # Must start with a canonical keyword
    if not cmd.startswith(CANON_PREFIXES):
        return False

    # Reject placeholder/template tokens as *whole words*
    if re.search(r"\b(<expr>|<op>|<command>|expr|op|command)\b", cmd):
        return False

    # Reject common code / injection markers
    bad_markers = [
        "__name__", "import", "from ", "def ", "class ", "lambda",
        "exec", "eval", "os.", "subprocess", "system(", "open(",
        "```", "{", "}", "[", "]"
    ]
    if any(b in cmd for b in bad_markers):
        return False

    # Extra: reject obvious "explanations"
    if any(phrase in cmd for phrase in ["because", "here's", "explanation", "the command is"]):
        return False

    return True


# -----------------------------------------------------------------------------
# RULE-BASED FALLBACK (MINIMAL on purpose: let LLM do most rewrites)
# -----------------------------------------------------------------------------
def rule_fallback(user_text: str) -> Optional[str]:
    """
    Minimal deterministic mapping.
    Keep this VERY small so most inputs go to the LLM (demo-friendly).

    Only handles the most reliable pattern:
    - storing a numeric value into a variable
    """
    t = (user_text or "").lower().strip()
    if not t:
        return None

    # "store 12 into variable x" / "save 3.5 in var score"
    m = re.search(
        r"\b(store|put|save)\s+(\d+(?:\.\d+)?)\s+(in|into)\s+(variable|var)\s+([a-z_]\w*)\b",
        t,
    )
    if m:
        value = m.group(2)
        name = m.group(5)
        return f"set {name} = {value}"

    return None


# -----------------------------------------------------------------------------
# LLM REWRITE (semantic mapping -> grammar-valid command)
# -----------------------------------------------------------------------------
def llm_rewrite(user_text: str) -> str:
    """
    Use the LLM to rewrite natural/ambiguous input into ONE canonical command
    that your grammar can parse.

    Flow:
      1) Try minimal rule_fallback (only set-var pattern)
      2) Otherwise call LLM
      3) Validate against safe DSL constraints

    Returns:
      - rewritten canonical command (string), OR
      - "FAIL" if it cannot produce a safe/valid command.
    """
    # 1) Minimal deterministic rule (kept tiny on purpose)
    rb = rule_fallback(user_text)
    if rb:
        return rb

    # 2) Otherwise, call the local LLM
    load_llm()

    prompt = f"""
    You are a translator into a tiny DSL.

    Output exactly ONE command. The command MUST start with one of:
    compute, set, if, sort, print, show
    If you cannot convert, output exactly: FAIL

    Valid outputs:
    - compute <expr>
    - set <id> = <expr>
    - if <expr> <op> <expr> then <command>
    - sort numbers
    - print result
    - show progress
    - sort numbers while show progress

    IMPORTANT CONCURRENCY RULE:
    - If the user input contains the word "while", you MUST output:
    sort numbers while show progress
    (This DSL only supports concurrency for sorting + progress.)

    Mapping rules:
    - "sort/organize/arrange/order/rank" + "list/numbers" => sort numbers
    - "progress/status" => show progress
    - "result/output/answer" => print result
    - "add/sum/plus/minus/times/divide/calc/calculate" => compute <expr>

    Hard rules:
    - Output ONE line only.
    - Output ONLY the DSL command, no explanation.
    - Do NOT output partial commands like "sort" or "show status".
    - Use the exact tokens: "numbers", "progress", "result".

    Examples:
    Input: pls sort this list
    Output: sort numbers

    Input: rank these numbers
    Output: sort numbers

    Input: organize list while show status
    Output: sort numbers while show progress

    Input: sort numbers while showing progress
    Output: sort numbers while show progress

    Input: show status
    Output: show progress

    Input: calc 4 + 5
    Output: compute 4 + 5

    Input: calc 4 + 5 while show progress
    Output: sort numbers while show progress

    Input: show the result
    Output: print result

    Input: {user_text}
    Output:
    """.strip()

    res = _translator(
        prompt,
        max_new_tokens=32,
        do_sample=False,
        num_beams=4,
        early_stopping=True,
    )[0]

    out = (res.get("generated_text") or "").strip().lower()

    # Keep only first line
    out = out.splitlines()[0].strip()

    # Normalize punctuation & word-ops
    out = (
        out.replace(":", "")
           .replace(";", "")
           .replace(",", "")
           .replace(" plus ", " + ")
           .replace(" minus ", " - ")
           .replace(" times ", " * ")
           .replace(" divided by ", " / ")
           .strip()
    )

    # Validate
    if out == "fail" or not is_safe_candidate(out):
        return "FAIL"

    return out
