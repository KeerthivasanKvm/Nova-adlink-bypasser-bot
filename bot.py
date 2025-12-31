"""
Main Bot File
Entry point for the Telegram bot (Polling Mode)
"""

import logging
import sys
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import Config
from database import db

# Import handlers (we'll create these)
from handlers import user, admin, bypass, callback

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    except:
        pass


async def post_init(application: Application):
    """Post initialization tasks"""
    logger.info("🚀 Bot initialized successfully!")
    logger.info(f"📊 Bot username: @{application.bot.username}")
    
    # Test database connection
    if db.db:
        logger.info("✅ Database connected")
    else:
        logger.error("❌ Database connection failed!")


def main():
    """Main function to run the bot"""
    try:
        logger.info("=" * 50)
        logger.info("🤖 Starting Nova Link Bypasser Bot")
        logger.info("=" * 50)
        
        # Validate configuration
        if not Config.validate():
            logger.error("❌ Configuration validation failed!")
            sys.exit(1)
        
        # Create application
        application = (
            Application.builder()
            .token(Config.BOT_TOKEN)
            .post_init(post_init)
            .build()
        )
        
        # Register command handlers
        logger.info("📝 Registering handlers...")
        
        # User commands
        application.add_handler(CommandHandler("start", user.start_command))
        application.add_handler(CommandHandler("help", user.help_command))
        application.add_handler(CommandHandler("premium", user.premium_command))
        application.add_handler(CommandHandler("stats", user.stats_command))
        application.add_handler(CommandHandler("sites", user.sites_command))
        application.add_handler(CommandHandler("refer", user.refer_command))
        application.add_handler(CommandHandler("redeem", user.redeem_command))
        application.add_handler(CommandHandler("reset", user.reset_command))
        application.add_handler(CommandHandler("report", user.report_command))
        application.add_handler(CommandHandler("request", user.request_command))
        
        # Bypass commands
        application.add_handler(CommandHandler("bypass", bypass.bypass_command))
        application.add_handler(CommandHandler("b", bypass.bypass_command))
        
        # Admin commands
        application.add_handler(CommandHandler("broadcast", admin.broadcast_command))
        application.add_handler(CommandHandler("generate_token", admin.generate_token_command))
        application.add_handler(CommandHandler("generate_reset", admin.generate_reset_command))
        application.add_handler(CommandHandler("addsite", admin.addsite_command))
        application.add_handler(CommandHandler("removesite", admin.removesite_command))
        application.add_handler(CommandHandler("addgroup", admin.addgroup_command))
        application.add_handler(CommandHandler("removegroup", admin.removegroup_command))
        application.add_handler(CommandHandler("ban", admin.ban_command))
        application.add_handler(CommandHandler("unban", admin.unban_command))
        application.add_handler(CommandHandler("set_limit", admin.set_limit_command))
        application.add_handler(CommandHandler("toggle_referral", admin.toggle_referral_command))
        application.add_handler(CommandHandler("users", admin.users_command))
        application.add_handler(CommandHandler("settings", admin.settings_command))
        
        # Callback query handlers
        application.add_handler(CallbackQueryHandler(callback.callback_handler))
        
        # Message handler for direct links
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.Regex(r'https?://'),
                bypass.direct_link_handler
            )
        )
        
        # Error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers registered")
        
        # Start bot
        if Config.WEBHOOK_MODE:
            logger.info("🌐 Starting in WEBHOOK mode...")
            logger.warning("⚠️ Webhook mode requires Flask app running!")
            logger.warning("⚠️ Use app.py for webhook mode")
        else:
            logger.info("🔄 Starting in POLLING mode...")
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
