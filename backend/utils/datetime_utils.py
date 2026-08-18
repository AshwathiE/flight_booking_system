import logging
from datetime import datetime, date, time, timezone, timedelta
from typing import Optional, Union

logger = logging.getLogger("datetime_utils")

# Configure Asia/Kolkata Timezone
try:
    from zoneinfo import ZoneInfo
    KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


def get_current_datetime_kolkata() -> datetime:
    """Get current timezone-aware datetime in Asia/Kolkata."""
    return datetime.now(KOLKATA_TZ)


def get_current_date_kolkata() -> date:
    """Get current date in Asia/Kolkata."""
    return get_current_datetime_kolkata().date()


def parse_flight_departure_datetime(
    flight_date: Union[date, str, None],
    departure_time_str: Union[time, str, None]
) -> Optional[datetime]:
    """
    Combine flight date (date object or str YYYY-MM-DD) and departure time
    (time object or str HH:MM/HH:MM:SS) into a timezone-aware Asia/Kolkata datetime.
    """
    if not flight_date or not departure_time_str:
        return None

    # 1. Parse date
    if isinstance(flight_date, date):
        d = flight_date
    else:
        try:
            d = datetime.strptime(str(flight_date).strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    # 2. Parse departure time
    if isinstance(departure_time_str, time):
        t = departure_time_str
    else:
        t_str = str(departure_time_str).strip()
        t = None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t = datetime.strptime(t_str, fmt).time()
                break
            except ValueError:
                continue
        if t is None:
            return None

    # 3. Combine and set Asia/Kolkata timezone
    dt_naive = datetime.combine(d, t)
    return dt_naive.replace(tzinfo=KOLKATA_TZ)


def is_flight_in_future(
    flight_date: Union[date, str, None],
    departure_time_str: Union[time, str, None],
    flight_id: str = ""
) -> bool:
    """
    Check if a flight's departure datetime is strictly in the future
    relative to current Asia/Kolkata datetime.
    
    Logs comparison details as required:
    [CURRENT TIME]
    Current datetime: ...
    [FLIGHT TIME]
    Flight {flight_id} departure: ...
    [FLIGHT VALIDATION]
    Flight {flight_id} is in the future → ALLOWED / REJECTED
    """
    curr_dt = get_current_datetime_kolkata()
    flight_dt = parse_flight_departure_datetime(flight_date, departure_time_str)

    if flight_dt is None:
        return False

    is_future = flight_dt > curr_dt
    fid = f"Flight {flight_id} " if flight_id else "Flight "

    if is_future:
        logger.info(
            "\n[CURRENT TIME]\nCurrent datetime: %s\n"
            "[FLIGHT TIME]\n%sdeparture: %s\n"
            "[FLIGHT VALIDATION]\n%sis in the future → ALLOWED",
            curr_dt.strftime("%Y-%m-%d %H:%M:%S%z"),
            fid,
            flight_dt.strftime("%Y-%m-%d %H:%M:%S%z"),
            fid
        )
    else:
        logger.info(
            "\n[CURRENT TIME]\nCurrent datetime: %s\n"
            "[FLIGHT TIME]\n%sdeparture: %s\n"
            "[FLIGHT VALIDATION]\n%sdeparture time has passed → REJECTED",
            curr_dt.strftime("%Y-%m-%d %H:%M:%S%z"),
            fid,
            flight_dt.strftime("%Y-%m-%d %H:%M:%S%z"),
            fid
        )

    return is_future
