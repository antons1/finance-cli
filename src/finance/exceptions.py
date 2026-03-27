"""Exception hierarchy for the finance CLI."""


class FinanceError(Exception):
    """Base exception for all finance CLI errors."""


class AuthError(FinanceError):
    """Authentication or authorization failure."""


class TokenExpiredError(AuthError):
    """Access and refresh tokens are both expired. Re-login required."""


class RateLimitError(FinanceError):
    """API rate limit exceeded."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after is not None:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg)


class ApiError(FinanceError):
    """API returned an error response."""

    def __init__(self, status_code: int, body: dict | str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"API error {status_code}: {body}")
