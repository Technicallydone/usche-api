from enum import Enum
from typing import List, Tuple


class PaymentCategory(Enum):
    ABSTRACT = "Abstract"
    JOIN_REQUEST = "Join Request"
    
    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(c.value, c.value) for c in cls]
    
    @classmethod
    def default(cls) -> str:
        return cls.ABSTRACT.value
    
    @classmethod
    def values(cls) -> List[str]:
        return [s.value for s in cls]
    
    @classmethod
    def validate(cls, category: str) -> bool:
        return category in {s.value for s in cls}