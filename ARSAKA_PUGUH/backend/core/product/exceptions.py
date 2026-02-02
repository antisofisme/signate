"""
Product Module Exceptions

Custom exceptions for product operations.
"""


class ProductError(Exception):
    """Base class for product errors."""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


class ProductNotFoundError(ProductError):
    """Raised when product is not found."""
    def __init__(self, product_code: str):
        super().__init__(
            message=f"Product '{product_code}' not found",
            code="PRODUCT_NOT_FOUND"
        )
        self.product_code = product_code


class ProductAccessDeniedError(ProductError):
    """Raised when tenant doesn't have access to a product."""
    def __init__(self, product_code: str, reason: str = None):
        message = f"Access denied to product '{product_code}'"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, code="PRODUCT_ACCESS_DENIED")
        self.product_code = product_code
        self.reason = reason


class ProductSubscriptionExistsError(ProductError):
    """Raised when subscription already exists."""
    def __init__(self, product_code: str):
        super().__init__(
            message=f"Already subscribed to product '{product_code}'",
            code="SUBSCRIPTION_EXISTS"
        )
        self.product_code = product_code


class ProductNotAvailableError(ProductError):
    """Raised when product is not available for subscription."""
    def __init__(self, product_code: str):
        super().__init__(
            message=f"Product '{product_code}' is not available for subscription",
            code="PRODUCT_NOT_AVAILABLE"
        )
        self.product_code = product_code


class UsageLimitExceededError(ProductError):
    """Raised when usage limit is exceeded."""
    def __init__(self, product_code: str, limit: int):
        super().__init__(
            message=f"Usage limit ({limit}) exceeded for product '{product_code}'",
            code="USAGE_LIMIT_EXCEEDED"
        )
        self.product_code = product_code
        self.limit = limit
