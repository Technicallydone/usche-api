from enum import Enum
from typing import List, Tuple

class TITLE_ENUM(Enum):
    MR = "Mr"
    MRS = "Mrs"
    MS = "Ms"
    DR = "Dr"
    PROF = "Prof"
    ENG = "Eng"
    HON = "Hon"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(t.value, t.value) for t in cls]
    
    @classmethod
    def default(cls) -> str:
        return cls.MR.value
    
    @classmethod
    def validate(cls, value) -> bool:
        return value in {t.value for t in cls}