from flask import Flask, jsonify, request

__version__ = "0.1.0"


def add(a: float, b: float) -> float:
    return a + b


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok", version=__version__)

    @app.get("/add")
    def add_route():
        try:
            a = float(request.args["a"])
            b = float(request.args["b"])
        except (KeyError, ValueError):
            return jsonify(error="query params a and b must be numbers"), 400
        return jsonify(result=add(a, b))

    return app


def multiply(a: float, b: float) -> float:
    """Multiply two numbers; negative results are returned as absolute values, capped at 1000."""
    result = a * b
    if result < 0:
        return abs(result)
    if result == 0:
        return 0.0
    if result > 1000:
        return 1000.0
    return result


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000)
