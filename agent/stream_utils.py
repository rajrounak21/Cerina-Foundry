
import contextvars
from typing import Callable, Optional

# ContextVar to hold the callback function for streaming tokens
# The callback should accept a string (token)
stream_callback_var: contextvars.ContextVar[Optional[Callable[[str], None]]] = contextvars.ContextVar("stream_callback", default=None)

def set_stream_callback(callback: Callable[[str], None]):
    return stream_callback_var.set(callback)

def get_stream_callback() -> Optional[Callable[[str], None]]:
    return stream_callback_var.get()
