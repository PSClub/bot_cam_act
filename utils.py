# utils.py
# Centralized utility functions for the tennis court booking system

import pytz
from datetime import datetime

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds in London UK timezone."""
    uk_tz = pytz.timezone('Europe/London')
    london_time = datetime.now(uk_tz)
    return f"[{london_time.strftime('%H:%M:%S.%f')[:-4]}]"

def get_current_london_time():
    """Get current time in London timezone as formatted string."""
    uk_tz = pytz.timezone('Europe/London')
    london_time = datetime.now(uk_tz)
    return london_time.strftime('%Y-%m-%d %H:%M:%S')

def get_london_datetime():
    """Get current datetime object in London timezone."""
    uk_tz = pytz.timezone('Europe/London')
    return datetime.now(uk_tz)
