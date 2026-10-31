"""Calculator app: Flask backend + SQLite history + responsive frontend."""
import ast
import operator
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request

DB_PATH = Path(__file__).with_name("calculator.db")
app = Flask(__name__)

# Only these operators are allowed -> safe alternative to eval()
OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def evaluate(node):
    """Recursively evaluate a parsed arithmetic expression."""
    if isinstance(node, ast.Expression):
        return evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left, right = evaluate(node.left), evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent too large")
        return OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        return UNARY[type(node.op)](evaluate(node.operand))
    raise ValueError("Invalid expression")


def calculate(expression: str) -> str:
    tree = ast.parse(expression.replace("×", "*").replace("÷", "/"), mode="eval")
    result = evaluate(tree)
    if isinstance(result, float):
        result = round(result, 10)
        if result == int(result) and abs(result) < 1e15:
            result = int(result)
    return str(result)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        )


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/calculate")
def api_calculate():
    expression = (request.get_json(silent=True) or {}).get("expression", "").strip()
    if not expression or len(expression) > 200:
        return jsonify(error="Enter an expression to calculate"), 400
    try:
        result = calculate(expression)
    except ZeroDivisionError:
        return jsonify(error="Cannot divide by zero"), 400
    except (ValueError, SyntaxError, OverflowError):
        return jsonify(error="Invalid expression"), 400
    with db() as conn:
        conn.execute("INSERT INTO history (expression, result) VALUES (?, ?)", (expression, result))
    return jsonify(result=result)


@app.get("/api/history")
def api_history():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, expression, result FROM history ORDER BY id DESC LIMIT 30"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.delete("/api/history")
def api_clear_history():
    with db() as conn:
        conn.execute("DELETE FROM history")
    return jsonify(ok=True)


init_db()
if __name__ == "__main__":
    app.run(debug=True)
