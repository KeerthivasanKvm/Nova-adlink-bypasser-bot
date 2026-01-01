"""
Utility Functions
All helper functions for the bot
"""

import re
import secrets
import string
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False


def format_datetime(dt: datetime) -> str:
    """
    Format datetime to human-readable string
    
    Args:
        dt: datetime object
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def time_ago(date: datetime) -> str:
    """
    Convert datetime to 'time ago' format
    
    Args:
        date: datetime object
        
    Returns:
        str: Human readable time ago string
    """
    now = datetime.now()
    diff = now - date
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"


def generate_token(length: int = 32) -> str:
    """
    Generate random token/key
    
    Args:
        length: Length of token (default 32)
        
    Returns:
        str: Random token string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_reset_key(length: int = 12) -> str:
    """
    Generate random reset key for admin functions
    
    Args:
        length: Length of key (default 12)
        
    Returns:
        str: Random reset key
    """
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse duration string to seconds
    
    Examples:
        "30s" -> 30
        "5m" -> 300
        "2h" -> 7200
        "1d" -> 86400
    
    Args:
        duration_str: Duration string (e.g., "30s", "5m", "2h", "1d")
        
    Returns:
        int: Duration in seconds, or None if invalid
    """
    try:
        duration_str = duration_str.strip().lower()
        
        # Extract number and unit
        match = re.match(r'^(\d+)([smhd])$', duration_str)
        if not match:
            return None
        
        value = int(match.group(1))
        unit = match.group(2)
        
        # Convert to seconds
        multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        
        return value * multipliers[unit]
    except:
        return None


def format_duration(seconds: int) -> str:
    """
    Format seconds to human-readable duration
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Human readable duration (e.g., "5 minutes", "2 hours")
    """
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 100)
        suffix: Suffix to add if truncated (default "...")
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_number(number: int) -> str:
    """
    Format number with commas (e.g., 1000 -> "1,000")
    
    Args:
        number: Number to format
        
    Returns:
        str: Formatted number string
    """
    return f"{number:,}"


def extract_user_id(text: str) -> Optional[int]:
    """
    Extract user ID from text (for admin commands)
    
    Args:
        text: Text containing user ID
        
    Returns:
        int: User ID if found, None otherwise
    """
    try:
        # Try to find a number in the text
        match = re.search(r'\d+', text)
        if match:
            return int(match.group())
        return None
    except:
        return None


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown
    
    Args:
        text: Text to escape
        
    Returns:
        str: Escaped text
    """
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text


def clean_url(url: str) -> str:
    """
    Clean and normalize URL
    
    Args:
        url: URL to clean
        
    Returns:
        str: Cleaned URL
    """
    url = url.strip()
    # Remove trailing slashes
    url = url.rstrip('/')
    return url


# Export all functions
__all__ = [
    'is_valid_url',
    'format_datetime',
    'time_ago',
    'generate_token',
    'generate_reset_key',
    'parse_duration',
    'format_duration',
    'sanitize_filename',
    'truncate_text',
    'format_number',
    'extract_user_id',
    'escape_markdown',
    'clean_url'
        ]
