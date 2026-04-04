from enum import Enum

class DefaultAppRolesEnum(Enum):
    Admin = "admin"
    Organizer = "organizer"
    User = "user"
    Bursar = "bursar"
    
    @classmethod
    def default(cls) -> str:
        """Default role for normal users."""
        return cls.User.value

    @classmethod
    def organizer(cls) -> str:
        """Role for organizers."""
        return cls.Organizer.value

    @classmethod
    def bursar(cls) -> str:
        """Role for bursars."""
        return cls.Bursar.value
    
    @classmethod
    def admin(cls) -> str:
        """Role for bursars."""
        return cls.Admin.value