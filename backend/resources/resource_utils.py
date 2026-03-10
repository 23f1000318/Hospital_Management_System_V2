from datetime import datetime

def validate_date(value):
    """Parse date string to datetime object"""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {value}. Use YYYY-MM-DD")

def validate_time(value):
    """Parse time string to time object"""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise ValueError(f"Invalid time format: {value}. Use HH:MM")
