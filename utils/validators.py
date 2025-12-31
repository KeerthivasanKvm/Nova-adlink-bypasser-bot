"""
Input Validators
Validation functions for user inputs
"""

import re
from typing import Tuple, Optional
from urllib.parse import urlparse
import validators as v


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL format and structure
    
    Args:
        url: URL string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty"
    
    url = url.strip()
    
    # Check if it's a valid URL
    if not v.url(url):
        return False, "Invalid URL format"
    
    # Check if scheme is http or https
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        return False, "URL must start with http:// or https://"
    
    # Check if domain exists
    if not parsed.netloc:
        return False, "URL must have a valid domain"
    
    # Check URL length
    if len(url) > 2048:
        return False, "URL is too long (max 2048 characters)"
    
    return True, None


def validate_token(token: str) -> Tuple[bool, Optional[str]]:
    """
    Validate access token format
    
    Args:
        token: Token string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not token or not isinstance(token, str):
        return False, "Token cannot be empty"
    
    token = token.strip()
    
    # Check length
    if len(token) < 16:
        return False, "Token is too short"
    
    if len(token) > 64:
        return False, "Token is too long"
    
    # Check if token contains only alphanumeric characters
    if not re.match(r'^[A-Za-z0-9_-]+$', token):
        return False, "Token contains invalid characters"
    
    return True, None


def validate_duration(duration_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate duration string format
    
    Args:
        duration_str: Duration string (e.g., '1h', '7d', '1m', '1y')
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not duration_str or not isinstance(duration_str, str):
        return False, "Duration cannot be empty"
    
    duration_str = duration_str.lower().strip()
    
    # Check format
    if not re.match(r'^\d+[hdmy]$', duration_str):
        return False, "Invalid duration format. Use: 1h, 7d, 1m, 1y"
    
    # Extract value
    value = int(re.findall(r'\d+', duration_str)[0])
    unit = duration_str[-1]
    
    # Validate value ranges
    if unit == 'h' and (value < 1 or value > 8760):  # Max 1 year in hours
        return False, "Hours must be between 1 and 8760"
    
    if unit == 'd' and (value < 1 or value > 365):  # Max 1 year in days
        return False, "Days must be between 1 and 365"
    
    if unit == 'm' and (value < 1 or value > 12):  # Max 12 months
        return False, "Months must be between 1 and 12"
    
    if unit == 'y' and (value < 1 or value > 5):  # Max 5 years
        return False, "Years must be between 1 and 5"
    
    return True, None


def validate_domain(domain: str) -> Tuple[bool, Optional[str]]:
    """
    Validate domain name format
    
    Args:
        domain: Domain name to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not domain or not isinstance(domain, str):
        return False, "Domain cannot be empty"
    
    domain = domain.strip().lower()
    
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '')
    domain = domain.replace('www.', '')
    
    # Remove path if present
    domain = domain.split('/')[0]
    
    # Check format
    if not v.domain(domain):
        return False, "Invalid domain format"
    
    # Check length
    if len(domain) > 253:
        return False, "Domain is too long"
    
    return True, None


def validate_telegram_id(user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Validate Telegram user/chat ID
    
    Args:
        user_id: Telegram ID to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(user_id, int):
        return False, "ID must be a number"
    
    # Telegram IDs are positive for users and negative for groups/channels
    # Valid range is approximately -10^15 to 10^15
    if abs(user_id) > 10**15:
        return False, "Invalid Telegram ID"
    
    if user_id == 0:
        return False, "ID cannot be zero"
    
    return True, None


def validate_limit(limit: int) -> Tuple[bool, Optional[str]]:
    """
    Validate bypass limit value
    
    Args:
        limit: Limit value to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(limit, int):
        return False, "Limit must be a number"
    
    if limit < 1:
        return False, "Limit must be at least 1"
    
    if limit > 10000:
        return False, "Limit is too high (max 10000)"
    
    return True, None


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input text
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '{', '}']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()
