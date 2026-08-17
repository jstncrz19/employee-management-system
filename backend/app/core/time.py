from datetime import datetime, date, time
from zoneinfo import ZoneInfo

from config import APP_TIMEZONE

TIMEZONE = ZoneInfo(APP_TIMEZONE)

def now() -> datetime:
    return datetime.now(TIMEZONE)

def today() -> date:
    return now().date()

def current_time() -> time:
    return now().time()