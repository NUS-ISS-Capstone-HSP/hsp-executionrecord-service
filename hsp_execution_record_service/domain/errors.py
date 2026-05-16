class DomainError(Exception):
    """Base domain error."""


class ValidationError(DomainError):
    """Raised when input validation fails."""


class NotFoundError(DomainError):
    """Raised when entity does not exist."""


class ConflictError(DomainError):
    """Raised when an entity is in a conflicting state."""


class ForbiddenError(DomainError):
    """Raised when the actor is not allowed to perform an action."""
