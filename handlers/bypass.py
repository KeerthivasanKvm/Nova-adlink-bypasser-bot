"""
Bypass Command Handlers - FIXED VERSION
Handle link bypassing operations
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
import html

from config import Config
from database import db
from middlewares.auth import check_user_status, check_force_subscription, check_group_permission
from middlewares.rate_limit import check_rate_limit
from services import intelligent_bypasser
from templates.messages import Messages as MSG
from utils import is_valid_url

logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown"""
    # Escape problematic characters
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text


async def bypass_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bypass and /b commands"""
    # Check user status
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    # Check force subscription
    if not await check_force_subscription(update, context):
        return
    
    # Check group permission
    if not await check_group_permission(update, context):
        return
    
    # Check if link provided
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/bypass <link>` or `/b <link>`\n\n"
            "**Example:**\n"
            "`/bypass https://example.com/short/abc123`\n\n"
            "Or simply send me any link directly!",
            parse_mode='Markdown'
        )
        return
    
    url = context.args[0]
    
    # Validate URL
    if not is_valid_url(url):
        await update.message.reply_text(
            MSG.ERROR_INVALID_URL,
            parse_mode='Markdown'
        )
        return
    
    # Check rate limit
    can_bypass, limit_msg = await check_rate_limit(update, context, user_data)
    if not can_bypass:
        return
    
    # Process bypass
    await _process_bypass(update, context, url, user_data)


async def direct_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direct link messages (without command)"""
    # Same checks as bypass_command
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    if not await check_force_subscription(update, context):
        return
    
    if not await check_group_permission(update, context):
        return
    
    url = update.message.text.strip()
    
    # Validate URL
    if not is_valid_url(url):
        # Don't respond to invalid URLs (might be normal chat)
        return
    
    # Check rate limit
    can_bypass, limit_msg = await check_rate_limit(update, context, user_data)
    if not can_bypass:
        return
    
    # Process bypass
    await _process_bypass(update, context, url, user_data)


async def _process_bypass(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, user_data: dict):
    """
    Process bypass request
    
    Args:
        update: Telegram update
        context: Bot context
        url: URL to bypass
        user_data: User data from database
    """
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ **Processing your link...**\n\n"
        "🔍 Checking cache...\n"
        "⚡ This may take 5-30 seconds\n\n"
        "Please wait...",
        parse_mode='Markdown'
    )
    
    try:
        # Perform bypass using intelligent bypasser
        result = await intelligent_bypasser.bypass(url, user_data['user_id'])
        
        if result['success']:
            # Success! Increment user bypass count
            db.increment_bypass_count(user_data['user_id'])
            
            # Format cache info
            if result.get('from_cache'):
                cache_info = "\n💾 **Retrieved from cache** (instant!)"
            else:
                cache_info = ""
            
            # Format method info
            method = result.get('method', 'unknown')
            if method.startswith('learned_'):
                method_info = f"🧠 AI Learned Pattern"
            elif method == 'ai_generated':
                method_info = f"🤖 AI Generated"
            elif method == 'cache':
                method_info = f"💾 Cache"
            else:
                method_info = f"🔧 Method: {method}"
            
            # Truncate URLs for display
            original_display = url[:50] + "..." if len(url) > 50 else url
            bypassed_display = result['url'][:50] + "..." if len(result['url']) > 50 else result['url']
            
            success_message = (
                f"✅ **Link Bypassed Successfully!**\n\n"
                f"🔗 **Original:**\n`{original_display}`\n\n"
                f"🎯 **Result:**\n`{bypassed_display}`\n\n"
                f"{method_info}\n"
                f"⏱️ Time: {result['time_taken']}s"
                f"{cache_info}\n\n"
                f"💡 **Tip:** Use /refer to invite friends and earn more bypasses!"
            )
            
            await processing_msg.edit_text(
                success_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ Bypass success for user {user_data['user_id']}: {url}")
            
        else:
            # Bypass failed
            # FIXED: Escape error message to prevent parse errors
            error_reason = str(result.get('error', 'Unknown error'))
            # Remove any markdown characters that could break formatting
            error_reason = error_reason.replace('*', '').replace('_', '').replace('`', '')[:100]
            
            fail_message = (
                f"❌ **Bypass Failed**\n\n"
                f"😞 Unable to bypass this link.\n\n"
                f"**Possible reasons:**\n"
                f"• Link format not supported\n"
                f"• Site protection too strong\n"
                f"• Temporary server issue\n"
                f"• Invalid or expired link\n\n"
                f"**What you can do:**\n"
                f"• Try again in a few moments\n"
                f"• Use /report to report the issue\n"
                f"• Check if the link is correct\n\n"
                f"Error details: {error_reason}"
            )
            
            await processing_msg.edit_text(
                fail_message,
                parse_mode='Markdown'
            )
            
            logger.warning(f"❌ Bypass failed for user {user_data['user_id']}: {url} - {error_reason}")
    
    except Exception as e:
        logger.error(f"❌ Bypass processing error for user {user_data['user_id']}: {e}", exc_info=True)
        
        try:
            # FIXED: Remove parse_mode entirely for error messages with unpredictable content
            error_msg = str(e)[:100]
            # Clean the error message
            error_msg = error_msg.replace('*', '').replace('_', '').replace('`', '')
            
            await processing_msg.edit_text(
                "❌ An error occurred\n\n"
                "Please try again later or contact support.\n\n"
                f"Error: {error_msg}"
                # NO parse_mode to avoid formatting issues
            )
        except Exception as edit_error:
            # If edit fails, send new message
            logger.error(f"Failed to edit message: {edit_error}")
            try:
                await update.message.reply_text(
                    "❌ An error occurred\n\n"
                    "Please try again later or contact support."
                    # NO parse_mode
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
