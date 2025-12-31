"""
Authentication Middleware
Handle user authentication, force subscription, and group permissions
"""

import logging
from typing import Optional, Tuple
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import Config
from database import db
from utils import generate_referral_code

logger = logging.getLogger(__name__)


async def check_user_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> Tuple[bool, Optional[dict]]:
    """
    Check and register user, return status
    
    Returns:
        (is_allowed, user_data)
    """
    user = update.effective_user
    user_id = user.id
    
    try:
        # Get or create user
        user_data = db.get_user(user_id)
        
        if not user_data:
            # Create new user
            referral_code = generate_referral_code(user_id)
            
            new_user = {
                'user_id': user_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_premium': False,
                'is_banned': False,
                'bypass_count': 0,
                'daily_bypass_count': 0,
                'monthly_bypass_count': 0,
                'referral_code': referral_code,
                'referred_by': None,
                'referral_count': 0,
                'created_at': datetime.utcnow()
            }
            
            # Check if user came from referral
            if context.args and len(context.args) > 0:
                ref_code = context.args[0]
                await _handle_referral(ref_code, user_id)
                new_user['referred_by'] = ref_code
            
            db.create_user(new_user)
            user_data = new_user
            
            logger.info(f"✅ New user registered: {user_id} (@{user.username})")
        
        # Check if banned
        if user_data.get('is_banned', False):
            await update.message.reply_text(
                "🚫 **You are banned**\n\n"
                "You have been banned from using this bot.\n"
                "Contact an administrator if you think this is a mistake.",
                parse_mode='Markdown'
            )
            return False, None
        
        # Update last activity
        db.update_user(user_id, {'last_seen': datetime.utcnow()})
        
        return True, user_data
        
    except Exception as e:
        logger.error(f"❌ Error checking user status: {e}")
        return False, None


async def _handle_referral(ref_code: str, new_user_id: int):
    """Handle referral reward"""
    try:
        # Extract referrer ID from code (format: REF{user_id}_{random})
        if ref_code.startswith('REF'):
            parts = ref_code[3:].split('_')
            if parts:
                referrer_id = int(parts[0])
                
                # Verify referrer exists
                referrer = db.get_user(referrer_id)
                if referrer:
                    # Increment referral count
                    from google.cloud import firestore
                    db.db.collection(Config.USERS_COLLECTION).document(str(referrer_id)).update({
                        'referral_count': firestore.Increment(1)
                    })
                    
                    # Add referral record
                    db.db.collection(Config.REFERRALS_COLLECTION).document(str(new_user_id)).set({
                        'referrer_id': referrer_id,
                        'referred_id': new_user_id,
                        'referral_code': ref_code,
                        'created_at': firestore.SERVER_TIMESTAMP,
                        'reward_given': False
                    })
                    
                    logger.info(f"✅ Referral: {referrer_id} referred {new_user_id}")
                    
    except Exception as e:
        logger.error(f"❌ Error handling referral: {e}")


async def check_force_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """
    Check if user has joined required channels/groups
    
    Returns:
        True if user has access, False if needs to subscribe
    """
    if not Config.FORCE_SUB_ENABLED:
        return True
    
    user_id = update.effective_user.id
    
    # Admins bypass force sub
    if Config.is_admin(user_id):
        return True
    
    try:
        channels_to_check = []
        if Config.FORCE_SUB_CHANNEL:
            channels_to_check.append(Config.FORCE_SUB_CHANNEL)
        if Config.FORCE_SUB_GROUP:
            channels_to_check.append(Config.FORCE_SUB_GROUP)
        
        not_joined = []
        
        for channel_id in channels_to_check:
            try:
                member = await context.bot.get_chat_member(channel_id, user_id)
                if member.status in ['left', 'kicked']:
                    not_joined.append(channel_id)
            except Exception as e:
                logger.error(f"❌ Error checking membership for {channel_id}: {e}")
                not_joined.append(channel_id)
        
        if not_joined:
            # User hasn't joined - send force sub message
            await _send_force_sub_message(update, not_joined)
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in force subscription check: {e}")
        return True  # Allow on error to avoid blocking users


async def _send_force_sub_message(update: Update, channels: list):
    """Send force subscription message"""
    keyboard = []
    
    for idx, channel_id in enumerate(channels, 1):
        # Create join button
        keyboard.append([
            InlineKeyboardButton(
                f"📢 Join Channel/Group {idx}",
                url=f"https://t.me/{abs(channel_id)}"
            )
        ])
    
    # Add verify button
    keyboard.append([
        InlineKeyboardButton(
            "✅ I Joined - Verify",
            callback_data="verify_subscription"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔒 **Subscription Required**\n\n"
        "To use this bot, you must join our channel/group.\n\n"
        "👇 Click the button(s) below to join, then click verify.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def check_group_permission(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """
    Check if bot is allowed in this group
    
    Returns:
        True if allowed, False if not
    """
    chat = update.effective_chat
    
    # Allow in private chats
    if chat.type == 'private':
        return True
    
    # Admins can use bot anywhere
    if Config.is_admin(update.effective_user.id):
        return True
    
    try:
        # Check if group is in allowed list
        group_id = chat.id
        is_allowed = db.is_group_allowed(group_id)
        
        if not is_allowed:
            await update.message.reply_text(
                "⛔ **Unauthorized Group**\n\n"
                "This bot is not authorized to work in this group.\n"
                "Please contact an administrator to enable the bot here.",
                parse_mode='Markdown'
            )
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking group permission: {e}")
        return True  # Allow on error


async def verify_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription verification callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Check if user has joined
    if not Config.FORCE_SUB_ENABLED:
        await query.edit_message_text("✅ Verification not required.")
        return
    
    try:
        channels_to_check = []
        if Config.FORCE_SUB_CHANNEL:
            channels_to_check.append(Config.FORCE_SUB_CHANNEL)
        if Config.FORCE_SUB_GROUP:
            channels_to_check.append(Config.FORCE_SUB_GROUP)
        
        not_joined = []
        
        for channel_id in channels_to_check:
            try:
                member = await context.bot.get_chat_member(channel_id, user_id)
                if member.status in ['left', 'kicked']:
                    not_joined.append(channel_id)
            except Exception:
                not_joined.append(channel_id)
        
        if not_joined:
            await query.edit_message_text(
                "❌ **Not Verified**\n\n"
                "You haven't joined all required channels/groups yet.\n"
                "Please join them and try again.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "✅ **Verified Successfully!**\n\n"
                "You can now use the bot. Send /help to get started.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"❌ Error verifying subscription: {e}")
        await query.edit_message_text(
            "❌ **Verification Failed**\n\n"
            "An error occurred. Please try again later.",
            parse_mode='Markdown'
      )
