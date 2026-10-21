import unittest

from src.report import average


class TestBasicAverage(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(average([1, 2]), 1.5)

    def test_single(self):
        self.assertEqual(average([4]), 4.0)


if __name__ == "__main__":
    unittest.main()
