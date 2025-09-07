import logging
import uuid
from django.core.signing import TimestampSigner
from user.models import User

signer = TimestampSigner()

logger = logging.getLogger(__name__)

def generate_token(user: User) -> str:
    """
    Generate a time-limited token for the user.

    Args:
        user (User): User instance.

    Returns:
        str: Signed token with user UUID.

    Raises:
        Exception: If token generation fails.
    """
    try:
        return signer.sign(str(user.user_id))
    except Exception as e:
        logger.error(f"Error generating token for user {user.email}: {e}")
        raise


def verify_token(token: str, max_age=3600) -> uuid.UUID:
    """Verify the token and return the user UUID.

    Args:
        token (str): Token to verify.
        max_age (int, optional): Expiration time in seconds. Defaults to 1 hour.

    Returns:
        uuid.UUID: Valid user UUID.

    Raises:
        SignatureExpired: If the token has expired.
        BadSignature: If the token is invalid or tampered with.
    """
    user_id = signer.unsign(token, max_age=max_age)
    return uuid.UUID(user_id)
