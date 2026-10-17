import unittest

from app import CalculationError, calculate


class CalculateTests(unittest.TestCase):
    def test_basic_arithmetic_and_precedence(self):
        self.assertEqual(calculate("2+3*4"), "14")
        self.assertEqual(calculate("(2+3)*4"), "20")
        self.assertEqual(calculate("-5+2"), "-3")

    def test_decimal_and_power(self):
        self.assertEqual(calculate("0.1+0.2"), "0.3")
        self.assertEqual(calculate("(3)**2"), "9")

    def test_square_root(self):
        self.assertEqual(calculate("sqrt(81)"), "9")

    def test_invalid_and_unsafe_expressions_are_rejected(self):
        for expression in (
            "",
            "1/0",
            "sqrt(-1)",
            "(-1)**0.5",
            "__import__('os')",
            "2**100",
            "9" * 255,
        ):
            with self.subTest(expression=expression):
                with self.assertRaises(CalculationError):
                    calculate(expression)

    def test_expression_limits(self):
        with self.assertRaises(CalculationError):
            calculate("1+" * 130 + "1")


if __name__ == "__main__":
    unittest.main()
