# enums/question_type_enum.py
from enum import Enum
from typing import List, Tuple


class QuestionTypeEnum(Enum):
    MULTIPLE_CHOICE = "multiple-choice"
    TEXT = "text"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        return [(e.value, e.name.replace("_", " ").title()) for e in cls]

    @classmethod
    def default(cls) -> str:
        return cls.TEXT.value

    @classmethod
    def validate(cls, value) -> bool:
        return value in {e.value for e in cls}
