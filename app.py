import ast
import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


APP_DIR = Path(__file__).resolve().parent
MAX_EXPRESSION_LENGTH = 256
MAX_AST_NODES = 64
MAX_RESULT_MAGNITUDE = 1e100


class CalculationError(ValueError):
    """Raised when an expression is invalid or outside supported limits."""


def _checked_number(value: int | float) -> float:
    if type(value) not in (int, float):
        raise CalculationError("The result must be a real number.")
    if abs(value) > MAX_RESULT_MAGNITUDE or not math.isfinite(value):
        raise CalculationError("The result is outside the supported range.")
    return float(value)


def _evaluate_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return _checked_number(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_node(node.operand)
        return _checked_number(value if isinstance(node.op, ast.UAdd) else -value)
    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        if isinstance(node.op, ast.Add):
            result = left + right
        elif isinstance(node.op, ast.Sub):
            result = left - right
        elif isinstance(node.op, ast.Mult):
            result = left * right
        elif isinstance(node.op, ast.Div):
            if right == 0:
                raise CalculationError("Cannot divide by zero.")
            result = left / right
        elif isinstance(node.op, ast.Pow):
            if abs(right) > 12 or (abs(left) > 1e50 and right > 1):
                raise CalculationError("That exponent is outside the supported range.")
            try:
                result = left**right
            except (OverflowError, ZeroDivisionError, ValueError):
                raise CalculationError("That operation is outside the supported range.") from None
        else:
            raise CalculationError("That operator is not supported.")
        return _checked_number(result)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "sqrt"
        and len(node.args) == 1
        and not node.keywords
    ):
        value = _evaluate_node(node.args[0])
        if value < 0:
            raise CalculationError("Cannot take the square root of a negative number.")
        return _checked_number(math.sqrt(value))
    raise CalculationError("Enter a valid arithmetic expression.")


def calculate(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip():
        raise CalculationError("Enter an expression first.")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculationError("The expression is too long.")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, MemoryError, RecursionError):
        raise CalculationError("Enter a valid arithmetic expression.") from None
    if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
        raise CalculationError("The expression is too complex.")
    result = _evaluate_node(tree)
    return format(result, ".12g")


class CalculatorHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        files = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/style.css": ("style.css", "text/css; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
        }
        if path not in files:
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        filename, content_type = files[path]
        try:
            body = (APP_DIR / filename).read_bytes()
        except OSError:
            self._send(500, b"Unable to load the application.", "text/plain; charset=utf-8")
            return
        self._send(200, body, content_type)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/calculate":
            self._send_json(404, {"error": "Not found."})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid request."})
            return
        if content_length <= 0 or content_length > 4096:
            self._send_json(400, {"error": "Invalid request size."})
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Send a valid JSON request."})
            return
        if not isinstance(payload, dict) or not isinstance(payload.get("expression"), str):
            self._send_json(400, {"error": "Include an expression to calculate."})
            return
        try:
            result = calculate(payload["expression"])
        except CalculationError as error:
            self._send_json(400, {"error": str(error)})
            return
        self._send_json(200, {"result": result})

    def log_message(self, format: str, *args: Any) -> None:
        print("%s - %s" % (self.address_string(), format % args))


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), CalculatorHandler)
    print(f"Calculator running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down calculator server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
