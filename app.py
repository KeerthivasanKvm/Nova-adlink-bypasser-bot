"""
Flask Application
Web server for webhook mode and API endpoints
"""

import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application

from config import Config
from bot import error_handler, post_init
from handlers import user, admin, bypass, callback
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY

# Telegram bot application
bot_app = None


async def initialize_bot():
    """Initialize Telegram bot"""
    global bot_app
    
    if bot_app:
        return bot_app
    
    logger.info("🤖 Initializing Telegram bot...")
    
    # Create application
    bot_app = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .build()
    )
    
    # Register handlers (same as bot.py)
    # User commands
    bot_app.add_handler(CommandHandler("start", user.start_command))
    bot_app.add_handler(CommandHandler("help", user.help_command))
    bot_app.add_handler(CommandHandler("premium", user.premium_command))
    bot_app.add_handler(CommandHandler("stats", user.stats_command))
    bot_app.add_handler(CommandHandler("sites", user.sites_command))
    bot_app.add_handler(CommandHandler("refer", user.refer_command))
    bot_app.add_handler(CommandHandler("redeem", user.redeem_command))
    bot_app.add_handler(CommandHandler("reset", user.reset_command))
    bot_app.add_handler(CommandHandler("report", user.report_command))
    bot_app.add_handler(CommandHandler("request", user.request_command))
    
    # Bypass commands
    bot_app.add_handler(CommandHandler("bypass", bypass.bypass_command))
    bot_app.add_handler(CommandHandler("b", bypass.bypass_command))
    
    # Admin commands
    bot_app.add_handler(CommandHandler("broadcast", admin.broadcast_command))
    bot_app.add_handler(CommandHandler("generate_token", admin.generate_token_command))
    bot_app.add_handler(CommandHandler("generate_reset", admin.generate_reset_command))
    bot_app.add_handler(CommandHandler("addsite", admin.addsite_command))
    bot_app.add_handler(CommandHandler("removesite", admin.removesite_command))
    bot_app.add_handler(CommandHandler("addgroup", admin.addgroup_command))
    bot_app.add_handler(CommandHandler("removegroup", admin.removegroup_command))
    bot_app.add_handler(CommandHandler("ban", admin.ban_command))
    bot_app.add_handler(CommandHandler("unban", admin.unban_command))
    bot_app.add_handler(CommandHandler("set_limit", admin.set_limit_command))
    bot_app.add_handler(CommandHandler("toggle_referral", admin.toggle_referral_command))
    bot_app.add_handler(CommandHandler("users", admin.users_command))
    bot_app.add_handler(CommandHandler("settings", admin.settings_command))
    
    # Callback handlers
    bot_app.add_handler(CallbackQueryHandler(callback.callback_handler))
    
    # Message handler
    bot_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r'https?://'),
            bypass.direct_link_handler
        )
    )
    
    # Error handler
    bot_app.add_error_handler(error_handler)
    
    # Initialize
    await bot_app.initialize()
    await post_init(bot_app)
    
    # Set webhook
    if Config.WEBHOOK_MODE and Config.WEBHOOK_URL:
        webhook_url = Config.get_webhook_url()
        await bot_app.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")
    
    return bot_app


@app.route('/')
def index():
    """Home page"""
    return jsonify({
        'status': 'running',
        'bot': 'Nova Link Bypasser Bot',
        'version': '1.0.0',
        'mode': 'webhook' if Config.WEBHOOK_MODE else 'polling'
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db.db else 'disconnected'
    }), 200


@app.route(Config.WEBHOOK_PATH, methods=['POST'])
async def webhook():
    """Handle incoming webhook updates"""
    try:
        # Get update
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot_app.bot)
        
        # Process update
        await bot_app.process_update(update)
        
        return jsonify({'ok': True})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/bypass', methods=['POST'])
async def api_bypass():
    """API endpoint for bypassing links"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Import bypass service
        from services import intelligent_bypasser
        
        # Perform bypass
        result = await intelligent_bypasser.bypass(url)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ API bypass error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get bot statistics"""
    try:
        from services import intelligent_bypasser
        
        stats = {
            'total_users': db.get_total_users(),
            'premium_users': db.get_premium_users_count(),
            'total_bypasses': db.get_total_bypasses(),
            'bypass_stats': intelligent_bypasser.get_statistics()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Stats API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.before_serving
async def startup():
    """Run on startup"""
    logger.info("🚀 Starting Flask application...")
    await initialize_bot()
    logger.info("✅ Flask application ready!")


if __name__ == '__main__':
    # Run Flask app
    asyncio.run(startup())
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
)
