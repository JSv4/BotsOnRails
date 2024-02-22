from enum import Enum
from typing import TypeVar

IT = TypeVar('IT')  # Generic for Input Type
OT = TypeVar('OT')  # Generic for Output Type


class SpecialTypes(Enum):
    NO_RETURN = 'NO_RETURN'
    EXECUTION_HALTED = 'EXECUTION_HALTED'
