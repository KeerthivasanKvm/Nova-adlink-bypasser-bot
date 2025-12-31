"""
Callback Query Handlers
Handle inline button callbacks
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from middlewares.auth import verify_subscription_callback

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main callback handler - routes callback queries to appropriate handlers
    """
    query = update.callback_query
    
    # Always answer callback query to remove loading state
    await query.answer()
    
    data = query.data
    
    try:
        # Route to appropriate handler based on callback data
        if data == "verify_subscription":
            await verify_subscription_callback(update, context)
        
        elif data.startswith("help_"):
            await _handle_help_callback(update, context, data)
        
        elif data.startswith("premium_"):
            await _handle_premium_callback(update, context, data)
        
        elif data == "close":
            await _handle_close_callback(update, context)
        
        else:
            logger.warning(f"Unknown callback data: {data}")
            await query.answer("⚠️ Unknown action", show_alert=True)
    
    except Exception as e:
        logger.error(f"Callback handler error: {e}", exc_info=True)
        await query.answer("❌ An error occurred", show_alert=True)


async def _handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle help-related callbacks"""
    query = update.callback_query
    
    if data == "help_commands":
        help_text = (
            "📝 **Available Commands:**\n\n"
            "**Basic:**\n"
            "/start - Start the bot\n"
            "/help - Show help menu\n"
            "/bypass <link> - Bypass a link\n"
            "/b <link> - Quick bypass\n\n"
            "**Account:**\n"
            "/premium - Premium status\n"
            "/stats - Your statistics\n"
            "/refer - Referral link\n\n"
            "**Support:**\n"
            "/sites - Supported sites\n"
            "/report - Report issue\n"
            "/request - Request site"
        )
        
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown'
        )
    
    elif data == "help_main":
        from templates.messages import Messages as MSG
        from config import Config
        
        help_text = MSG.HELP.format(
            referral_reward=Config.REFERRAL_REWARD_BYPASSES
        )
        
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown'
        )


async def _handle_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle premium-related callbacks"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if data == "premium_info":
        from templates.messages import Messages as MSG
        from config import Config
        from database import db
        
        user_data = db.get_user(user_id)
        
        if user_data:
            is_premium = user_data.get('is_premium', False)
            premium_until = user_data.get('premium_until')
            
            if is_premium:
                if premium_until:
                    from datetime import datetime
                    if isinstance(premium_until, str):
                        premium_until = datetime.fromisoformat(premium_until)
                    
                    days_left = (premium_until - datetime.utcnow()).days
                    expiry_info = f"📅 Expires in: **{days_left} days**\n📆 Expiry Date: {premium_until.strftime('%Y-%m-%d')}"
                else:
                    expiry_info = "♾️ **Lifetime Premium**"
                
                status = "💎 **Premium Active**"
            else:
                status = "🆓 **Free Plan**"
                expiry_info = ""
            
            premium_text = MSG.PREMIUM_INFO.format(
                status=status,
                expiry_info=expiry_info,
                free_limit=Config.FREE_USER_DAILY_LIMIT
            )
            
            await query.edit_message_text(
                premium_text,
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ User data not found", show_alert=True)


async def _handle_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle close button callback"""
    query = update.callback_query
    
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
        await query.answer("✅ Closed", show_alert=False)
