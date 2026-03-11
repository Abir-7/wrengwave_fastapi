import random
import string
from typing import Literal

def generate_code(length: int = 6, mode: Literal["numbers", "letters", "mixed"] = "mixed") -> str:
    char_sets = {
        "numbers": string.digits,
        "letters": string.ascii_letters,
        "mixed": string.ascii_letters + string.digits,
    }

    chars = char_sets[mode]
    return "".join(random.choice(chars) for _ in range(length))