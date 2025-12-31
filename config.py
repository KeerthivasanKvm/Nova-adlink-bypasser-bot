"""
Configuration Module
Handles all environment variables and configuration settings
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)


class Config:
    """Main configuration class"""
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    API_ID: int = int(os.getenv('API_ID', '0'))
    API_HASH: str = os.getenv('API_HASH', '')
    BOT_USERNAME: str = os.getenv('BOT_USERNAME', '')
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS: str = os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json')
    FIREBASE_PROJECT_ID: str = os.getenv('FIREBASE_PROJECT_ID', '')
    
    # Collections
    USERS_COLLECTION = 'users'
    TOKENS_COLLECTION = 'access_tokens'
    CACHE_COLLECTION = 'bypass_cache'
    SITES_COLLECTION = 'supported_sites'
    GROUPS_COLLECTION = 'allowed_groups'
    REFERRALS_COLLECTION = 'referrals'
    STATS_COLLECTION = 'statistics'
    
    # Admin Configuration
    OWNER_ID: int = int(os.getenv('OWNER_ID', '0'))
    ADMIN_IDS: List[int] = [
        int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') 
        if x.strip().isdigit()
    ]
    
    # Flask Configuration
    FLASK_SECRET_KEY: str = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    PORT: int = int(os.getenv('PORT', '8080'))
    HOST: str = os.getenv('HOST', '0.0.0.0')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Webhook Configuration
    WEBHOOK_MODE: bool = os.getenv('WEBHOOK_MODE', 'False').lower() == 'true'
    WEBHOOK_URL: Optional[str] = os.getenv('WEBHOOK_URL')
    WEBHOOK_PATH: str = f"/webhook/{BOT_TOKEN}"
    
    # Force Subscribe
    FORCE_SUB_ENABLED: bool = os.getenv('FORCE_SUB_ENABLED', 'False').lower() == 'true'
    FORCE_SUB_CHANNEL: Optional[int] = (
        int(os.getenv('FORCE_SUB_CHANNEL')) 
        if os.getenv('FORCE_SUB_CHANNEL') else None
    )
    FORCE_SUB_GROUP: Optional[int] = (
        int(os.getenv('FORCE_SUB_GROUP')) 
        if os.getenv('FORCE_SUB_GROUP') else None
    )
    
    # User Limits
    FREE_USER_DAILY_LIMIT: int = int(os.getenv('FREE_USER_DAILY_LIMIT', '10'))
    FREE_USER_MONTHLY_LIMIT: int = int(os.getenv('FREE_USER_MONTHLY_LIMIT', '100'))
    PREMIUM_DAILY_LIMIT: int = -1  # Unlimited
    
    # Referral System
    REFERRAL_ENABLED: bool = os.getenv('REFERRAL_ENABLED', 'True').lower() == 'true'
    REFERRAL_REWARD_BYPASSES: int = int(os.getenv('REFERRAL_REWARD_BYPASSES', '5'))
    MIN_REFERRALS_FOR_REWARD: int = int(os.getenv('MIN_REFERRALS_FOR_REWARD', '3'))
    
    # Premium Configuration
    PREMIUM_NOTIFICATION_DAYS: int = int(os.getenv('PREMIUM_NOTIFICATION_DAYS', '3'))
    
    # Rate Limiting
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '60'))
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    CLOUDFLARE_TIMEOUT: int = int(os.getenv('CLOUDFLARE_TIMEOUT', '30'))
    
    # Browser Configuration
    HEADLESS_BROWSER: bool = os.getenv('HEADLESS_BROWSER', 'True').lower() == 'true'
    BROWSER_TIMEOUT: int = int(os.getenv('BROWSER_TIMEOUT', '45'))
    
    # Cache Settings
    CACHE_EXPIRY_HOURS: int = int(os.getenv('CACHE_EXPIRY_HOURS', '24'))
    ENABLE_CACHE: bool = True
    
    # Notification Settings
    NOTIFY_ADMIN_ERRORS: bool = os.getenv('NOTIFY_ADMIN_ERRORS', 'True').lower() == 'true'
    ERROR_CHANNEL_ID: Optional[int] = (
        int(os.getenv('ERROR_CHANNEL_ID')) 
        if os.getenv('ERROR_CHANNEL_ID') else None
    )
    
    # Bypass Methods Configuration
    BYPASS_METHODS = [
        'html_form',
        'css_hidden',
        'javascript',
        'countdown_timer',
        'dynamic_content',
        'cloudflare',
        'redirect_chain',
        'base64_decode',
        'url_decode',
        'browser_automation'
    ]
    
    # Supported Domains (Initial list)
    DEFAULT_SUPPORTED_DOMAINS = [
        'gplinks.co',
        'gplinks.in',
        'short.st',
        'ouo.io',
        'ouo.press',
        'terabox.com',
        'teraboxapp.com',
        '1024tera.com',
        'freeterabox.com',
        'gdtot.pro',
        'gdtot.dad',
        'appdrive.me',
        'drivehub.ws',
        'driveapp.in',
        'mediafire.com',
        'droplink.co',
        'exe.io',
        'linkvertise.com',
        'work.ink',
        'shrinkme.io',
        'bc.vc',
        'adfly.com',
        'adf.ly',
        'bit.ly',
        'tinyurl.com',
        'cutt.ly',
        'shorte.st'
    ]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_fields = {
            'BOT_TOKEN': cls.BOT_TOKEN,
            'API_ID': cls.API_ID,
            'API_HASH': cls.API_HASH,
            'FIREBASE_PROJECT_ID': cls.FIREBASE_PROJECT_ID,
            'OWNER_ID': cls.OWNER_ID
        }
        
        missing = [key for key, value in required_fields.items() if not value]
        
        if missing:
            logger.error(f"❌ Missing required configuration: {', '.join(missing)}")
            logger.error("Please check your .env file or environment variables")
            return False
        
        # Validate webhook configuration
        if cls.WEBHOOK_MODE and not cls.WEBHOOK_URL:
            logger.error("❌ WEBHOOK_MODE is enabled but WEBHOOK_URL is not set")
            return False
        
        logger.info("✅ Configuration validated successfully")
        return True
    
    @classmethod
    def get_firebase_config(cls) -> dict:
        """Get Firebase configuration"""
        return {
            'credentials_path': cls.FIREBASE_CREDENTIALS,
            'project_id': cls.FIREBASE_PROJECT_ID
        }
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == cls.OWNER_ID or user_id in cls.ADMIN_IDS
    
    @classmethod
    def get_webhook_url(cls) -> Optional[str]:
        """Get full webhook URL"""
        if cls.WEBHOOK_MODE and cls.WEBHOOK_URL:
            return f"{cls.WEBHOOK_URL}{cls.WEBHOOK_PATH}"
        return None


# Validate configuration on import
if not Config.validate():
    raise ValueError("❌ Invalid configuration. Please check your environment variables.")

# Export config instance
config = Config()
