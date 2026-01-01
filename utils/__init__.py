"""
Utilities Package
Helper functions and decorators
"""

from datetime import datetime

def time_ago(date):
    """Convert datetime to human-readable 'time ago' format"""
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
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"

from .helpers import (
    generate_token,
    generate_referral_code,
    parse_duration,
    format_duration,
    extract_domain,
    is_valid_url,
    format_file_size,
    format_datetime
)
from .validators import validate_url, validate_token, validate_duration
from .decorators import admin_only, group_only, rate_limit, log_action

__all__ = [
    'generate_token',
    'generate_referral_code',
    'parse_duration',
    'format_duration',
    'extract_domain',
    'is_valid_url',
    'format_file_size',
    'format_datetime',
    'validate_url',
    'validate_token',
    'validate_duration',
    'admin_only',
    'group_only',
    'rate_limit',
    'log_action'
]
