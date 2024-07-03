import re


def extract_room_number(s: str) -> int | None:
    numbers = re.findall(r'\d+', s)
    if len(numbers) < 1 or len(numbers) > 1:
        return
    return numbers[0]
