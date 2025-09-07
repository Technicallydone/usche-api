from enum import Enum
from typing import List, Tuple


class AttendeeStatus(Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    WAITING = "waiting"
    ATTENDED = "attended"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """Returns a list of (value, value) tuples for use in the model choices."""
        return [(status.value, status.value) for status in cls]

    @classmethod
    def default(cls) -> str:
        """Returns the default value of the status."""
        return cls.ACTIVE.value

    @classmethod
    def validate(cls, value) -> bool:
        """Validates if a value is a valid status."""
        return value in {status.value for status in cls}