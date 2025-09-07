from enum import Enum
from typing import List, Tuple


class PaymentStatus(Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    REJECTED = "Rejected"

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
    def validate(cls, category: str) -> bool:
        return category in {s.value for s in cls}
    
    