import unittest

from src.report import average


class TestAverageEmptyRegression(unittest.TestCase):
    def test_empty_input_returns_zero(self):
        self.assertEqual(average([]), 0.0)


if __name__ == "__main__":
    unittest.main()
