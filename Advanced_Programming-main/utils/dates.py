# utils/dates.py

from datetime import date, timedelta


def week_range(day: date) -> tuple[date, date]:
    """
    Given any date, return (monday, sunday) of that week.
    """
    # weekday(): Monday = 0, Sunday = 6
    start = day - timedelta(days=day.weekday())
    end = start + timedelta(days=6)
    return start, end