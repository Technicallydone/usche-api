"""User roles

    Returns:
        List[Tuple[str, str]]: List of roles in a taple
        str: Default value of Role
        bool: Return True if the role is valid, otherwise False
"""

from enum import Enum
from typing import List, Tuple


class ROLE(Enum):
    """User roles enum

    Args:
        Enum (Role): Role keys

    Returns:
        List[Tuple[str, str]]: List of roles in a taple
        str: Default value of Role
        bool: Return True if the role is valid, otherwise False
    """
    ATTENDEE = "Attendee"
    ORGANIZER = "Organizer"
    ADMIN = "Admin"
    BURSAR = "Bursar"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """Role choices in a tuple of key and values

        Returns:
            List[Tuple[str, str]]: List of tuple containing key and value of role values
        """
        return [(role.value, role.value) for role in cls]

    @classmethod
    def default(cls) -> str:
        """Retrieve default value of role

        Returns:
            str: Default value
        """
        return cls.ATTENDEE.value

    @classmethod
    def validate(cls, role: str) -> bool:
        """Validate role

        Args:
            role (str): Role value

        Returns:
            bool: True if the role is valid, otherwise False
        """
        return role in {r.value for r in cls}
