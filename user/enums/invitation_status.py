from enum import Enum


class InvitationStatusEnum(Enum):
    ALL = "all"
    INVITED = "invited"
    NOT_INVITED = "not_invited"
    INVITED_NOT_SENT = "invited_not_sent"
    
    @classmethod
    def choices(cls):
        return [(status.value, status.value) for status in cls]
    
    @classmethod
    def default(cls):
        return cls.ALL.value

    @classmethod
    def validate(cls, value):
        """Validate invitation status."""
        normalized_value = value.lower() if isinstance(value, str) else value
        if normalized_value not in {status.value for status in cls}:
            raise ValueError(f"Invalid invitation status: {value}")
        return normalized_value
