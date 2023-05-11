from config.config import *
config = getConfig()

_lock = threading.Lock()

def locked(func):
    def with_locking(*args, **kwargs):
        with _lock:
            return func(*args, **kwargs)

    return with_locking