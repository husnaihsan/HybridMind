# HybridMind  
**Grammar-Driven, LLM-Assisted Natural Language Interpreter**

HybridMind is a prototype natural-language programming system that combines a **formal grammar-based interpreter** with an **LLM fallback mechanism** to balance correctness and flexibility. The system interprets simple natural-language commands such as arithmetic computation, conditional execution, and (later) concurrent actions, while ensuring deterministic and verifiable execution.

This project is developed as part of the WIF3010 Programming Language Paradigms coursework.

---

## 📌 Project Motivation

Natural-language interfaces are increasingly used to express computational tasks. However:

- **Pure grammar-based systems** are strict and fail when users use synonyms or informal phrasing.
- **Pure LLM-based systems** are flexible but may hallucinate, misinterpret intent, or produce logically incorrect results.

Based on literature review and interview insights from a practising data analyst, we observed that users often struggle with:
- Ambiguous natural-language commands
- Missing or unclear context
- Over-trusting LLM outputs without verification

HybridMind addresses this gap using a **two-tier hybrid architecture**:
1. Grammar-first parsing for correctness and control
2. LLM-assisted rewriting only when grammar parsing fails

---

## 🎯 Project Objectives

- Design a **context-free grammar (CFG)** using EBNF for structured natural-language commands
- Implement a **recursive-descent parser** and interpreter in Python
- Construct a **two-tier hybrid interpreter**:
  - Tier 1: Grammar-based parsing and deterministic execution
  - Tier 2: LLM fallback to resolve ambiguity and synonyms
- Extend the language with a **concurrency paradigm** using natural expressions such as  
  `"sort numbers while printing progress"`
- Evaluate correctness, ambiguity handling, and execution behaviour

---

## 🧠 System Overview


### HybridMind Processing Pipeline

HybridMind processes user input through the following steps:

1. User input is first tokenized by a regex-based lexical analyzer.
2. The token stream is parsed using a recursive-descent parser.
3. If the input conforms to the grammar, an abstract syntax tree (AST) is generated and executed by the interpreter.
4. If parsing fails, the system invokes an LLM to rewrite the input into a grammar-compliant command.
5. The rewritten command is re-verified by the grammar before execution.

This grammar-first approach ensures deterministic execution while allowing flexibility for ambiguous or informal inputs.


- The grammar is the **final authority**
- The LLM never executes commands directly
- All rewritten commands are re-verified before execution

---

## ✍️ Supported Language Features

### Core Commands (Deliverable 3)
- Assignment:  
  `set x = 10 + 5`
- Arithmetic expressions with precedence:  
  `compute x * 2`
- Conditional statements:  
  `if x > 10 then print result`
- Action commands:  
  `print result`, `sort numbers`

### Hybrid Extension (Deliverable 4)
- Informal and ambiguous input handling using LLM fallback:  
  `pls organize this list` → `sort numbers`

### Paradigm Extension (Deliverable 5)
- **Concurrency** using natural syntax:  
  `sort numbers while print progress`

---

## 🛠️ Implementation Details

- **Language**: Python 3
- **Lexer**: Regex-based scanner
- **Parser**: Hand-written recursive-descent parser
- **Interpreter**: AST-based deterministic execution
- **LLM Integration**:
  - Google Gemini (real API)
  - Simulated LLM fallback for robustness and offline safety
- **Concurrency**: Python threading

---

## ▶️ How to Run

### 1. Clone or open the project folder
```bash
cd HybridMind

