import unittest

from src.client import send
from src.worker import effective_retries


class TestRetryBehavior(unittest.TestCase):
    def test_effective_retries_unchanged(self):
        self.assertEqual(effective_retries(), 3)

    def test_client_message_unchanged(self):
        self.assertEqual(send(), "retrying up to 3 times")


if __name__ == "__main__":
    unittest.main()
