"""
Utility functions for the sample project.
Demonstrates various Python patterns for AST analysis.
"""

import re
import json
from typing import Dict, List, Any, Union, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from abc import ABC, abstractmethod

# Global constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def timer(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.

    Args:
        func: Function to time

    Returns:
        Wrapped function that prints execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"{func.__name__} took {duration:.4f} seconds")
        return result
    return wrapper

def retry(max_attempts: int = MAX_RETRIES, delay: float = 1.0):
    """
    Decorator for retrying failed function calls.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    continue

            raise last_exception
        return wrapper
    return decorator

class BaseValidator(ABC):
    """Abstract base class for validators."""

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate a value."""
        pass

    @abstractmethod
    def get_error_message(self) -> str:
        """Get validation error message."""
        pass

class EmailValidator(BaseValidator):
    """Validator for email addresses."""

    def validate(self, email: str) -> bool:
        """
        Validate email format using regex.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(email, str):
            return False
        return bool(EMAIL_PATTERN.match(email))

    def get_error_message(self) -> str:
        """Get error message for invalid email."""
        return "Invalid email format"

class LengthValidator(BaseValidator):
    """Validator for string length."""

    def __init__(self, min_length: int = 0, max_length: int = 255):
        """
        Initialize length validator.

        Args:
            min_length: Minimum required length
            max_length: Maximum allowed length
        """
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: str) -> bool:
        """
        Validate string length.

        Args:
            value: String to validate

        Returns:
            True if length is within bounds
        """
        if not isinstance(value, str):
            return False
        return self.min_length <= len(value) <= self.max_length

    def get_error_message(self) -> str:
        """Get error message for invalid length."""
        return f"Length must be between {self.min_length} and {self.max_length}"

class DataProcessor:
    """Utility class for data processing operations."""

    def __init__(self, validators: List[BaseValidator] = None):
        """
        Initialize data processor.

        Args:
            validators: List of validators to use
        """
        self.validators = validators or []
        self._cache = {}

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data using configured validators.

        Args:
            data: Data dictionary to validate

        Returns:
            Validation results

        Raises:
            ValidationError: If validation fails
        """
        results = {"valid": True, "errors": []}

        for key, value in data.items():
            for validator in self.validators:
                if not validator.validate(value):
                    results["valid"] = False
                    results["errors"].append({
                        "field": key,
                        "error": validator.get_error_message()
                    })

        if not results["valid"]:
            raise ValidationError(f"Validation failed: {results['errors']}")

        return results

    @timer
    def process_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of items with validation.

        Args:
            items: List of items to process

        Returns:
            List of processed items

        Raises:
            ValidationError: If any item fails validation
        """
        processed_items = []

        for i, item in enumerate(items):
            try:
                # Validate item
                self.validate_data(item)

                # Process item (add metadata)
                processed_item = {
                    **item,
                    "processed_at": datetime.now().isoformat(),
                    "batch_index": i
                }

                processed_items.append(processed_item)

            except ValidationError as e:
                raise ValidationError(f"Item {i} failed validation: {e}")

        return processed_items

    def cache_result(self, key: str, value: Any) -> None:
        """Cache a result for later retrieval."""
        self._cache[key] = {
            "value": value,
            "cached_at": datetime.now()
        }

    def get_cached_result(self, key: str, max_age_seconds: int = 300) -> Optional[Any]:
        """
        Get cached result if still valid.

        Args:
            key: Cache key
            max_age_seconds: Maximum age of cached data in seconds

        Returns:
            Cached value if valid, None otherwise
        """
        if key not in self._cache:
            return None

        cached_item = self._cache[key]
        age = (datetime.now() - cached_item["cached_at"]).total_seconds()

        if age > max_age_seconds:
            del self._cache[key]
            return None

        return cached_item["value"]

# Utility functions
def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object as string.

    Args:
        dt: Datetime object to format
        format_string: Format string

    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_string)

def parse_json_safe(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string.

    Args:
        json_string: JSON string to parse

    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return None

def calculate_percentage(value: float, total: float, precision: int = 2) -> float:
    """
    Calculate percentage with specified precision.

    Args:
        value: Value to calculate percentage for
        total: Total value
        precision: Number of decimal places

    Returns:
        Percentage value

    Raises:
        ValueError: If total is zero
    """
    if total == 0:
        raise ValueError("Total cannot be zero")

    percentage = (value / total) * 100
    return round(percentage, precision)

def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate URL-friendly slug from text.

    Args:
        text: Text to convert to slug
        max_length: Maximum length of slug

    Returns:
        URL-friendly slug
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)

    # Trim to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')

    return slug

# Module-level variables for configuration
_config = {
    "debug_mode": False,
    "log_level": "INFO",
    "database_url": None
}

def set_config(key: str, value: Any) -> None:
    """Set configuration value."""
    global _config
    _config[key] = value

def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    return _config.get(key, default)