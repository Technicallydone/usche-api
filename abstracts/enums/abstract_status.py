from enum import Enum
from typing import List, Tuple


class AbstractStatus(Enum):
    PENDING = "Pending"
    REQUIRE_PAYMENT = "Require Payment"
    REJECTED = "Rejected"
    APPROVED = "Approved"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(status.value, status.value) for status in cls]

    @classmethod
    def default(cls) -> str:
        return cls.PENDING.value
    
    @classmethod
    def values(cls) -> List[str]:
        return [s.value for s in cls]
    
    @classmethod
    def validate(cls, status: str) -> bool:
        return status in {s.value for s in cls}