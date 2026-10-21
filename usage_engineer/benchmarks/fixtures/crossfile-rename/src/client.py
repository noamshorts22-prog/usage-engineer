from .config import MAX_RETRIES


def send():
    return "retrying up to %d times" % MAX_RETRIES
