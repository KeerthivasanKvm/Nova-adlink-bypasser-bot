"""
User Command Handlers
Handle user-facing commands
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import db
from middlewares.auth import check_user_status, check_force_subscription
from templates.messages import Messages as MSG
from utils import format_datetime, time_ago

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    if not await check_force_subscription(update, context):
        return
    
    await update.message.reply_text(
        MSG.WELCOME,
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    help_text = MSG.HELP.format(
        referral_reward=Config.REFERRAL_REWARD_BYPASSES
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /premium command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
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
    
    await update.message.reply_text(
        premium_text,
        parse_mode='Markdown'
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    from datetime import datetime
    
    is_premium = user_data.get('is_premium', False)
    premium_until = user_data.get('premium_until')
    
    if is_premium and premium_until:
        if isinstance(premium_until, str):
            premium_until = datetime.fromisoformat(premium_until)
        days_left = (premium_until - datetime.utcnow()).days
        premium_expiry = f"⏰ Premium expires in: **{days_left} days**"
    else:
        premium_expiry = ""
    
    created_at = user_data.get('created_at')
    if created_at:
        member_since = time_ago(created_at)
    else:
        member_since = "Recently"
    
    stats_text = MSG.STATS.format(
        user_id=user_data['user_id'],
        member_since=member_since,
        status="💎 Premium" if is_premium else "🆓 Free",
        total_bypasses=user_data.get('bypass_count', 0),
        daily_bypasses=user_data.get('daily_bypass_count', 0),
        daily_limit=Config.FREE_USER_DAILY_LIMIT if not is_premium else "♾️",
        monthly_bypasses=user_data.get('monthly_bypass_count', 0),
        referral_code=user_data.get('referral_code', 'N/A'),
        referral_count=user_data.get('referral_count', 0),
        bonus_bypasses=user_data.get('referral_count', 0) * Config.REFERRAL_REWARD_BYPASSES,
        premium_expiry=premium_expiry
    )
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown'
    )


async def sites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sites command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    sites = db.get_active_sites()
    
    # Format sites list (show first 50 sites if too many)
    sites_to_show = sorted(sites)[:50]
    sites_formatted = "\n".join([f"• {site}" for site in sites_to_show])
    
    if len(sites) > 50:
        sites_formatted += f"\n\n... and {len(sites) - 50} more sites"
    
    sites_text = MSG.SITES_LIST.format(
        total=len(sites),
        sites_list=sites_formatted
    )
    
    await update.message.reply_text(
        sites_text,
        parse_mode='Markdown'
    )


async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /refer command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    if not Config.REFERRAL_ENABLED:
        await update.message.reply_text(
            "⚠️ Referral system is currently disabled.",
            parse_mode='Markdown'
        )
        return
    
    referral_code = user_data.get('referral_code')
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    refer_text = MSG.REFERRAL_INFO.format(
        referral_link=referral_link,
        referral_count=user_data.get('referral_count', 0),
        bonus_bypasses=user_data.get('referral_count', 0) * Config.REFERRAL_REWARD_BYPASSES,
        reward=Config.REFERRAL_REWARD_BYPASSES,
        min_referrals=Config.MIN_REFERRALS_FOR_REWARD
    )
    
    await update.message.reply_text(
        refer_text,
        parse_mode='Markdown'
    )


async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /redeem command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/redeem <token>`\n\n"
            "Example: `/redeem ABC123XYZ`",
            parse_mode='Markdown'
        )
        return
    
    token = context.args[0]
    user_id = update.effective_user.id
    
    from middlewares.rate_limit import redeem_access_token
    success, message = await redeem_access_token(user_id, token)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/reset <reset_key>`\n\n"
            "Example: `/reset RESET_1234567_ABCD1234`",
            parse_mode='Markdown'
        )
        return
    
    reset_key = context.args[0]
    user_id = update.effective_user.id
    
    from middlewares.rate_limit import reset_user_limit
    success, message = await reset_user_limit(user_id, reset_key)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/report <link> [description]`\n\n"
            "Example: `/report https://example.com/link This link doesn't work`",
            parse_mode='Markdown'
        )
        return
    
    link = context.args[0]
    description = " ".join(context.args[1:]) if len(context.args) > 1 else "No description"
    
    # Generate report ID
    import uuid
    report_id = str(uuid.uuid4())[:8]
    
    # Send report to admin
    report_message = (
        f"📝 **New Error Report**\n\n"
        f"Report ID: `{report_id}`\n"
        f"User: {update.effective_user.id} (@{update.effective_user.username})\n"
        f"Link: {link}\n"
        f"Description: {description}"
    )
    
    # Send to owner
    try:
        await context.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=report_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send report to admin: {e}")
    
    # Confirm to user
    await update.message.reply_text(
        MSG.ERROR_REPORT_SENT.format(
            report_id=report_id,
            link=link
        ),
        parse_mode='Markdown'
    )


async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /request command"""
    allowed, user_data = await check_user_status(update, context)
    if not allowed:
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/request <site_url> [reason]`\n\n"
            "Example: `/request https://newsite.com Please add support`",
            parse_mode='Markdown'
        )
        return
    
    site_url = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
    
    from utils import extract_domain
    domain = extract_domain(site_url)
    
    # Generate request ID
    import uuid
    request_id = str(uuid.uuid4())[:8]
    
    # Send to admin
    request_message = (
        f"📮 **New Site Request**\n\n"
        f"Request ID: `{request_id}`\n"
        f"User: {update.effective_user.id} (@{update.effective_user.username})\n"
        f"Site: {site_url}\n"
        f"Domain: {domain}\n"
        f"Reason: {reason}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=Config.OWNER_ID,
            text=request_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send site request to admin: {e}")
    
    # Confirm to user
    await update.message.reply_text(
        MSG.SITE_REQUEST_SENT.format(
            request_id=request_id,
            site=domain or site_url
        ),
        parse_mode='Markdown'
  )
