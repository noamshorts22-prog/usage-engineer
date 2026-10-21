import unittest

from src.calc import sum_range


class TestSumRange(unittest.TestCase):
    def test_small_inclusive(self):
        self.assertEqual(sum_range(1, 3), 6)

    def test_single(self):
        self.assertEqual(sum_range(5, 5), 5)

    def test_negative(self):
        self.assertEqual(sum_range(-2, 2), 0)


if __name__ == "__main__":
    unittest.main()
