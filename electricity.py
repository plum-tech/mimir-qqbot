import re
import requests


def extract_room_number(s: str) -> int | None:
    numbers = re.findall(r'\d+', s)
    if len(numbers) < 1 or len(numbers) > 1:
        return
    return numbers[0]


class ElectricityBalance:
    def __init__(self, room_number: str, balance: float):
        self.room_number = room_number
        self.balance = balance

    def __str__(self):
        return f"#{self.room_number}: ¥{self.balance}"


def fetch(room_number: str | int, throws=False) -> ElectricityBalance | None:
    return ElectricityBalance(str(room_number),0)
