class PrivacyEngineError(Exception):
    """Base exception for known application errors."""


class InvalidInputError(PrivacyEngineError):
    """Raised when application input is invalid."""


class DatabaseUnavailableError(PrivacyEngineError):
    """Raised when the database cannot complete an operation."""