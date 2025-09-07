from enum import Enum
from typing import List, Tuple

class SessionTypeEnum(Enum):
    KEYNOTE = "keynote"
    PLENARY = "plenary"
    BREAKOUT = "breakout"
    POSTER = "poster"
    NETWORKING = "networking"
    ENTERTAINMENT = "entertainment"
    CEREMONY = "ceremony"
    QA = "qa"
    OTHER = "other"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(e.value, e.name.capitalize()) for e in cls]

    @classmethod
    def default(cls) -> str:
        return cls.OTHER.value

    @classmethod
    def validate(cls, value) -> bool:
        return value in {e.value for e in cls}
