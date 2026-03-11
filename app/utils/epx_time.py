from datetime import datetime, timezone
def is_expire(expire_time: datetime) -> bool:
    return expire_time < datetime.now(timezone.utc)