from enum import Enum
from typing import List, Tuple

class UserRoleActionEnum(str, Enum):
    ASSIGN = "assign"
    UNASSIGN = "unassign"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """
        Returns choices as a list of tuples, e.g.:
        [("assign", "assign"), ("unassign", "unassign")]
        """
        return [(action.value, action.value) for action in cls]
