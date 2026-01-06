import time
import threading

env = {}
_stop_progress = threading.Event()

def eval_expr(node):
    kind = node[0]
    if kind == "NUM":
        return node[1]
    if kind == "VAR":
        return env.get(node[1], 0)
    if kind == "BINOP":
        op, left, right = node[1], node[2], node[3]
        lval = eval_expr(left)
        rval = eval_expr(right)
        if op == "PLUS":  return lval + rval
        if op == "MINUS": return lval - rval
        if op == "TIMES": return lval * rval
        if op == "DIV":   return lval / rval
    raise RuntimeError(f"Unknown expr node: {node}")

def eval_condition(node):
    _, op, left, right = node
    lval = eval_expr(left)
    rval = eval_expr(right)
    if op == "GT": return lval > rval
    if op == "LT": return lval < rval
    if op == "GE": return lval >= rval
    if op == "LE": return lval <= rval
    if op == "EQ": return lval == rval
    raise RuntimeError(f"Unknown condition op: {op}")

def do_sort(obj):
    target = obj or "numbers"
    print(f"[SORT] Sorting {target}...")
    time.sleep(2)
    print(f"[SORT] Done sorting {target}.")

def do_compute(expr_node):
    val = eval_expr(expr_node)
    env["result"] = val
    print(f"[COMPUTE] result = {val}")

def do_print(value):
    print(f"[PRINT] {value}")

def show_progress(label="progress"):
    i = 0
    while not _stop_progress.is_set():
        i += 1
        print(f"[PROGRESS] {label}... {i}")
        time.sleep(0.5)

def run_parallel(cmd1, cmd2):
    _stop_progress.clear()

    t1 = threading.Thread(target=lambda: execute(cmd1))
    t2 = threading.Thread(target=lambda: execute(cmd2))

    start = time.time()
    t1.start(); t2.start()

    t1.join()
    _stop_progress.set()
    t2.join()

    elapsed = time.time() - start
    print(f"[CONCURRENCY] Done in ~{elapsed:.2f}s")

def execute(node):
    kind = node[0]

    if kind == "ASSIGN":
        _, name, expr = node
        env[name] = eval_expr(expr)
        print(f"[ASSIGN] {name} = {env[name]}")
        return

    if kind == "IF":
        _, cond, body = node
        if eval_condition(cond):
            print("[IF] condition true → executing body")
            execute(body)
        else:
            print("[IF] condition false → skipping body")
        return

    if kind == "PARALLEL":
        _, left, right = node
        print("[CONCURRENCY] Running in parallel...")
        run_parallel(left, right)
        return

    if kind == "ACTION_CMD":
        _, action, obj, expr = node
        if action == "sort":
            do_sort(obj); return
        if action == "compute":
            do_compute(expr); return
        if action in ("print", "show"):
            if obj == "result":
                do_print(env.get("result", None))
            elif obj == "progress":
                show_progress("progress")
            elif obj in env:
                do_print(env[obj])
            else:
                do_print(obj)
            return

    raise RuntimeError(f"Unknown AST node: {node}")
