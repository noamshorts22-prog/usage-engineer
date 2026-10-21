from .config import RETRY_LIMIT


def effective_retries():
    return RETRY_LIMIT
