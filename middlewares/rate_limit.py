"""
Rate Limiting Middleware
Control bypass limits for free and premium users
"""

import logging
from datetime import datetime, date
from typing import Tuple
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import db

logger = logging.getLogger(__name__)


async def check_rate_limit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_data: dict
) -> Tuple[bool, str]:
    """
    Check if user can perform bypass (rate limit check)
    
    Args:
        update: Telegram update
        context: Bot context
        user_data: User data from database
    
    Returns:
        (can_bypass, message)
    """
    user_id = user_data['user_id']
    
    try:
        # Admins have unlimited access
        if Config.is_admin(user_id):
            return True, "Admin - Unlimited"
        
        # Check if premium user
        is_premium = user_data.get('is_premium', False)
        premium_until = user_data.get('premium_until')
        
        # Check premium expiry
        if is_premium and premium_until:
            if isinstance(premium_until, str):
                from datetime import datetime
                premium_until = datetime.fromisoformat(premium_until)
            
            if datetime.utcnow() > premium_until:
                # Premium expired
                db.update_user(user_id, {'is_premium': False})
                is_premium = False
                
                await update.message.reply_text(
                    "⏰ **Premium Expired**\n\n"
                    "Your premium subscription has expired.\n"
                    "You are now on the free plan.",
                    parse_mode='Markdown'
                )
        
        # Premium users have unlimited access
        if is_premium:
            return True, "Premium - Unlimited"
        
        # Free users - check daily limit
        daily_count = user_data.get('daily_bypass_count', 0)
        daily_limit = Config.FREE_USER_DAILY_LIMIT
        
        # Check if we need to reset daily counter
        last_reset = user_data.get('last_reset_date')
        today = date.today().isoformat()
        
        if last_reset != today:
            # Reset daily counter
            db.update_user(user_id, {
                'daily_bypass_count': 0,
                'last_reset_date': today
            })
            daily_count = 0
        
        # Check if limit reached
        if daily_count >= daily_limit:
            remaining_time = _get_time_until_reset()
            
            message = (
                f"⛔ **Daily Limit Reached**\n\n"
                f"You've used all {daily_limit} bypasses for today.\n\n"
                f"**Options:**\n"
                f"• Wait {remaining_time} for reset\n"
                f"• Use /refer to invite friends\n"
                f"• Upgrade to /premium (unlimited)\n"
                f"• Contact admin for reset key"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return False, "Limit reached"
        
        # User can bypass
        remaining = daily_limit - daily_count
        return True, f"Free - {remaining} remaining today"
        
    except Exception as e:
        logger.error(f"❌ Error checking rate limit: {e}")
        return True, "Error - Allowed"  # Allow on error


def _get_time_until_reset() -> str:
    """Calculate time until daily reset (midnight UTC)"""
    now = datetime.utcnow()
    midnight = datetime.combine(now.date(), datetime.min.time())
    
    # Next midnight
    from datetime import timedelta
    next_midnight = midnight + timedelta(days=1)
    
    time_left = next_midnight - now
    hours = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)
    
    return f"{hours}h {minutes}m"


async def reset_user_limit(user_id: int, reset_key: str) -> Tuple[bool, str]:
    """
    Reset user's daily limit using reset key
    
    Args:
        user_id: User ID to reset
        reset_key: Universal reset key
    
    Returns:
        (success, message)
    """
    try:
        # Verify reset key
        key_data = db.get_reset_key(reset_key)
        
        if not key_data:
            return False, "❌ Invalid reset key"
        
        if not key_data.get('is_active', False):
            return False, "❌ This reset key has been deactivated"
        
        # Reset user's daily count
        today = date.today().isoformat()
        db.update_user(user_id, {
            'daily_bypass_count': 0,
            'last_reset_date': today
        })
        
        # Increment key usage
        db.use_reset_key(reset_key)
        
        logger.info(f"✅ Reset limit for user {user_id} using key {reset_key}")
        
        return True, (
            f"✅ **Limit Reset Successful**\n\n"
            f"Your daily limit has been reset!\n"
            f"You now have {Config.FREE_USER_DAILY_LIMIT} bypasses available."
        )
        
    except Exception as e:
        logger.error(f"❌ Error resetting user limit: {e}")
        return False, "❌ An error occurred. Please try again."


async def redeem_access_token(user_id: int, token: str) -> Tuple[bool, str]:
    """
    Redeem premium access token
    
    Args:
        user_id: User ID
        token: Access token
    
    Returns:
        (success, message)
    """
    try:
        # Get token data
        token_data = db.get_token(token)
        
        if not token_data:
            return False, "❌ Invalid access token"
        
        # Check if already used
        if token_data.get('is_used', False):
            return False, "❌ This token has already been used"
        
        # Check expiry
        expires_at = token_data.get('expires_at')
        if isinstance(expires_at, str):
            from datetime import datetime
            expires_at = datetime.fromisoformat(expires_at)
        
        if datetime.utcnow() > expires_at:
            return False, "❌ This token has expired"
        
        # Mark token as used
        success = db.use_token(token, user_id)
        if not success:
            return False, "❌ Failed to redeem token. It may have been used already."
        
        # Calculate premium end date
        duration_type = token_data.get('duration_type')
        duration_value = token_data.get('duration_value')
        
        from datetime import timedelta
        duration_map = {
            'hours': timedelta(hours=duration_value),
            'days': timedelta(days=duration_value),
            'months': timedelta(days=duration_value * 30),
            'years': timedelta(days=duration_value * 365)
        }
        
        premium_until = datetime.utcnow() + duration_map.get(duration_type, timedelta(days=30))
        
        # Update user to premium
        db.update_user(user_id, {
            'is_premium': True,
            'premium_until': premium_until,
            'premium_activated_at': datetime.utcnow()
        })
        
        logger.info(f"✅ User {user_id} redeemed token {token}")
        
        # Format duration
        from utils import format_duration
        duration_str = format_duration(duration_type, duration_value)
        
        return True, (
            f"🎉 **Premium Activated!**\n\n"
            f"✅ Duration: {duration_str}\n"
            f"📅 Expires: {premium_until.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"You now have:\n"
            f"• ♾️ Unlimited bypasses\n"
            f"• ⚡ Priority processing\n"
            f"• 🎯 Advanced AI methods\n"
            f"• 🔔 Expiry notifications\n\n"
            f"Use /premium to check your status!"
        )
        
    except Exception as e:
        logger.error(f"❌ Error redeeming token: {e}")
        return False, "❌ An error occurred. Please try again."
