class ApartmentsSDKError(Exception):
    """Base SDK error."""


class APIError(ApartmentsSDKError):
    def __init__(self, status_code: int, message: str):
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.message = message


class AuthError(ApartmentsSDKError):
    """Raised when an authenticated call is made without a token."""

