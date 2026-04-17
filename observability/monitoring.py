import logging
from functools import wraps
from typing import Callable, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_request(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for logging request information.  Supports async functions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logging.info(f"Request received for: {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = await func(*args, **kwargs) if hasattr(func, "__call__") and hasattr(func, "__code__") and func.__code__.co_flags & 0x20 else func(*args, **kwargs) # Check if it is a coroutine
            logging.info(f"Request completed for: {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error processing request for: {func.__name__}: {e}")
            raise
    return wrapper