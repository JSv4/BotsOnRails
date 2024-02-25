from enum import Enum
from typing import TypeVar

IT = TypeVar('IT')  # Generic for Input Type
OT = TypeVar('OT')  # Generic for Output Type


class SpecialTypes(str, Enum):
    NO_RETURN = '__NO_RETURN--'
    NEVER_FINISHED = "__NEVER_FINISHED--"
    NOT_PROVIDED = "__NOT_PROVIDED--"
    EXECUTION_HALTED = '__EXECUTION_HALTED--'
