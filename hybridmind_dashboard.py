"""
HybridMind Visualization Dashboard
A Streamlit app for exploring and demoing the HybridMind interpreter.
Run with: streamlit run hybridmind_dashboard.py
"""

import streamlit as st
import re
import time
import random
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="HybridMind Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* App background */
.stApp {
    background: #0a0e1a;
    color: #e2e8f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f1625 !important;
    border-right: 1px solid #1e2d40;
}

/* Mono font for code-like elements */
code, pre, .mono {
    font-family: 'Space Mono', monospace !important;
}

/* Cards */
.metric-card {
    background: linear-gradient(135deg, #111827 0%, #1a2535 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent);
}
.metric-card .value {
    font-size: 2.4rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    color: var(--accent);
    line-height: 1.1;
}
.metric-card .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-top: 4px;
}

/* Output box */
.output-box {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 16px 20px;
    font-family: 'Space Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.8;
    white-space: pre-wrap;
    min-height: 120px;
    color: #c9d1d9;
}

/* Tag badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-tier1 { background: #0d3326; color: #34d399; border: 1px solid #065f46; }
.badge-rule  { background: #172554; color: #60a5fa; border: 1px solid #1e40af; }
.badge-llm   { background: #2d1b69; color: #a78bfa; border: 1px solid #4c1d95; }
.badge-fail  { background: #2d0a0a; color: #f87171; border: 1px solid #7f1d1d; }

/* Section headers */
.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #475569;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2d40;
    margin-bottom: 16px;
}

/* Pipeline step */
.pipeline-step {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    border: 1px solid;
}
.step-tier1 { background: #051a0e; border-color: #065f46; }
.step-rule   { background: #0a1628; border-color: #1e3a8a; }
.step-llm    { background: #13082a; border-color: #3b0764; }
.step-reject { background: #150505; border-color: #7f1d1d; }

.step-icon { font-size: 1.2rem; margin-top: 2px; }
.step-title { font-weight: 600; font-size: 0.85rem; color: #e2e8f0; }
.step-desc  { font-size: 0.78rem; color: #64748b; margin-top: 2px; }

/* Sticker on pipeline */
.pipe-line {
    width: 2px;
    background: linear-gradient(to bottom, #1e3a5f, transparent);
    height: 24px;
    margin: 0 auto 0 28px;
}

/* AST tree */
.ast-node {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: #93c5fd;
}
.ast-node span { color: #fbbf24; }

/* Streamlit overrides */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #111827 !important;
    border: 1px solid #1e3a5f !important;
    color: #e2e8f0 !important;
    font-family: 'Space Mono', monospace !important;
}
[data-testid="stButton"] button {
    background: linear-gradient(135deg, #1d4ed8, #3730a3) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid #1e2d40 !important;
    border-radius: 8px !important;
}

/* Tabs */
[data-baseweb="tab-list"] {
    background: #0f1625 !important;
    border-radius: 8px;
    padding: 4px;
}
[data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #64748b !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #60a5fa !important;
    background: #1e3a5f !important;
    border-radius: 6px !important;
}

h1, h2, h3 {
    font-family: 'Space Mono', monospace !important;
}

.stSelectbox label, .stTextInput label, .stSlider label {
    color: #64748b !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CORE HYBRIDMIND LOGIC (self-contained, no imports needed)
# ─────────────────────────────────────────────

TOKEN_SPEC = [
    ("IF",      r"if"),
    ("THEN",    r"then"),
    ("SET",     r"set"),
    ("WHILE",   r"while"),
    ("ACTION",  r"(sort|print|show|compute)"),
    ("OBJECT",  r"(numbers|number|list|progress|result)"),
    ("GE",      r">="),
    ("LE",      r"<="),
    ("EQ",      r"=="),
    ("GT",      r">"),
    ("LT",      r"<"),
    ("ASSIGN",  r"="),
    ("PLUS",    r"\+"),
    ("MINUS",   r"-"),
    ("TIMES",   r"\*"),
    ("DIV",     r"/"),
    ("LPAREN",  r"\("),
    ("RPAREN",  r"\)"),
    ("NUMBER",  r"\d+(\.\d+)?"),
    ("ID",      r"[A-Za-z_][A-Za-z_0-9]*"),
    ("WS",      r"\s+"),
]

def tokenize(text: str):
    tokens = []
    i = 0
    text = text.strip().lower()
    while i < len(text):
        match = None
        for tok_type, tok_re in TOKEN_SPEC:
            match = re.compile(tok_re).match(text, i)
            if match:
                if tok_type != "WS":
                    tokens.append((tok_type, match.group()))
                i = match.end()
                break
        if not match:
            raise ValueError(f"Unexpected character: '{text[i]}'")
    return tokens


class Parser:
    def __init__(self, tokens, enable_concurrency=True):
        self.tokens = tokens
        self.pos = 0
        self.enable_concurrency = enable_concurrency

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, tok_type):
        tok = self.peek()
        if tok and tok[0] == tok_type:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected {tok_type}, got {tok}")

    def parse_command(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Empty command")
        if tok[0] == "IF":
            return self.parse_if()
        if tok[0] == "SET":
            return self.parse_assign()
        if self.enable_concurrency:
            remaining = [t[0] for t in self.tokens[self.pos:]]
            if "WHILE" in remaining:
                return self.parse_parallel()
        return self.parse_action_cmd()

    def parse_parallel(self):
        left = self.parse_action_cmd()
        self.consume("WHILE")
        right = self.parse_action_cmd()
        return ("PARALLEL", left, right)

    def parse_action_cmd(self):
        action = self.consume("ACTION")[1]
        if action == "compute":
            expr = self.parse_expression()
            return ("ACTION_CMD", action, None, expr)
        obj = None
        if self.peek() and self.peek()[0] in ("OBJECT", "ID"):
            obj = self.consume(self.peek()[0])[1]
        return ("ACTION_CMD", action, obj, None)

    def parse_assign(self):
        self.consume("SET")
        name = self.consume("ID")[1]
        self.consume("ASSIGN")
        expr = self.parse_expression()
        return ("ASSIGN", name, expr)

    def parse_if(self):
        self.consume("IF")
        cond = self.parse_condition()
        self.consume("THEN")
        body = self.parse_command()
        return ("IF", cond, body)

    def parse_condition(self):
        left = self.parse_expression()
        tok = self.peek()
        if tok is None or tok[0] not in ("GT", "LT", "GE", "LE", "EQ"):
            raise SyntaxError("Expected comparison operator")
        op = self.consume(tok[0])[0]
        right = self.parse_expression()
        return ("COND", op, left, right)

    def parse_expression(self):
        node = self.parse_term()
        while self.peek() and self.peek()[0] in ("PLUS", "MINUS"):
            op = self.consume(self.peek()[0])[0]
            right = self.parse_term()
            node = ("BINOP", op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()[0] in ("TIMES", "DIV"):
            op = self.consume(self.peek()[0])[0]
            right = self.parse_factor()
            node = ("BINOP", op, node, right)
        return node

    def parse_factor(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        if tok[0] == "NUMBER":
            self.consume("NUMBER")
            val = float(tok[1]) if "." in tok[1] else int(tok[1])
            return ("NUM", val)
        if tok[0] == "ID":
            return ("VAR", self.consume("ID")[1])
        if tok[0] == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr
        raise SyntaxError(f"Unexpected token in factor: {tok}")


STOPWORDS = {"me", "the", "a", "an", "please", "pls", "this", "that", "it"}
UNSAFE_MARKERS = ("import", "__", "eval", "exec", "open(", "os.", "subprocess", "def ", "class ", "```")
CANON_PREFIXES = ("sort", "print", "show", "compute", "set", "if")

def try_parse(text, enable_concurrency=True):
    try:
        tokens = tokenize(text)
        return Parser(tokens, enable_concurrency=enable_concurrency).parse_command()
    except Exception:
        return None

def is_semantically_valid(ast):
    if ast is None:
        return False
    if ast[0] != "ACTION_CMD":
        return True
    _, action, obj, expr = ast
    if action == "compute":
        return expr is not None
    if action in ("show", "print") and obj in STOPWORDS:
        return False
    return True

def rule_fallback(user_text: str) -> Optional[str]:
    t = (user_text or "").lower().strip()
    if not t:
        return None
    m = re.search(r"\b(store|put|save)\s+(\d+(?:\.\d+)?)\s+(in|into)\s+(variable|var)\s+([a-z_]\w*)\b", t)
    if m:
        return f"set {m.group(5)} = {m.group(2)}"
    if t.startswith("calculate "):
        expr = t[len("calculate "):].strip()
        expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        expr = re.sub(r"\s+", " ", expr)
        return f"compute {expr}"
    if "result" in t and any(w in t for w in ["print", "show", "display"]):
        return "print result"
    if "while" in t and any(w in t for w in ["progress", "status"]):
        if any(w in t for w in ["sort", "arrange", "organize"]):
            return "sort numbers while show progress"
    if any(w in t for w in ["sort", "arrange", "organize"]) and any(w in t for w in ["list", "numbers", "number"]):
        return "sort numbers"
    if any(w in t for w in ["progress", "status"]) and any(w in t for w in ["show", "display", "print"]):
        return "show progress"
    return None


# ─────────────────────────────────────────────
# INTERPRETER (non-blocking, returns log)
# ─────────────────────────────────────────────

class SimulatedInterpreter:
    def __init__(self, env=None):
        self.env = env or {}
        self.log: List[Tuple[str, str]] = []  # (type, message)

    def _log(self, kind, msg):
        self.log.append((kind, msg))

    def eval_expr(self, node):
        kind = node[0]
        if kind == "NUM":
            return node[1]
        if kind == "VAR":
            return self.env.get(node[1], 0)
        if kind == "BINOP":
            op, left, right = node[1], node[2], node[3]
            lv = self.eval_expr(left)
            rv = self.eval_expr(right)
            if op == "PLUS": return lv + rv
            if op == "MINUS": return lv - rv
            if op == "TIMES": return lv * rv
            if op == "DIV": return lv / rv
        raise RuntimeError(f"Unknown node: {node}")

    def eval_condition(self, node):
        _, op, left, right = node
        lv = self.eval_expr(left)
        rv = self.eval_expr(right)
        if op == "GT": return lv > rv
        if op == "LT": return lv < rv
        if op == "GE": return lv >= rv
        if op == "LE": return lv <= rv
        if op == "EQ": return lv == rv

    def execute(self, node):
        kind = node[0]
        if kind == "ASSIGN":
            _, name, expr = node
            val = self.eval_expr(expr)
            self.env[name] = val
            self._log("assign", f"[ASSIGN] {name} = {val}")
            return val
        if kind == "IF":
            _, cond, body = node
            result = self.eval_condition(cond)
            if result:
                self._log("if", "[IF] condition true → executing body")
                self.execute(body)
            else:
                self._log("if", "[IF] condition false → skipping body")
            return result
        if kind == "PARALLEL":
            _, left, right = node
            self._log("parallel", "[CONCURRENCY] Running in parallel...")
            self.execute(left)
            self._log("progress", "[PROGRESS] progress... 1")
            self._log("progress", "[PROGRESS] progress... 2")
            self._log("progress", "[PROGRESS] progress... 3")
            self._log("parallel", "[CONCURRENCY] Done in ~2.0s")
            return
        if kind == "ACTION_CMD":
            _, action, obj, expr = node
            if action == "sort":
                target = obj or "numbers"
                self._log("sort", f"[SORT] Sorting {target}...")
                self._log("sort", f"[SORT] Done sorting {target}.")
                return
            if action == "compute":
                val = self.eval_expr(expr)
                self.env["result"] = val
                self._log("compute", f"[COMPUTE] result = {val}")
                return val
            if action in ("print", "show"):
                if obj == "result":
                    self._log("print", f"[PRINT] {self.env.get('result', 'None')}")
                elif obj == "progress":
                    self._log("progress", "[PROGRESS] progress... 1")
                    self._log("progress", "[PROGRESS] progress... 2")
                elif obj and obj in self.env:
                    self._log("print", f"[PRINT] {self.env[obj]}")
                else:
                    self._log("print", f"[PRINT] {obj}")


@dataclass
class StepTrace:
    tier: str  # "tier1" | "rule" | "llm" | "rejected"
    original: str
    rewritten: Optional[str]
    ast: Optional[tuple]
    tokens: List[tuple]
    output_log: List[Tuple[str, str]]
    success: bool
    error: Optional[str] = None


def run_hybridmind(text: str, env: dict, enable_llm_sim: bool = True) -> StepTrace:
    """Full pipeline — returns a StepTrace for visualization."""
    raw = (text or "").lower().strip()

    # Safety check
    if any(m in raw for m in UNSAFE_MARKERS):
        return StepTrace("rejected", text, None, None, [], [("error", "[REJECTED] Unsafe input.")], False, "Unsafe markers detected")

    # Tier-1
    try:
        tokens = tokenize(text)
    except ValueError as e:
        tokens = []
        ast = None
        tier1_ok = False
        tier1_err = str(e)
    else:
        ast = try_parse(text)
        tier1_ok = ast is not None and is_semantically_valid(ast)
        tier1_err = None

    if tier1_ok:
        interp = SimulatedInterpreter(env)
        interp.execute(ast)
        return StepTrace("tier1", text, None, ast, tokens, interp.log, True)

    # Rule fallback
    rb = rule_fallback(text)
    if rb:
        rb_ast = try_parse(rb)
        rb_tokens = []
        try:
            rb_tokens = tokenize(rb)
        except Exception:
            pass
        if rb_ast and is_semantically_valid(rb_ast):
            interp = SimulatedInterpreter(env)
            interp.execute(rb_ast)
            return StepTrace("rule", text, rb, rb_ast, rb_tokens, interp.log, True)

    # LLM simulation (no real LLM — we simulate for demo)
    if enable_llm_sim:
        llm_map = {
            "pls sort": "sort numbers",
            "organize": "sort numbers",
            "arrange": "sort numbers",
            "rank": "sort numbers",
            "show status": "show progress",
            "display status": "show progress",
            "show the result": "print result",
            "display result": "print result",
            "print the result": "print result",
            "calc ": "compute ",
            "calculate ": "compute ",
        }
        simulated = None
        t_lower = text.lower()
        for k, v in llm_map.items():
            if k in t_lower:
                # Handle arithmetic
                if k in ("calc ", "calculate "):
                    rest = t_lower.split(k, 1)[1] if k in t_lower else ""
                    rest = rest.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
                    simulated = f"compute {rest.strip()}"
                else:
                    simulated = v
                break

        if simulated:
            sim_ast = try_parse(simulated)
            sim_tokens = []
            try:
                sim_tokens = tokenize(simulated)
            except Exception:
                pass
            if sim_ast and is_semantically_valid(sim_ast):
                interp = SimulatedInterpreter(env)
                interp.execute(sim_ast)
                return StepTrace("llm", text, simulated, sim_ast, sim_tokens,
                                 [("llm", f"[LLM] Rewritten as: {simulated}")] + interp.log, True)

    return StepTrace("rejected", text, None, None, tokens or [],
                     [("error", "[ERROR] Could not parse or rewrite input.")], False,
                     tier1_err or "No fallback matched")


# ─────────────────────────────────────────────
# AST RENDERING
# ─────────────────────────────────────────────

def ast_to_lines(node, indent=0) -> List[str]:
    prefix = "  " * indent
    if node is None:
        return [f"{prefix}None"]
    kind = node[0]
    lines = []
    if kind == "NUM":
        lines.append(f"{prefix}NUM({node[1]})")
    elif kind == "VAR":
        lines.append(f"{prefix}VAR({node[1]})")
    elif kind == "BINOP":
        lines.append(f"{prefix}BINOP [{node[1]}]")
        lines += ast_to_lines(node[2], indent + 1)
        lines += ast_to_lines(node[3], indent + 1)
    elif kind == "ASSIGN":
        lines.append(f"{prefix}ASSIGN [{node[1]}]")
        lines += ast_to_lines(node[2], indent + 1)
    elif kind == "COND":
        lines.append(f"{prefix}COND [{node[1]}]")
        lines += ast_to_lines(node[2], indent + 1)
        lines += ast_to_lines(node[3], indent + 1)
    elif kind == "IF":
        lines.append(f"{prefix}IF")
        lines += ast_to_lines(node[1], indent + 1)
        lines.append(f"{'  ' * (indent+1)}THEN →")
        lines += ast_to_lines(node[2], indent + 2)
    elif kind == "PARALLEL":
        lines.append(f"{prefix}PARALLEL")
        lines.append(f"{'  ' * (indent+1)}LEFT →")
        lines += ast_to_lines(node[1], indent + 2)
        lines.append(f"{'  ' * (indent+1)}RIGHT →")
        lines += ast_to_lines(node[2], indent + 2)
    elif kind == "ACTION_CMD":
        lines.append(f"{prefix}ACTION_CMD [{node[1]}]")
        if node[2]:
            lines.append(f"{'  ' * (indent+1)}obj: {node[2]}")
        if node[3]:
            lines += ast_to_lines(node[3], indent + 1)
    else:
        lines.append(f"{prefix}{kind}: {node[1:]}")
    return lines


# ─────────────────────────────────────────────
# PLOTLY CHARTS
# ─────────────────────────────────────────────

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Mono", color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
)

def make_tier_donut(stats: Dict):
    total = stats.get("total", 1)
    tier1 = stats.get("tier1", 0)
    rule = stats.get("rule", 0)
    llm = stats.get("llm", 0)
    fail = stats.get("fail", 0)

    fig = go.Figure(go.Pie(
        labels=["Tier-1 (Grammar)", "Rule Fallback", "LLM Fallback", "Failed"],
        values=[tier1, rule, llm, fail],
        hole=0.65,
        marker=dict(colors=["#34d399", "#60a5fa", "#a78bfa", "#f87171"],
                    line=dict(color="#0a0e1a", width=2)),
        textinfo="percent",
        textfont=dict(family="Space Mono", size=10, color="white"),
    ))
    fig.update_layout(
        **DARK_LAYOUT,
        height=240,
        showlegend=True,
        legend=dict(
            font=dict(family="DM Sans", size=11, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)",
            x=1.0, y=0.5, xanchor="left",
        ),
        annotations=[dict(text=f"<b>{total}</b><br>total", x=0.5, y=0.5,
                          font=dict(family="Space Mono", size=14, color="#e2e8f0"),
                          showarrow=False)]
    )
    return fig


def make_history_bar(history: List[Dict]):
    if not history:
        return None
    df = pd.DataFrame(history[-20:])
    color_map = {"tier1": "#34d399", "rule": "#60a5fa", "llm": "#a78bfa", "rejected": "#f87171"}
    colors = [color_map.get(t, "#64748b") for t in df["tier"]]

    fig = go.Figure(go.Bar(
        x=list(range(len(df))),
        y=[1] * len(df),
        marker=dict(color=colors, line=dict(width=0)),
        hovertext=df["input"].tolist(),
        hoverinfo="text",
        width=0.8,
    ))
    fig.update_layout(
        **DARK_LAYOUT,
        height=90,
        showlegend=False,
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False, range=[0, 1.5]),
        bargap=0.1,
    )
    return fig


def make_token_viz(tokens: List[tuple]):
    if not tokens:
        return None
    types = [t[0] for t in tokens]
    vals = [t[1] for t in tokens]
    color_map = {
        "ACTION": "#34d399", "OBJECT": "#60a5fa", "IF": "#fbbf24",
        "THEN": "#fbbf24", "SET": "#fb923c", "WHILE": "#f472b6",
        "NUMBER": "#a78bfa", "ID": "#67e8f9", "PLUS": "#94a3b8",
        "MINUS": "#94a3b8", "TIMES": "#94a3b8", "DIV": "#94a3b8",
        "GT": "#f87171", "LT": "#f87171", "GE": "#f87171",
        "LE": "#f87171", "EQ": "#f87171", "ASSIGN": "#fb923c",
        "LPAREN": "#e2e8f0", "RPAREN": "#e2e8f0",
    }
    colors = [color_map.get(t, "#64748b") for t in types]

    fig = go.Figure()
    for i, (typ, val, col) in enumerate(zip(types, vals, colors)):
        fig.add_trace(go.Scatter(
            x=[i], y=[0],
            mode="markers+text",
            marker=dict(size=40, color=col, symbol="square", opacity=0.15),
            text=[val],
            textposition="middle center",
            textfont=dict(family="Space Mono", size=11, color=col),
            hovertext=f"{typ}: '{val}'",
            hoverinfo="text",
            showlegend=False,
        ))
        fig.add_annotation(
            x=i, y=-0.45, text=typ,
            showarrow=False, font=dict(family="Space Mono", size=8, color="#475569"),
        )

    fig.update_layout(
        **DARK_LAYOUT,
        height=130,
        xaxis=dict(visible=False, range=[-0.5, len(tokens) - 0.5]),
        yaxis=dict(visible=False, range=[-0.8, 0.6]),
    )
    return fig


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "env" not in st.session_state:
    st.session_state.env = {}
if "history" not in st.session_state:
    st.session_state.history = []
if "stats" not in st.session_state:
    st.session_state.stats = {"total": 0, "tier1": 0, "rule": 0, "llm": 0, "fail": 0}
if "last_trace" not in st.session_state:
    st.session_state.last_trace = None


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0 12px;">
        <div style="font-family: 'Space Mono', monospace; font-size: 1.1rem; color: #60a5fa; font-weight: 700; letter-spacing: 0.05em;">🧠 HybridMind</div>
        <div style="font-size: 0.7rem; color: #475569; margin-top: 4px; letter-spacing: 0.1em; text-transform: uppercase;">Visualization Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="section-header">Pipeline Settings</p>', unsafe_allow_html=True)
    enable_llm_sim = st.toggle("Enable LLM Fallback (Simulated)", value=True)
    enable_concurrency = st.toggle("Enable Concurrency", value=True)

    st.markdown('<p class="section-header" style="margin-top:20px;">Environment State</p>', unsafe_allow_html=True)
    if st.session_state.env:
        env_df = pd.DataFrame(list(st.session_state.env.items()), columns=["Variable", "Value"])
        st.dataframe(env_df, hide_index=True, use_container_width=True)
    else:
        st.caption("No variables set yet.")

    if st.button("🗑 Reset Environment", use_container_width=True):
        st.session_state.env = {}
        st.rerun()

    st.markdown('<p class="section-header" style="margin-top:20px;">Example Inputs</p>', unsafe_allow_html=True)
    examples = {
        "Tier-1 direct": [
            "compute 1 + 2 * 3",
            "set x = 10",
            "if x > 5 then print result",
            "sort numbers",
            "sort numbers while show progress",
            "compute (4 + 6) * 2",
        ],
        "Rule fallback": [
            "store 99 in variable score",
            "calculate 5 times (2 plus 3)",
            "show the result",
            "organize list while showing status",
        ],
        "LLM fallback": [
            "pls sort this list",
            "arrange these numbers",
            "display result",
        ],
    }
    for group, cmds in examples.items():
        st.caption(group)
        for cmd in cmds:
            if st.button(cmd, key=f"ex_{cmd}", use_container_width=True):
                st.session_state["_prefill"] = cmd


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown("""
<div style="display:flex; align-items:baseline; gap:14px; padding: 8px 0 4px;">
    <h1 style="font-family:'Space Mono',monospace; font-size:1.6rem; color:#e2e8f0; margin:0; font-weight:700;">
        🧠 HybridMind
    </h1>
    <span style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#1d4ed8; background:#172554; padding:3px 10px; border-radius:20px; border:1px solid #1e3a8a;">
        WIF3010 · Grammar-Driven NL Interpreter
    </span>
</div>
<p style="color:#475569; font-size:0.85rem; margin: 0 0 20px;">
    Two-tier hybrid pipeline: Context-Free Grammar parser + LLM-assisted fallback for natural language commands.
</p>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["▶  Interpreter", "📊  Analytics", "🔬  Pipeline Explorer", "📖  Grammar Reference"])


# ════════════════════════════════════════════
# TAB 1: INTERPRETER
# ════════════════════════════════════════════
with tab1:
    col_input, col_out = st.columns([1.1, 1], gap="large")

    with col_input:
        st.markdown('<p class="section-header">Input Command</p>', unsafe_allow_html=True)

        prefill = st.session_state.pop("_prefill", "")
        user_input = st.text_input(
            "Enter a HybridMind command",
            value=prefill,
            placeholder="e.g. compute 1 + 2 * 3",
            label_visibility="collapsed",
        )

        run_col, clear_col = st.columns([2, 1])
        with run_col:
            run_btn = st.button("▶  Run Command", use_container_width=True)
        with clear_col:
            if st.button("Clear History", use_container_width=True):
                st.session_state.history = []
                st.session_state.stats = {"total": 0, "tier1": 0, "rule": 0, "llm": 0, "fail": 0}
                st.rerun()

        if run_btn and user_input.strip():
            trace = run_hybridmind(user_input.strip(), st.session_state.env, enable_llm_sim)
            st.session_state.last_trace = trace
            st.session_state.history.append({
                "input": user_input.strip(),
                "tier": trace.tier,
                "success": trace.success,
                "rewritten": trace.rewritten,
            })
            s = st.session_state.stats
            s["total"] += 1
            if trace.tier == "tier1":
                s["tier1"] += 1
            elif trace.tier == "rule":
                s["rule"] += 1
            elif trace.tier == "llm":
                s["llm"] += 1
            else:
                s["fail"] += 1

        # Pipeline trace
        trace = st.session_state.last_trace
        if trace:
            st.markdown('<p class="section-header" style="margin-top:20px;">Pipeline Trace</p>', unsafe_allow_html=True)

            tier_info = {
                "tier1": ("step-tier1", "✅", "Tier-1: Grammar Parse", "Input matched the CFG directly."),
                "rule":  ("step-rule",  "🔀", "Tier-2a: Rule Fallback", f'Rewritten → <code style="color:#93c5fd">{trace.rewritten or ""}</code>'),
                "llm":   ("step-llm",   "🤖", "Tier-2b: LLM Rewrite",  f'LLM output → <code style="color:#c4b5fd">{trace.rewritten or ""}</code>'),
                "rejected": ("step-reject", "🚫", "Rejected", trace.error or "Could not process."),
            }

            steps = []
            steps.append(("step-tier1" if trace.tier == "tier1" else "step-reject" if trace.tier == "rejected" else "step-rule",
                           "🔍", "Tokenize & Parse", f"{len(trace.tokens)} tokens generated"))

            if trace.tier != "tier1":
                steps.append(("step-rule", "🔀", "Rule Fallback Check",
                               "Matched rule" if trace.tier == "rule" else "No rule matched"))

            if trace.tier == "llm":
                steps.append(("step-llm", "🤖", "LLM Rewrite (Simulated)",
                               f'Output: <code style="color:#c4b5fd">{trace.rewritten}</code>'))

            if trace.tier == "rejected":
                steps.append(("step-reject", "❌", "Parse Failed", trace.error or ""))
            else:
                steps.append(("step-tier1", "⚡", "Execute AST", "Grammar verified → running interpreter"))

            for cls, icon, title, desc in steps:
                st.markdown(f"""
                <div class="pipeline-step {cls}">
                    <span class="step-icon">{icon}</span>
                    <div>
                        <div class="step-title">{title}</div>
                        <div class="step-desc">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Token visualization
        if trace and trace.tokens:
            st.markdown('<p class="section-header" style="margin-top:16px;">Token Stream</p>', unsafe_allow_html=True)
            tfig = make_token_viz(trace.tokens)
            if tfig:
                st.plotly_chart(tfig, use_container_width=True, config={"displayModeBar": False})

    with col_out:
        st.markdown('<p class="section-header">Execution Output</p>', unsafe_allow_html=True)

        trace = st.session_state.last_trace
        if trace:
            # Tier badge
            badge_map = {
                "tier1": ('<span class="badge badge-tier1">Tier-1 Grammar</span>', "#34d399"),
                "rule":  ('<span class="badge badge-rule">Rule Fallback</span>', "#60a5fa"),
                "llm":   ('<span class="badge badge-llm">LLM Rewrite</span>', "#a78bfa"),
                "rejected": ('<span class="badge badge-fail">Rejected</span>', "#f87171"),
            }
            badge_html, _ = badge_map.get(trace.tier, ("", "#64748b"))
            st.markdown(f"<div style='margin-bottom:10px;'>{badge_html}</div>", unsafe_allow_html=True)

            # Output log
            log_lines = []
            color_map_log = {
                "assign": "#60a5fa", "compute": "#34d399", "if": "#fbbf24",
                "sort": "#a78bfa", "print": "#67e8f9", "progress": "#94a3b8",
                "parallel": "#f472b6", "llm": "#a78bfa", "error": "#f87171",
            }
            for kind, msg in trace.output_log:
                color = color_map_log.get(kind, "#e2e8f0")
                log_lines.append(f'<span style="color:{color};">{msg}</span>')

            output_html = "\n".join(log_lines) if log_lines else '<span style="color:#475569;">No output.</span>'
            st.markdown(f'<div class="output-box">{output_html}</div>', unsafe_allow_html=True)

            # AST
            if trace.ast:
                with st.expander("🌳 Abstract Syntax Tree", expanded=False):
                    ast_lines = ast_to_lines(trace.ast)
                    ast_colored = []
                    for line in ast_lines:
                        line_html = line.replace("&", "&amp;").replace("<", "&lt;")
                        for keyword in ["BINOP", "ASSIGN", "IF", "PARALLEL", "ACTION_CMD", "COND"]:
                            line_html = line_html.replace(keyword, f'<span style="color:#fbbf24;">{keyword}</span>')
                        for keyword in ["NUM", "VAR"]:
                            line_html = line_html.replace(keyword, f'<span style="color:#a78bfa;">{keyword}</span>')
                        ast_colored.append(line_html)
                    st.markdown(
                        f'<div class="output-box" style="min-height:auto;">{"<br>".join(ast_colored)}</div>',
                        unsafe_allow_html=True
                    )
        else:
            st.markdown(
                '<div class="output-box" style="display:flex;align-items:center;justify-content:center;color:#1e3a5f;font-size:0.9rem;">'
                'Run a command to see output...'
                '</div>',
                unsafe_allow_html=True
            )

        # History
        if st.session_state.history:
            st.markdown('<p class="section-header" style="margin-top:20px;">Recent History</p>', unsafe_allow_html=True)
            hist_fig = make_history_bar(st.session_state.history)
            if hist_fig:
                st.plotly_chart(hist_fig, use_container_width=True, config={"displayModeBar": False})
                st.caption("Each bar = one command. Green=Tier1, Blue=Rule, Purple=LLM, Red=Fail")

            with st.expander(f"History Log ({len(st.session_state.history)} entries)", expanded=False):
                for i, h in enumerate(reversed(st.session_state.history[-10:])):
                    badge_cls = {"tier1": "badge-tier1", "rule": "badge-rule", "llm": "badge-llm"}.get(h["tier"], "badge-fail")
                    st.markdown(
                        f'<div style="display:flex;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid #1e2d40;">'
                        f'<span class="badge {badge_cls}">{h["tier"]}</span>'
                        f'<code style="font-size:0.78rem;color:#c9d1d9;">{h["input"]}</code>'
                        f'</div>',
                        unsafe_allow_html=True
                    )


# ════════════════════════════════════════════
# TAB 2: ANALYTICS
# ════════════════════════════════════════════
with tab2:
    s = st.session_state.stats
    total = max(s["total"], 1)

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, "#34d399", str(s["total"]), "Total Inputs"),
        (c2, "#34d399", f'{s["tier1"]/total:.0%}', "Tier-1 Rate"),
        (c3, "#60a5fa", f'{(s["rule"]+s["llm"])/total:.0%}', "Fallback Rate"),
        (c4, "#f87171", f'{s["fail"]/total:.0%}', "Failure Rate"),
    ]
    for col, accent, val, label in metrics:
        with col:
            st.markdown(
                f'<div class="metric-card" style="--accent:{accent};">'
                f'<div class="value">{val}</div>'
                f'<div class="label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    col_donut, col_bar = st.columns([1, 1.4], gap="large")

    with col_donut:
        st.markdown('<p class="section-header">Tier Distribution</p>', unsafe_allow_html=True)
        donut = make_tier_donut(s)
        st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})

    with col_bar:
        st.markdown('<p class="section-header">Tier Comparison</p>', unsafe_allow_html=True)
        categories = ["Tier-1\n(Grammar)", "Rule\nFallback", "LLM\nFallback", "Failed"]
        values = [s["tier1"], s["rule"], s["llm"], s["fail"]]
        colors = ["#34d399", "#60a5fa", "#a78bfa", "#f87171"]
        bar_fig = go.Figure(go.Bar(
            x=categories, y=values,
            marker=dict(color=colors, line=dict(width=0)),
            text=values, textposition="outside",
            textfont=dict(family="Space Mono", size=11, color="#94a3b8"),
            width=0.55,
        ))
        bar_fig.update_layout(
            **DARK_LAYOUT, height=260,
            xaxis=dict(showgrid=False, color="#475569", tickfont=dict(family="Space Mono", size=10)),
            yaxis=dict(showgrid=True, gridcolor="#1e2d40", color="#475569"),
        )
        st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})

    # History table
    if st.session_state.history:
        st.markdown('<p class="section-header" style="margin-top:8px;">Command History</p>', unsafe_allow_html=True)
        hist_df = pd.DataFrame(st.session_state.history)
        hist_df.index = hist_df.index + 1
        hist_df.columns = ["Input", "Tier", "Success", "Rewritten To"]
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.info("Run some commands in the Interpreter tab to see analytics here.", icon="ℹ️")


# ════════════════════════════════════════════
# TAB 3: PIPELINE EXPLORER
# ════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-header">Architecture Overview</p>', unsafe_allow_html=True)

    arch_col, desc_col = st.columns([1.3, 1], gap="large")

    with arch_col:
        # Architecture diagram using plotly
        fig = go.Figure()

        nodes = [
            (0.5, 0.92, "User Input", "#1e3a5f", "#60a5fa", 0.18),
            (0.5, 0.75, "Tokenizer\n(Lexer)", "#0d3326", "#34d399", 0.14),
            (0.5, 0.58, "Tier-1 Parser\n(Recursive Descent CFG)", "#1a1a0a", "#fbbf24", 0.22),
            (0.5, 0.41, "Semantic\nValidator", "#1a1a0a", "#fbbf24", 0.14),
            (0.18, 0.24, "Rule-Based\nFallback", "#0a1628", "#60a5fa", 0.16),
            (0.82, 0.24, "LLM Rewrite\n(Flan-T5)", "#13082a", "#a78bfa", 0.16),
            (0.5, 0.07, "Interpreter\n(Execute AST)", "#0d3326", "#34d399", 0.18),
        ]

        for x, y, label, bg, border, size in nodes:
            fig.add_shape(type="rect",
                x0=x-size, x1=x+size, y0=y-0.07, y1=y+0.07,
                fillcolor=bg, line=dict(color=border, width=1.5),
                layer="below")
            fig.add_annotation(
                x=x, y=y, text=label.replace("\n", "<br>"),
                showarrow=False,
                font=dict(family="Space Mono", size=9, color=border),
                align="center",
            )

        # Arrows
        arrows = [
            (0.5, 0.85, 0.5, 0.82),
            (0.5, 0.68, 0.5, 0.65),
            (0.5, 0.51, 0.5, 0.48),
            (0.3, 0.34, 0.18, 0.31),  # to rule
            (0.7, 0.34, 0.82, 0.31),  # to LLM
            (0.18, 0.17, 0.4, 0.14),  # rule -> exec
            (0.82, 0.17, 0.6, 0.14),  # LLM -> exec
            (0.5, 0.34, 0.5, 0.31),   # pass through (valid)
        ]
        for x0, y0, x1, y1 in arrows:
            fig.add_annotation(
                ax=x0, ay=y0, x=x1, y=y1,
                xref="paper", yref="paper",
                axref="pixel", ayref="pixel",
                showarrow=True,
                arrowhead=2, arrowsize=1, arrowwidth=1.5,
                arrowcolor="#1e3a5f",
            )

        # Labels on branches
        fig.add_annotation(x=0.28, y=0.39, text="FAIL", showarrow=False,
                           font=dict(family="Space Mono", size=8, color="#f87171"))
        fig.add_annotation(x=0.72, y=0.39, text="FAIL", showarrow=False,
                           font=dict(family="Space Mono", size=8, color="#f87171"))
        fig.add_annotation(x=0.55, y=0.39, text="OK", showarrow=False,
                           font=dict(family="Space Mono", size=8, color="#34d399"))

        fig.update_layout(
            **DARK_LAYOUT,
            height=420,
            xaxis=dict(visible=False, range=[0, 1]),
            yaxis=dict(visible=False, range=[0, 1]),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with desc_col:
        st.markdown('<p class="section-header">How it works</p>', unsafe_allow_html=True)

        steps_desc = [
            ("🔍", "#60a5fa", "Tokenizer",
             "Regex-based lexer converts raw text to a typed token stream. Keywords, operators, numbers, and identifiers are classified."),
            ("📐", "#fbbf24", "Tier-1 CFG Parser",
             "A recursive-descent parser attempts to match the token stream against the Context-Free Grammar. Builds an AST on success."),
            ("✅", "#34d399", "Semantic Validation",
             "Validates the parsed AST for semantic correctness (e.g. compute must have an expression, not a stopword object)."),
            ("🔀", "#60a5fa", "Rule Fallback",
             "Deterministic regex patterns rewrite informal phrasing into canonical grammar-valid commands. Fast and reliable for known patterns."),
            ("🤖", "#a78bfa", "LLM Rewrite",
             "Flan-T5 LLM rewrites unrecognized input into a canonical command. Output is validated before execution — LLM never executes directly."),
            ("⚡", "#34d399", "AST Interpreter",
             "The final, grammar-verified AST is executed by the tree-walking interpreter. Supports arithmetic, assignment, conditionals, and concurrency."),
        ]

        for icon, color, title, desc in steps_desc:
            st.markdown(f"""
            <div style="display:flex; gap:12px; padding: 10px 0; border-bottom: 1px solid #0f1625;">
                <span style="font-size:1.2rem; margin-top:2px;">{icon}</span>
                <div>
                    <div style="font-family:'Space Mono',monospace; font-size:0.8rem; color:{color}; font-weight:700;">{title}</div>
                    <div style="font-size:0.78rem; color:#64748b; margin-top:3px; line-height:1.5;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Safety principle
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0a1628,#0d1117); border:1px solid #1e3a5f; border-radius:12px; padding:18px 22px;">
        <div style="font-family:'Space Mono',monospace; font-size:0.75rem; color:#60a5fa; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">🔒 Core Safety Principle</div>
        <div style="font-size:0.85rem; color:#94a3b8; line-height:1.7;">
            The <strong style="color:#e2e8f0;">grammar is the final authority</strong>. The LLM never executes commands directly.
            All LLM-rewritten commands are <strong style="color:#e2e8f0;">re-parsed and verified</strong> by the CFG before execution.
            This prevents LLM hallucination from causing unintended or unsafe behaviour.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════
# TAB 4: GRAMMAR REFERENCE
# ════════════════════════════════════════════
with tab4:
    g_col1, g_col2 = st.columns(2, gap="large")

    with g_col1:
        st.markdown('<p class="section-header">EBNF Grammar</p>', unsafe_allow_html=True)
        grammar_text = """
command     ::= if_stmt
              | assign_stmt
              | parallel_cmd
              | action_cmd

if_stmt     ::= "if" condition "then" command
assign_stmt ::= "set" ID "=" expression
parallel_cmd::= action_cmd "while" action_cmd
action_cmd  ::= "compute" expression
              | ("sort"|"print"|"show") [OBJECT|ID]

condition   ::= expression COMP_OP expression
COMP_OP     ::= ">" | "<" | ">=" | "<=" | "=="

expression  ::= term (("+"|"-") term)*
term        ::= factor (("*"|"/") factor)*
factor      ::= NUMBER | ID | "(" expression ")"

OBJECT      ::= "numbers"|"number"|"list"
              | "progress"|"result"
ID          ::= [A-Za-z_][A-Za-z_0-9]*
NUMBER      ::= [0-9]+ ("." [0-9]+)?
""".strip()
        st.markdown(
            f'<div class="output-box">{grammar_text}</div>',
            unsafe_allow_html=True
        )

        st.markdown('<p class="section-header" style="margin-top:20px;">Token Types</p>', unsafe_allow_html=True)
        token_data = {
            "Token": ["ACTION", "OBJECT", "IF/THEN", "SET", "WHILE", "NUMBER", "ID", "OPERATORS"],
            "Examples": ["sort, print, show, compute", "numbers, progress, result", "if, then",
                         "set", "while", "42, 3.14", "x, score, result", "+ - * / > < >= <= == ="],
            "Color": ["#34d399", "#60a5fa", "#fbbf24", "#fb923c", "#f472b6", "#a78bfa", "#67e8f9", "#94a3b8"],
        }
        for tok, ex, col in zip(token_data["Token"], token_data["Examples"], token_data["Color"]):
            st.markdown(
                f'<div style="display:flex;gap:12px;align-items:center;padding:7px 0;border-bottom:1px solid #0f1625;">'
                f'<code style="font-family:Space Mono;font-size:0.75rem;color:{col};min-width:80px;">{tok}</code>'
                f'<span style="font-size:0.78rem;color:#64748b;">{ex}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    with g_col2:
        st.markdown('<p class="section-header">Example Commands</p>', unsafe_allow_html=True)
        examples_ref = [
            ("Arithmetic", "compute 1 + 2 * 3", "tier1", "result = 7"),
            ("Assignment", "set x = 10", "tier1", "x = 10"),
            ("Conditional", "if x > 5 then print result", "tier1", "[IF] condition true"),
            ("Sort", "sort numbers", "tier1", "[SORT] Sorting numbers..."),
            ("Concurrency", "sort numbers while show progress", "tier1", "[CONCURRENCY] Parallel"),
            ("Rule → set", "store 99 in variable score", "rule", "set score = 99"),
            ("Rule → compute", "calculate 5 times (2 plus 3)", "rule", "compute 5 * (2+3)"),
            ("LLM → sort", "pls organize this list", "llm", "sort numbers"),
            ("LLM → sort", "arrange these numbers", "llm", "sort numbers"),
        ]
        badge_cls_map = {"tier1": "badge-tier1", "rule": "badge-rule", "llm": "badge-llm"}

        for title, cmd, tier, result in examples_ref:
            badge_cls = badge_cls_map.get(tier, "badge-fail")
            st.markdown(f"""
            <div style="background:#0d1117; border:1px solid #21262d; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <span style="font-size:0.72rem; color:#475569; text-transform:uppercase; letter-spacing:0.08em;">{title}</span>
                    <span class="badge {badge_cls}">{tier}</span>
                </div>
                <code style="font-family:'Space Mono',monospace; font-size:0.82rem; color:#93c5fd;">{cmd}</code>
                <div style="font-size:0.75rem; color:#34d399; margin-top:5px; font-family:'Space Mono',monospace;">→ {result}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<p class="section-header" style="margin-top:16px;">Rule Fallback Patterns</p>', unsafe_allow_html=True)
        rules = [
            ("store/save/put N in variable X", "set X = N"),
            ("calculate/calc … plus/minus/times", "compute …"),
            ("show/display the result", "print result"),
            ("organize/sort … while show status", "sort numbers while show progress"),
            ("sort/arrange/organize + list/numbers", "sort numbers"),
        ]
        for pattern, output in rules:
            st.markdown(
                f'<div style="display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #0f1625;align-items:flex-start;">'
                f'<code style="font-size:0.76rem;color:#60a5fa;min-width:260px;flex-shrink:0;">{pattern}</code>'
                f'<span style="color:#475569;font-size:0.75rem;">→</span>'
                f'<code style="font-size:0.76rem;color:#34d399;">{output}</code>'
                f'</div>',
                unsafe_allow_html=True
            )