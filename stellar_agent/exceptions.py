"""Custom exceptions for Stellar Agent."""


class StellarAgentError(Exception):
    """Base exception for Stellar Agent."""
    pass


class ConfigurationError(StellarAgentError):
    """Raised when there's a configuration issue."""
    pass


class ValidationError(StellarAgentError):
    """Raised when input validation fails."""
    pass


class InsufficientBalanceError(StellarAgentError):
    """Raised when account has insufficient balance."""
    pass


class AccountNotFoundError(StellarAgentError):
    """Raised when Stellar account is not found."""
    pass


class TransactionError(StellarAgentError):
    """Raised when transaction fails."""
    pass


class NetworkError(StellarAgentError):
    """Raised when network connectivity issues occur."""
    pass
