import time
import logging
from functools import wraps

def retry(tentativas=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for tentativa in range(tentativas):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.warning(f"Tentativa {tentativa+1} falhou na função {func.__name__}: {e}")
                    time.sleep(delay)
            raise Exception(f"Falha na função {func.__name__} após {tentativas} tentativas")
        return wrapper
    return decorator