from enum import Enum
from typing import TypeVar

IT = TypeVar('IT')  # Generic for Input Type
OT = TypeVar('OT')  # Generic for Output Type


class SpecialTypes(str, Enum):
    NORETURN = 'NORETURN'
