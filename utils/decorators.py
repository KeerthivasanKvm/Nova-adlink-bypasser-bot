"""
Custom Decorators
Function decorators for authorization, rate limiting, and logging
"""

import functools
import logging
from datetime import datetime
from typing import Callable
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import db

logger = logging.getLogger(__name__)


def admin_only(func: Callable) -> Callable:
    """
    Decorator to restrict command to admins only
    
    Usage:
        @admin_only
        async def my_command(update, context):
            ...
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if not Config.is_admin(user_id):
            await update.message.reply_text(
                "⛔ **Access Denied**\n\n"
                "This command is only available to administrators.",
                parse_mode='Markdown'
            )
            logger.warning(f"Unauthorized admin command attempt by user {user_id}")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def group_only(func: Callable) -> Callable:
    """
    Decorator to restrict command to groups only
    
    Usage:
        @group_only
        async def my_command(update, context):
            ...
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat_type = update.effective_chat.type
        
        if chat_type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "⛔ **Group Only Command**\n\n"
                "This command can only be used in groups.",
                parse_mode='Markdown'
            )
            return
        
        # Check if group is allowed
        group_id = update.effective_chat.id
        allowed_group = db.db.get_collection(Config.GROUPS_COLLECTION).find_one(
            {'group_id': group_id, 'is_active': True}
        )
        
        # Admins can use in any group
        user_id = update.effective_user.id
        if not allowed_group and not Config.is_admin(user_id):
            await update.message.reply_text(
                "⛔ **Unauthorized Group**\n\n"
                "This bot is not authorized to work in this group.\n"
                "Please contact an administrator.",
                parse_mode='Markdown'
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def rate_limit(max_calls: int = 5, period: int = 60):
    """
    Decorator to rate limit function calls per user
    
    Args:
        max_calls: Maximum calls allowed
        period: Time period in seconds
    
    Usage:
        @rate_limit(max_calls=5, period=60)
        async def my_command(update, context):
            ...
    """
    def decorator(func: Callable) -> Callable:
        user_calls = {}
        
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            current_time = datetime.utcnow().timestamp()
            
            # Initialize user's call history
            if user_id not in user_calls:
                user_calls[user_id] = []
            
            # Remove old calls outside the period
            user_calls[user_id] = [
                call_time for call_time in user_calls[user_id]
                if current_time - call_time < period
            ]
            
            # Check if rate limit exceeded
            if len(user_calls[user_id]) >= max_calls:
                remaining_time = int(period - (current_time - user_calls[user_id][0]))
                await update.message.reply_text(
                    f"⏱️ **Rate Limit Exceeded**\n\n"
                    f"Please wait {remaining_time} seconds before trying again.",
                    parse_mode='Markdown'
                )
                return
            
            # Add current call
            user_calls[user_id].append(current_time)
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    return decorator


def log_action(action_name: str):
    """
    Decorator to log user actions
    
    Args:
        action_name: Name of the action being logged
    
    Usage:
        @log_action("bypass_link")
        async def bypass_command(update, context):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            chat = update.effective_chat
            
            logger.info(
                f"Action: {action_name} | "
                f"User: {user.id} (@{user.username}) | "
                f"Chat: {chat.id} ({chat.type})"
            )
            
            try:
                result = await func(update, context, *args, **kwargs)
                logger.info(f"Action: {action_name} | User: {user.id} | Status: Success")
                return result
            except Exception as e:
                logger.error(f"Action: {action_name} | User: {user.id} | Error: {e}")
                raise
        
        return wrapper
    
    return decorator


def check_ban(func: Callable) -> Callable:
    """
    Decorator to check if user is banned
    
    Usage:
        @check_ban
        async def my_command(update, context):
            ...
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Admins can't be banned
        if Config.is_admin(user_id):
            return await func(update, context, *args, **kwargs)
        
        # Check if user is banned
        user_data = db.get_user(user_id)
        if user_data and user_data.get('is_banned', False):
            await update.message.reply_text(
                "🚫 **You are banned**\n\n"
                "You have been banned from using this bot.\n"
                "Contact an administrator if you think this is a mistake.",
                parse_mode='Markdown'
            )
            logger.warning(f"Banned user {user_id} attempted to use bot")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def require_premium(func: Callable) -> Callable:
    """
    Decorator to restrict command to premium users only
    
    Usage:
        @require_premium
        async def premium_command(update, context):
            ...
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Admins bypass premium check
        if Config.is_admin(user_id):
            return await func(update, context, *args, **kwargs)
        
        # Check premium status
        user_data = db.get_user(user_id)
        if not user_data:
            await update.message.reply_text(
                "❌ Please use /start first to register.",
                parse_mode='Markdown'
            )
            return
        
        is_premium = user_data.get('is_premium', False)
        premium_until = user_data.get('premium_until')
        
        # Check if premium is active
        if not is_premium:
            await update.message.reply_text(
                "💎 **Premium Feature**\n\n"
                "This feature is only available for premium users.\n"
                "Use /premium to upgrade your account.",
                parse_mode='Markdown'
            )
            return
        
        # Check if premium expired
        if premium_until and datetime.utcnow() > premium_until:
            await update.message.reply_text(
                "⏰ **Premium Expired**\n\n"
                "Your premium subscription has expired.\n"
                "Use /premium to renew your account.",
                parse_mode='Markdown'
            )
            
            # Update user status
            db.update_user(user_id, {'is_premium': False})
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def error_handler(func: Callable) -> Callable:
    """
    Decorator to handle errors gracefully
    
    Usage:
        @error_handler
        async def my_command(update, context):
            ...
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            try:
                await update.message.reply_text(
                    "❌ **An error occurred**\n\n"
                    "Please try again later or contact support.",
                    parse_mode='Markdown'
                )
            except Exception:
                pass  # Fail silently if we can't send error message
    
    return wrapper
