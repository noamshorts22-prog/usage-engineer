from .config import RETRY_LIMIT


def send():
    return "retrying up to %d times" % RETRY_LIMIT
