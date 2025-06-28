"""
Custom exceptions for DROMA-Py package.
"""

from typing import Optional


class DROMAError(Exception):
    """Base exception class for all DROMA-related errors."""
    
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class DROMAConnectionError(DROMAError):
    """Raised when database connection operations fail."""
    pass


class DROMADataError(DROMAError):
    """Raised when data operations fail (e.g., invalid data format, missing data)."""
    pass


class DROMAValidationError(DROMAError):
    """Raised when input validation fails."""
    pass


class DROMAQueryError(DROMAError):
    """Raised when database queries fail."""
    pass


class DROMATableError(DROMAError):
    """Raised when table operations fail (e.g., table not found, schema mismatch)."""
    pass 