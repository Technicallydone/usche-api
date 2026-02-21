from abc import ABC, abstractmethod
from typing import List

class BaseEmailProvider(ABC):
    """
    Base class for any email provider.
    """

    @abstractmethod
    def send(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        html_message: str | None = None
    ) -> None:
        """
        Send an email.
        """
        raise NotImplementedError()
