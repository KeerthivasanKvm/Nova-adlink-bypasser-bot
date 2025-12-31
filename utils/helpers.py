"""
Helper Utilities
Common helper functions used across the application
"""

import re
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlparse
import validators


def generate_token(length: int = 32) -> str:
    """
    Generate a secure random token
    
    Args:
        length: Token length (default 32)
    
    Returns:
        Random token string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_referral_code(user_id: int) -> str:
    """
    Generate referral code for user
    
    Args:
        user_id: User's Telegram ID
    
    Returns:
        Referral code
    """
    # Format: REF{user_id}_{random}
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"REF{user_id}_{random_part}"


def parse_duration(duration_str: str) -> Tuple[str, int, datetime]:
    """
    Parse duration string like '1h', '7d', '1m', '1y'
    
    Args:
        duration_str: Duration string (e.g., '1h', '7d', '1m', '1y')
    
    Returns:
        Tuple of (type, value, expiry_datetime)
    
    Raises:
        ValueError: If duration format is invalid
    """
    duration_str = duration_str.lower().strip()
    
    # Extract number and unit
    match = re.match(r'^(\d+)([hdmy])$', duration_str)
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}. Use format like '1h', '7d', '1m', '1y'")
    
    value_str, unit = match.groups()
    value = int(value_str)
    
    # Map units to timedelta
    unit_map = {
        'h': ('hours', timedelta(hours=value)),
        'd': ('days', timedelta(days=value)),
        'm': ('months', timedelta(days=value * 30)),
        'y': ('years', timedelta(days=value * 365))
    }
    
    duration_type, delta = unit_map[unit]
    expires_at = datetime.utcnow() + delta
    
    return duration_type, value, expires_at


def format_duration(duration_type: str, value: int) -> str:
    """
    Format duration for display
    
    Args:
        duration_type: Type (hours, days, months, years)
        value: Duration value
    
    Returns:
        Formatted string
    """
    type_map = {
        'hours': ('hour', 'hours'),
        'days': ('day', 'days'),
        'months': ('month', 'months'),
        'years': ('year', 'years')
    }
    
    singular, plural = type_map.get(duration_type, ('unit', 'units'))
    return f"{value} {singular if value == 1 else plural}"


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL
    
    Args:
        url: Full URL
    
    Returns:
        Domain name or None
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        domain = domain.replace('www.', '')
        return domain.lower()
    except Exception:
        return None


def is_valid_url(url: str) -> bool:
    """
    Check if string is a valid URL
    
    Args:
        url: URL string to validate
    
    Returns:
        True if valid, False otherwise
    """
    return validators.url(url) is True


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_datetime(dt: datetime, format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime object
    
    Args:
        dt: Datetime object
        format: Format string
    
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format)


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time ago string
    
    Args:
        dt: Past datetime
    
    Returns:
        Time ago string (e.g., '2 hours ago')
    """
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} {'day' if days == 1 else 'days'} ago"
    else:
        return dt.strftime('%Y-%m-%d')


def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_user_info(user) -> dict:
    """
    Extract user information from Telegram user object
    
    Args:
        user: Telegram user object
    
    Returns:
        Dictionary with user info
    """
    return {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_bot': user.is_bot,
        'language_code': user.language_code
    }


def generate_reset_key() -> str:
    """
    Generate universal reset key
    
    Returns:
        Reset key string
    """
    # Format: RESET_{timestamp}_{random}
    timestamp = int(datetime.utcnow().timestamp())
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"RESET_{timestamp}_{random_part}"


def format_bypass_stats(stats: dict) -> str:
    """
    Format bypass statistics for display
    
    Args:
        stats: Statistics dictionary
    
    Returns:
        Formatted stats string
    """
    return f"""
📊 **Bypass Statistics**

✅ Successful: {stats.get('successful', 0)}
❌ Failed: {stats.get('failed', 0)}
💾 Cache Hits: {stats.get('cache_hits', 0)}
🔄 Total: {stats.get('total', 0)}
📈 Success Rate: {stats.get('success_rate', 0):.1f}%
"""


def get_greeting() -> str:
    """
    Get time-based greeting
    
    Returns:
        Greeting message
    """
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 21:
        return "Good evening"
    else:
        return "Good night"


def format_user_status(user_data: dict) -> str:
    """
    Format user status message
    
    Args:
        user_data: User data dictionary
    
    Returns:
        Formatted status message
    """
    is_premium = user_data.get('is_premium', False)
    premium_until = user_data.get('premium_until')
    
    if is_premium:
        if premium_until:
            days_left = (premium_until - datetime.utcnow()).days
            return f"💎 Premium (Expires in {days_left} days)"
        else:
            return "💎 Premium (Lifetime)"
    else:
        return "🆓 Free"
