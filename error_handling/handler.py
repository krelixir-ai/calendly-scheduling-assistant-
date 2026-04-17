import time
import random

def retry(func, attempts=3, delay=1, exponential_backoff=True):
    """
    Retry a function with exponential backoff.
    """
    for attempt in range(attempts):
        try:
            return func()
        except Exception as e:
            if attempt == attempts - 1:
                raise
            sleep_time = delay * (2 ** attempt) if exponential_backoff else delay
            sleep_time = sleep_time + random.uniform(0, 0.5)  # Add some jitter
            print(f"Attempt {attempt + 1} failed. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)