"""
This module contains the exceptions raised by the Multilspy framework.
"""


class LanguageServerException(Exception):
    """
    Exceptions raised by the Multilspy framework.
    """

    def __init__(self, message: str):
        """
        Initializes the exception with the given message.
        """
        super().__init__(message)
