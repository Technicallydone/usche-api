from enum import Enum
from typing import List, Tuple

class SPEAKER_CATEGORY(Enum):
    KEYNOTE = "Keynote Speakers"
    PLENARY = "Plenary Speakers"
    BREAKOUT = "Breakout Speakers"
    
    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(s.value, s.value) for s in cls]
    
    @classmethod
    def default(cls) -> str:
        return cls.BREAKOUT.value
    
    @classmethod
    def validate(cls, value: str):
        return value in {s.value for s in cls}
    

from enum import Enum
from typing import List, Tuple

class SPEAKER_TITLE(Enum):
    DR = "Dr."
    PROF = "Prof."
    MR = "Mr."
    MS = "Ms."
    MRS = "Mrs."
    ENG = "Eng."
    ARCH = "Arch."
    
    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(s.value, s.value) for s in cls]
    
    @classmethod
    def default(cls) -> str:
        return cls.DR.value
    
    @classmethod
    def validate(cls, value: str):
        return value in {s.value for s in cls}
