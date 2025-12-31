"""
Admin Command Handlers
Handle admin-only commands
"""

import logging
import time
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from config import Config
from database import db
from utils.decorators import admin_only
from utils import generate_token, generate_reset_key, parse_duration, format_duration
from templates.messages import Messages as MSG

logger = logging.getLogger(__name__)


@admin_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/broadcast <message>`\n\n"
            "Example: `/broadcast Hello everyone! New features added.`",
            parse_mode='Markdown'
        )
        return
    
    message = " ".join(context.args)
    
    # Send confirmation
    confirm_msg = await update.message.reply_text(
        "📢 **Broadcasting message...**\n\n"
        f"Message: {message}\n\n"
        "Please wait...",
        parse_mode='Markdown'
    )
    
    # Get all users
    users = db.get_all_users()
    
    success_count = 0
    failed_count = 0
    start_time = time.time()
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=message,
                parse_mode='Markdown'
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user['user_id']}: {e}")
            failed_count += 1
    
    time_taken = round(time.time() - start_time, 2)
    
    await confirm_msg.edit_text(
        MSG.BROADCAST_SENT.format(
            success_count=success_count,
            failed_count=failed_count,
            time_taken=time_taken,
            message=message
        ),
        parse_mode='Markdown'
    )


@admin_only
async def generate_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate premium access token"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/generate_token <duration>`\n\n"
            "**Examples:**\n"
            "• `/generate_token 1h` - 1 hour\n"
            "• `/generate_token 1d` - 1 day\n"
            "• `/generate_token 7d` - 7 days\n"
            "• `/generate_token 1m` - 1 month\n"
            "• `/generate_token 1y` - 1 year",
            parse_mode='Markdown'
        )
        return
    
    duration_str = context.args[0]
    
    try:
        duration_type, value, expires_at = parse_duration(duration_str)
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}", parse_mode='Markdown')
        return
    
    # Generate token
    token = generate_token()
    
    # Store in database
    token_data = {
        'token': token,
        'duration_type': duration_type,
        'duration_value': value,
        'expires_at': expires_at,
        'created_by': update.effective_user.id
    }
    
    success = db.create_token(token_data)
    
    if not success:
        await update.message.reply_text(
            "❌ Failed to create token. Please try again.",
            parse_mode='Markdown'
        )
        return
    
    duration_formatted = format_duration(duration_type, value)
    
    await update.message.reply_text(
        MSG.TOKEN_GENERATED.format(
            token=token,
            duration=duration_formatted,
            expires_at=expires_at.strftime('%Y-%m-%d %H:%M UTC'),
            created_by=update.effective_user.username or "Admin"
        ),
        parse_mode='Markdown'
    )


@admin_only
async def generate_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate universal reset key"""
    reset_key = generate_reset_key()
    
    # Store in database
    key_data = {
        'key': reset_key,
        'created_by': update.effective_user.id,
        'is_active': True,
        'usage_count': 0
    }
    
    success = db.create_reset_key(key_data)
    
    if not success:
        await update.message.reply_text(
            "❌ Failed to create reset key. Please try again.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        MSG.RESET_KEY_GENERATED.format(
            reset_key=reset_key,
            created_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            created_by=update.effective_user.username or "Admin"
        ),
        parse_mode='Markdown'
    )


@admin_only
async def addsite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add supported site"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/addsite <domain>`\n\n"
            "Example: `/addsite newsite.com`",
            parse_mode='Markdown'
        )
        return
    
    domain = context.args[0].lower().replace('www.', '').replace('http://', '').replace('https://', '')
    
    success = db.add_site(domain, update.effective_user.id)
    
    if success:
        await update.message.reply_text(
            MSG.SITE_ADDED.format(
                domain=domain,
                added_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
                added_by=update.effective_user.username or "Admin"
            ),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to add site `{domain}`. It may already exist.",
            parse_mode='Markdown'
        )


@admin_only
async def removesite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove supported site"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/removesite <domain>`\n\n"
            "Example: `/removesite oldsite.com`",
            parse_mode='Markdown'
        )
        return
    
    domain = context.args[0].lower()
    
    success = db.remove_site(domain)
    
    if success:
        await update.message.reply_text(
            MSG.SITE_REMOVED.format(domain=domain),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Site `{domain}` not found or already removed.",
            parse_mode='Markdown'
        )


@admin_only
async def addgroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add allowed group"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/addgroup <group_id>`\n\n"
            "Example: `/addgroup -1001234567890`\n\n"
            "**How to get group ID:**\n"
            "1. Add bot to group\n"
            "2. Forward a message from group to @userinfobot\n"
            "3. Copy the group ID",
            parse_mode='Markdown'
        )
        return
    
    try:
        group_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid group ID. Must be a number.",
            parse_mode='Markdown'
        )
        return
    
    # Try to get group info
    try:
        chat = await context.bot.get_chat(group_id)
        group_title = chat.title
    except Exception:
        group_title = "Unknown Group"
    
    success = db.add_group(group_id, group_title, update.effective_user.id)
    
    if success:
        await update.message.reply_text(
            MSG.GROUP_ADDED.format(
                group_id=group_id,
                group_name=group_title,
                added_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            ),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to add group. It may already exist.",
            parse_mode='Markdown'
        )


@admin_only
async def removegroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove allowed group"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/removegroup <group_id>`\n\n"
            "Example: `/removegroup -1001234567890`",
            parse_mode='Markdown'
        )
        return
    
    try:
        group_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid group ID. Must be a number.",
            parse_mode='Markdown'
        )
        return
    
    success = db.remove_group(group_id)
    
    if success:
        await update.message.reply_text(
            f"✅ **Group Removed**\n\n"
            f"Group ID: `{group_id}`\n\n"
            f"The bot can no longer be used in this group.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Group `{group_id}` not found or already removed.",
            parse_mode='Markdown'
        )


@admin_only
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/ban <user_id>`\n\n"
            "Example: `/ban 123456789`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID. Must be a number.",
            parse_mode='Markdown'
        )
        return
    
    # Can't ban admins
    if Config.is_admin(user_id):
        await update.message.reply_text(
            "❌ Cannot ban an admin!",
            parse_mode='Markdown'
        )
        return
    
    success = db.update_user(user_id, {'is_banned': True, 'banned_at': datetime.utcnow()})
    
    if success:
        await update.message.reply_text(
            MSG.USER_BANNED.format(
                user_id=user_id,
                banned_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
                banned_by=update.effective_user.username or "Admin"
            ),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ User `{user_id}` not found.",
            parse_mode='Markdown'
        )


@admin_only
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/unban <user_id>`\n\n"
            "Example: `/unban 123456789`",
            parse_mode='Markdown'
        )
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID. Must be a number.",
            parse_mode='Markdown'
        )
        return
    
    success = db.update_user(user_id, {'is_banned': False, 'unbanned_at': datetime.utcnow()})
    
    if success:
        await update.message.reply_text(
            MSG.USER_UNBANNED.format(
                user_id=user_id,
                unbanned_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            ),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ User `{user_id}` not found.",
            parse_mode='Markdown'
        )


@admin_only
async def set_limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set free user bypass limit"""
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage:** `/set_limit <number>`\n\n"
            "Example: `/set_limit 20`\n\n"
            "Current limit: " + str(Config.FREE_USER_DAILY_LIMIT),
            parse_mode='Markdown'
        )
        return
    
    try:
        new_limit = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number. Must be an integer.",
            parse_mode='Markdown'
        )
        return
    
    if new_limit < 1 or new_limit > 10000:
        await update.message.reply_text(
            "❌ Limit must be between 1 and 10000.",
            parse_mode='Markdown'
        )
        return
    
    # Update config (Note: This only affects current session)
    Config.FREE_USER_DAILY_LIMIT = new_limit
    
    await update.message.reply_text(
        f"✅ **Limit Updated**\n\n"
        f"New free user daily limit: **{new_limit}**\n\n"
        f"⚠️ Note: Restart bot to persist this change.",
        parse_mode='Markdown'
    )


@admin_only
async def toggle_referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle referral system"""
    current_status = Config.REFERRAL_ENABLED
    Config.REFERRAL_ENABLED = not current_status
    
    status = "✅ **Enabled**" if Config.REFERRAL_ENABLED else "❌ **Disabled**"
    
    await update.message.reply_text(
        f"🎁 **Referral System**\n\n"
        f"Status: {status}\n\n"
        f"⚠️ Note: Restart bot to persist this change.",
        parse_mode='Markdown'
    )


@admin_only
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user statistics"""
    total_users = db.get_total_users()
    premium_users = db.get_premium_users_count()
    total_bypasses = db.get_total_bypasses()
    
    from services import intelligent_bypasser
    bypass_stats = intelligent_bypasser.get_statistics()
    
    stats_text = (
        f"📊 **Bot Statistics**\n\n"
        f"**Users:**\n"
        f"• Total: {total_users}\n"
        f"• Premium: {premium_users}\n"
        f"• Free: {total_users - premium_users}\n\n"
        f"**Bypasses:**\n"
        f"• Total: {total_bypasses}\n"
        f"• Success Rate: {bypass_stats.get('success_rate', 0)}%\n"
        f"• Cache Hits: {bypass_stats.get('cache_hits', 0)}\n"
        f"• AI Assisted: {bypass_stats.get('ai_assisted_bypasses', 0)}\n\n"
        f"**AI Stats:**\n"
        f"• Analyses: {bypass_stats.get('ai_stats', {}).get('total_analyses', 0)}\n"
        f"• Learned Patterns: {bypass_stats.get('ai_stats', {}).get('learned_patterns_count', 0)}"
    )
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown'
    )


@admin_only
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View bot settings"""
    settings_text = (
        f"⚙️ **Bot Settings**\n\n"
        f"**Limits:**\n"
        f"• Free Daily Limit: {Config.FREE_USER_DAILY_LIMIT}\n"
        f"• Premium: Unlimited\n\n"
        f"**Features:**\n"
        f"• Referral System: {'✅ Enabled' if Config.REFERRAL_ENABLED else '❌ Disabled'}\n"
        f"• Force Subscribe: {'✅ Enabled' if Config.FORCE_SUB_ENABLED else '❌ Disabled'}\n"
        f"• Webhook Mode: {'✅ Yes' if Config.WEBHOOK_MODE else '❌ No (Polling)'}\n\n"
        f"**Referral:**\n"
        f"• Reward per referral: {Config.REFERRAL_REWARD_BYPASSES} bypasses\n"
        f"• Min referrals: {Config.MIN_REFERRALS_FOR_REWARD}\n\n"
        f"**Cache:**\n"
        f"• Expiry: {Config.CACHE_EXPIRY_HOURS} hours\n\n"
        f"**AI:**\n"
        f"• Provider: Google Gemini (FREE)\n"
        f"• Daily quota: 1500 requests"
    )
    
    await update.message.reply_text(
        settings_text,
        parse_mode='Markdown'
      )
