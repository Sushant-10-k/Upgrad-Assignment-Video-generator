import ast
import operator
import re
import logging
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

# Allowed AST operators for safe mathematical evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval_ast(node: ast.AST) -> Union[int, float]:
    """Safely evaluate an AST expression with an allow-list of operators."""
    if isinstance(node, ast.Expression):
        return safe_eval_ast(node.body)
    elif isinstance(node, ast.Constant):  # Python 3.8+ for numbers
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        left = safe_eval_ast(node.left)
        right = safe_eval_ast(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = safe_eval_ast(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    else:
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")


class NumericalCalculator:
    """Deterministic Numerical Reasoning Engine."""

    @staticmethod
    def normalize_expression(expr: str) -> str:
        """Normalize math symbols to valid Python expression syntax."""
        expr_clean = expr.replace("×", "*").replace("x", "*").replace("^", "**").replace("–", "-")
        return expr_clean.strip()

    def evaluate(self, expression_str: str) -> Dict[str, Any]:
        """
        Safely evaluate a numerical expression or formatted tuple/range string.
        Returns dict matching PRD §11:
        {
            "expression": original_str,
            "result": evaluated_result,
            "formatted_result": string_formatted_result
        }
        """
        raw_expr = expression_str.strip()
        normalized = self.normalize_expression(raw_expr)

        # Handle tuple like (255, 0, 0)
        tuple_match = re.match(r"^\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", raw_expr)
        if tuple_match:
            vals = tuple(int(g) for g in tuple_match.groups())
            return {
                "expression": raw_expr,
                "result": vals,
                "formatted_result": f"({vals[0]}, {vals[1]}, {vals[2]})"
            }

        # Handle range like 0 to 255 or 0-255
        range_match = re.match(r"^(\d+)\s*(?:to|-|–)\s*(\d+)$", raw_expr)
        if range_match:
            start_val, end_val = int(range_match.group(1)), int(range_match.group(2))
            return {
                "expression": raw_expr,
                "result": (start_val, end_val),
                "formatted_result": f"{start_val}–{end_val}"
            }

        # Evaluate mathematical AST expression
        try:
            parsed = ast.parse(normalized, mode="eval")
            res = safe_eval_ast(parsed)

            # Format integer with commas if large
            if isinstance(res, float) and res.is_integer():
                res = int(res)

            formatted = f"{res:,}" if isinstance(res, int) else str(res)

            return {
                "expression": raw_expr,
                "result": res,
                "formatted_result": formatted
            }
        except Exception as e:
            logger.warning(f"WARNING: Could not safely evaluate expression '{expression_str}': {e}")
            return {
                "expression": raw_expr,
                "result": raw_expr,
                "formatted_result": raw_expr,
                "warning": f"Could not safely evaluate: {e}"
            }
