import pytest
from src.numerical.calculator import NumericalCalculator


def test_numerical_script_a_values():
    calc = NumericalCalculator()

    # 1. 2^8 = 256
    res1 = calc.evaluate("2^8")
    assert res1["result"] == 256
    assert res1["formatted_result"] == "256"

    # 2. 256 * 256 * 256 = 16,777,216
    res2 = calc.evaluate("256 * 256 * 256")
    assert res2["result"] == 16777216
    assert res2["formatted_result"] == "16,777,216"

    # 3. range 0 to 255
    res3 = calc.evaluate("0 to 255")
    assert res3["result"] == (0, 255)
    assert res3["formatted_result"] == "0–255"

    # 4. tuple (255, 0, 0)
    res4 = calc.evaluate("(255, 0, 0)")
    assert res4["result"] == (255, 0, 0)
    assert res4["formatted_result"] == "(255, 0, 0)"


def test_numerical_unsafe_expression():
    calc = NumericalCalculator()
    # Unsafe function call should return warning and passed-through text
    res = calc.evaluate("__import__('os').system('dir')")
    assert "warning" in res
    assert res["formatted_result"] == "__import__('os').system('dir')"
