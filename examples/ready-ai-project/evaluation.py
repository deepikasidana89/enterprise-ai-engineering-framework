"""Repeatable evaluation entry point for the example AI application."""


def evaluate(output: str) -> float:
    expected = "answer"
    return 1.0 if expected in output.lower() else 0.0


def run_evaluation() -> float:
    return evaluate("example answer")
