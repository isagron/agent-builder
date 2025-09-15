"""Calculator tool for mathematical operations."""

from __future__ import annotations

import ast
import operator
from typing import Any

from langchain.tools import tool


@tool
def calculator(expression: str) -> str:
    """
    Perform mathematical calculations and evaluate expressions safely.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., '2 + 3 * 4')
    
    Returns:
        The result of the calculation as a string
    """
    try:
        result = _safe_eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation failed: {str(e)}"


def _safe_eval(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    # Strip extra quotes if present (agent sometimes passes quoted expressions)
    if expression.startswith("'") and expression.endswith("'"):
        expression = expression[1:-1]
    elif expression.startswith('"') and expression.endswith('"'):
        expression = expression[1:-1]
    
    # Allowed operators and functions
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    functions = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
    }
    
    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        elif isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op = operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op = operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")
            func_name = node.func.id
            if func_name not in functions:
                raise ValueError(f"Function '{func_name}' is not allowed")
            args = [_eval_node(arg) for arg in node.args]
            return functions[func_name](*args)
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")
    
    try:
        tree = ast.parse(expression, mode='eval')
        return _eval_node(tree)
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {e}")
