"""
Database Models
Data structures for MongoDB documents
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class User:
    """User model"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_premium: bool = False
    is_banned: bool = False
    premium_until: Optional[datetime] = None
    bypass_count: int = 0
    daily_bypass_count: int = 0
    monthly_bypass_count: int = 0
    referral_code: Optional[str] = None
    referred_by: Optional[int] = None
    referral_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_bypass_at: Optional[datetime] = None
    last_reset_date: str = field(default_factory=lambda: datetime.utcnow().date().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_premium_active(self) -> bool:
        """Check if premium is still active"""
        if not self.is_premium:
            return False
        if self.premium_until is None:
            return True  # Lifetime premium
        return datetime.utcnow() < self.premium_until
    
    def days_until_expiry(self) -> Optional[int]:
        """Get days until premium expires"""
        if not self.premium_until:
            return None
        delta = self.premium_until - datetime.utcnow()
        return max(0, delta.days)
    
    def can_bypass(self, daily_limit: int) -> bool:
        """Check if user can perform bypass"""
        if self.is_banned:
            return False
        if self.is_premium_active():
            return True
        return self.daily_bypass_count < daily_limit
    
    def get_remaining_bypasses(self, daily_limit: int) -> int:
        """Get remaining bypasses for today"""
        if self.is_premium_active():
            return -1  # Unlimited
        return max(0, daily_limit - self.daily_bypass_count)


@dataclass
class AccessToken:
    """Access token model for premium access"""
    token: str
    duration_type: str  # 'hours', 'days', 'months', 'years'
    duration_value: int
    expires_at: datetime
    created_by: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_used: bool = False
    used_by: Optional[int] = None
    used_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        if self.is_used:
            return False
        return datetime.utcnow() < self.expires_at
    
    @staticmethod
    def parse_duration(duration_str: str) -> tuple:
        """
        Parse duration string like '1h', '7d', '1m', '1y'
        Returns (type, value, expires_at)
        """
        duration_str = duration_str.lower().strip()
        
        # Extract number and unit
        value = int(''.join(filter(str.isdigit, duration_str)))
        unit = ''.join(filter(str.isalpha, duration_str))
        
        # Map units
        unit_map = {
            'h': ('hours', timedelta(hours=value)),
            'd': ('days', timedelta(days=value)),
            'm': ('months', timedelta(days=value * 30)),
            'y': ('years', timedelta(days=value * 365))
        }
        
        if unit not in unit_map:
            raise ValueError(f"Invalid duration unit: {unit}")
        
        duration_type, delta = unit_map[unit]
        expires_at = datetime.utcnow() + delta
        
        return duration_type, value, expires_at


@dataclass
class ResetKey:
    """Universal reset key for free users"""
    key: str
    created_by: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class BypassCache:
    """Cached bypass result"""
    original_url: str
    bypassed_url: str
    method_used: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    hit_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Site:
    """Supported site/domain"""
    domain: str
    is_active: bool = True
    added_by: int = 0
    added_at: datetime = field(default_factory=datetime.utcnow)
    bypass_success_rate: float = 0.0
    total_attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Group:
    """Allowed Telegram group"""
    group_id: int
    group_title: Optional[str] = None
    added_by: int = 0
    added_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Referral:
    """Referral record"""
    referrer_id: int
    referred_id: int
    referral_code: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    reward_given: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ErrorReport:
    """User error report"""
    report_id: str
    user_id: int
    link: str
    error_type: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = 'pending'  # pending, reviewed, fixed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class SiteRequest:
    """User site request"""
    request_id: str
    user_id: int
    site_url: str
    site_domain: str
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = 'pending'  # pending, approved, rejected
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Statistics:
    """Bot statistics"""
    date: str
    total_users: int = 0
    premium_users: int = 0
    total_bypasses: int = 0
    successful_bypasses: int = 0
    failed_bypasses: int = 0
    cache_hits: int = 0
    new_users: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
