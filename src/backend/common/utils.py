"""
Utility functions used throughout the application.
"""

import hashlib
import json
import random
import re
import string
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from src.backend.common.constants import ID_PREFIXES


T = TypeVar("T")


def generate_id(entity_type: str, length: int = 16) -> str:
    """
    Generate a unique ID for an entity.

    Args:
        entity_type: Type of entity (e.g., 'pipeline', 'task')
        length: Length of the random part

    Returns:
        Unique ID string
    """
    prefix = ID_PREFIXES.get(entity_type, "obj")
    random_part = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}-{random_part}"


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_short_uuid(length: int = 8) -> str:
    """
    Generate a short UUID.

    Args:
        length: Length of the UUID

    Returns:
        Short UUID string
    """
    full_uuid = uuid.uuid4().hex
    return full_uuid[:length]


def format_datetime(
    dt: Optional[datetime] = None, format_str: str = "%Y-%m-%dT%H:%M:%S.%fZ"
) -> str:
    """
    Format a datetime object to string.

    Args:
        dt: Datetime object (defaults to now)
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> Optional[datetime]:
    """
    Parse a datetime string to datetime object.

    Args:
        dt_str: Datetime string
        format_str: Format string

    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError, TypeError:
        return None


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def sanitize_string(s: str, max_length: Optional[int] = None, allow_newlines: bool = False) -> str:
    """
    Sanitize a string by removing or replacing special characters.

    Args:
        s: Input string
        max_length: Maximum length (truncates if exceeded)
        allow_newlines: Whether to keep newlines

    Returns:
        Sanitized string
    """
    if not s:
        return ""

    # Remove control characters except newlines (if allowed)
    if allow_newlines:
        sanitized = "".join(
            char for char in s if char == "\n" or (ord(char) >= 32 and ord(char) != 127)
        )
    else:
        sanitized = "".join(char for char in s if ord(char) >= 32 and ord(char) != 127)

    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        s: Input string
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s

    return s[: max_length - len(suffix)] + suffix


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of a specified size.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        retryable_exceptions: Exceptions to retry on

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    delay = base_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                time.sleep(delay)
                delay = min(delay * exponential_base, max_delay)

    raise last_exception


def compute_hash(data: Union[str, bytes, Dict[str, Any]], algorithm: str = "sha256") -> str:
    """
    Compute hash of data.

    Args:
        data: Data to hash (string, bytes, or dict)
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)

    Returns:
        Hex digest of hash
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, separators=(",", ":"))

    if isinstance(data, str):
        data = data.encode("utf-8")

    hash_func = getattr(hashlib, algorithm, hashlib.sha256)
    return hash_func(data).hexdigest()


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    Mask sensitive data in a dictionary.

    Args:
        data: Dictionary to mask
        sensitive_keys: List of keys to mask (defaults to common sensitive keys)

    Returns:
        Dictionary with sensitive data masked
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "password",
            "secret",
            "token",
            "api_key",
            "apikey",
            "private_key",
            "credential",
            "auth",
        ]

    result = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sk in key_lower for sk in sensitive_keys):
            result[key] = "***MASKED***"
        elif isinstance(value, dict):
            result[key] = mask_sensitive_data(value, sensitive_keys)
        else:
            result[key] = value

    return result


def parse_size(size_str: str) -> int:
    """
    Parse a size string to bytes.

    Args:
        size_str: Size string (e.g., "1G", "512M", "10K")

    Returns:
        Size in bytes

    Raises:
        ValueError: If size string is invalid
    """
    units = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024**2,
        "MB": 1024**2,
        "G": 1024**3,
        "GB": 1024**3,
        "T": 1024**4,
        "TB": 1024**4,
    }

    size_str = size_str.strip().upper()

    for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(unit):
            number = size_str[: -len(unit)]
            try:
                return int(float(number) * multiplier)
            except ValueError:
                raise ValueError(f"Invalid size: {size_str}")

    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"Invalid size: {size_str}")


def format_size(size_bytes: int, precision: int = 2) -> str:
    """
    Format bytes to human-readable string.

    Args:
        size_bytes: Size in bytes
        precision: Decimal precision

    Returns:
        Human-readable size string
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.{precision}f} {units[unit_index]}"


def parse_duration(duration_str: str) -> int:
    """
    Parse a duration string to seconds.

    Args:
        duration_str: Duration string (e.g., "1h", "30m", "60s")

    Returns:
        Duration in seconds

    Raises:
        ValueError: If duration string is invalid
    """
    units = {
        "S": 1,
        "SECOND": 1,
        "SECONDS": 1,
        "M": 60,
        "MIN": 60,
        "MINUTE": 60,
        "MINUTES": 60,
        "H": 3600,
        "HR": 3600,
        "HOUR": 3600,
        "HOURS": 3600,
        "D": 86400,
        "DAY": 86400,
        "DAYS": 86400,
        "W": 604800,
        "WEEK": 604800,
        "WEEKS": 604800,
    }

    duration_str = duration_str.strip().upper()

    for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
        if duration_str.endswith(unit):
            number = duration_str[: -len(unit)]
            try:
                return int(float(number) * multiplier)
            except ValueError:
                raise ValueError(f"Invalid duration: {duration_str}")

    try:
        return int(duration_str)
    except ValueError:
        raise ValueError(f"Invalid duration: {duration_str}")


def format_duration(seconds: int, precision: str = "seconds") -> str:
    """
    Format seconds to human-readable duration string.

    Args:
        seconds: Duration in seconds
        precision: Precision level ("seconds", "minutes", "hours", "days")

    Returns:
        Human-readable duration string
    """
    if seconds < 0:
        return "0s"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []

    if days > 0 and precision in ("seconds", "minutes", "hours", "days"):
        parts.append(f"{days}d")
    if hours > 0 and precision in ("seconds", "minutes", "hours"):
        parts.append(f"{hours}h")
    if minutes > 0 and precision in ("seconds", "minutes"):
        parts.append(f"{minutes}m")
    if secs > 0 and precision in ("seconds",):
        parts.append(f"{secs}s")

    if not parts:
        return "0s"

    return " ".join(parts)
