from datetime import datetime, time

def parse_time_string(value: str) -> time:
    value = value.strip().lower()

    formats = [
        "%I:%M%p",   # 9:30am
        "%I:%M %p",  # 9:30 am
        "%H:%M",     # 21:30
        "%H:%M:%S",  # 21:30:00
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    raise ValueError("Invalid time format")



from datetime import datetime, date, time

def parse_date_string(value: str) -> date:
    value = value.strip()

    # List of common date formats you expect
    formats = [
        "%d/%m/%y",     # 23/02/26
        "%d/%m/%Y",     # 23/02/2026
        "%Y-%m-%d",     # 2026-02-23
        "%d-%m-%y",     # 23-02-26
        "%d-%m-%Y",     # 23-02-2026
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError("Invalid date format")