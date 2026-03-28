from typing import Dict

def calculate_total_price(details: Dict[str, float]) -> float:
    if not isinstance(details, dict):
        raise ValueError("details must be a dictionary")

    total = 0.0

    for key, value in details.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"Invalid value for '{key}': must be a number")
        if value < 0:
            raise ValueError(f"Invalid value for '{key}': cannot be negative")

        total += float(value)

    return total