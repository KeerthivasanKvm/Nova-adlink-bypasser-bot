"""
Message Templates
Predefined message templates for bot responses
"""

from typing import Dict, Any


class Messages:
    """Message templates for the bot"""
    
    # Welcome Messages
    WELCOME = """
👋 **Welcome to Nova Link Bypasser Bot!**

I can bypass ad-link shorteners and generate direct download links with **10 advanced methods**.

🔓 **What I can do:**
• Bypass 100+ link shorteners
• Generate direct download links
• Skip countdown timers
• Bypass Cloudflare protection
• And much more!

📝 **Quick Start:**
Just send me any supported link and I'll bypass it for you!

Use /help to see all available commands.
"""
    
    HELP = """
📚 **Help Menu**

**🔓 Basic Commands:**
/start - Start the bot
/help - Show this menu
/bypass <link> or /b <link> - Bypass a link
/sites - List supported sites

**💎 Premium Commands:**
/premium - Check premium status & upgrade
/stats - View your usage statistics
/refer - Get your referral link

**📢 Feedback:**
/report <link> - Report broken/unsupported link
/request <site> - Request support for new website

**ℹ️ How to use:**
1. Send me a supported link
2. Wait for processing (5-30 seconds)
3. Get your bypassed link!

**🎁 Referral System:**
Invite friends to earn extra bypasses!
Each friend gives you {referral_reward} bonus bypasses.

**Need help?** Contact: @YourSupportChannel
"""
    
    PREMIUM_INFO = """
💎 **Premium Subscription**

**Current Status:** {status}
{expiry_info}

**🆓 Free Plan:**
• {free_limit} bypasses per day
• Standard priority
• Cache access

**💎 Premium Plan:**
• ✅ Unlimited bypasses
• ⚡ High priority processing
• 🎯 Advanced methods
• 💾 Extended cache access
• 🔔 Expiry notifications

**🎟️ How to get Premium:**
1. Use an access token from admin
2. Earn through referrals
3. Contact admin for purchase

Use /refer to invite friends and earn premium access!
"""
    
    STATS = """
📊 **Your Statistics**

**Account Info:**
👤 User ID: `{user_id}`
📅 Member Since: {member_since}
💎 Status: {status}

**Usage Statistics:**
✅ Total Bypasses: {total_bypasses}
📅 Today: {daily_bypasses}/{daily_limit}
📆 This Month: {monthly_bypasses}

**Referral Stats:**
🎁 Referral Code: `{referral_code}`
👥 Total Referrals: {referral_count}
🎯 Bonus Bypasses: {bonus_bypasses}

{premium_expiry}
"""
    
    SITES_LIST = """
🌐 **Supported Sites** ({total} sites)

{sites_list}

**Can't find your site?**
Use /request <site_url> to request support!

**Note:** New sites are added regularly based on user requests.
"""
    
    BYPASS_PROCESSING = """
⏳ **Processing your link...**

🔍 Method: {method}
⏱️ This may take 5-30 seconds

Please wait...
"""
    
    BYPASS_SUCCESS = """
✅ **Link Bypassed Successfully!**

🔗 **Original:** {original_url}

🎯 **Result:** {bypassed_url}

⚡ Method Used: {method}
⏱️ Time Taken: {time_taken}s
{cache_info}

**Share with friends!** Use /refer to get your referral link.
"""
    
    BYPASS_ERROR = """
❌ **Bypass Failed**

😞 Unable to bypass this link.

**Possible reasons:**
• Link format not supported
• Site protection too strong
• Temporary server issue
• Invalid/expired link

**What you can do:**
• Try again in a few moments
• Use /report <link> to report the issue
• Check if the link is correct

**Need help?** Contact @YourSupportChannel
"""
    
    CACHE_HIT = """
✅ **Link Bypassed** (From Cache)

🔗 **Result:** {bypassed_url}

💾 This link was previously bypassed
⚡ Instant delivery from cache!

**Share with friends!** Use /refer
"""
    
    # Admin Messages
    TOKEN_GENERATED = """
🎟️ **Access Token Generated**

**Token:** `{token}`
**Duration:** {duration}
**Expires:** {expires_at}
**Created by:** {created_by}

**Instructions:**
1. Share this token with the user
2. User sends: /redeem {token}
3. Token can only be used once

⚠️ **Keep this token safe!**
"""
    
    RESET_KEY_GENERATED = """
🔑 **Universal Reset Key Generated**

**Reset Key:** `{reset_key}`
**Created:** {created_at}
**Created by:** {created_by}

**Instructions:**
Anyone can use this key to reset their daily limit:
/reset {reset_key}

⚠️ **This key works for all users!**
"""
    
    BROADCAST_SENT = """
📢 **Broadcast Message Sent**

✅ Successfully sent to: {success_count} users
❌ Failed: {failed_count} users
⏱️ Time taken: {time_taken}s

**Message:**
{message}
"""
    
    SITE_ADDED = """
✅ **Site Added Successfully**

🌐 Domain: `{domain}`
📅 Added: {added_at}
👤 Added by: {added_by}

The site is now supported for bypassing!
"""
    
    SITE_REMOVED = """
❌ **Site Removed**

🌐 Domain: `{domain}`

The site has been removed from supported list.
"""
    
    USER_BANNED = """
🚫 **User Banned**

👤 User ID: `{user_id}`
📅 Banned at: {banned_at}
👤 Banned by: {banned_by}

The user can no longer use the bot.
"""
    
    USER_UNBANNED = """
✅ **User Unbanned**

👤 User ID: `{user_id}`
📅 Unbanned at: {unbanned_at}

The user can now use the bot again.
"""
    
    GROUP_ADDED = """
✅ **Group Added**

👥 Group ID: `{group_id}`
📝 Group Name: {group_name}
📅 Added: {added_at}

The bot can now be used in this group.
"""
    
    # Error/Feedback Messages
    ERROR_REPORT_SENT = """
📝 **Error Report Sent**

Thank you for reporting! Our team will look into it.

**Report ID:** `{report_id}`
**Link:** {link}

We'll notify you once it's fixed!
"""
    
    SITE_REQUEST_SENT = """
📮 **Site Request Submitted**

Thank you for your suggestion!

**Request ID:** `{request_id}`
**Site:** {site}

We'll review your request and add the site if possible.
"""
    
    # Referral Messages
    REFERRAL_INFO = """
🎁 **Referral Program**

**Your Referral Link:**
`{referral_link}`

**Your Stats:**
👥 Total Referrals: {referral_count}
🎯 Bonus Bypasses: {bonus_bypasses}

**How it works:**
1. Share your referral link
2. Friends click and /start the bot
3. You get {reward} bonus bypasses per referral
4. After {min_referrals} referrals, get rewards!

**Share now and earn unlimited bypasses!**
"""
    
    REFERRAL_SUCCESS = """
🎉 **Referral Successful!**

Someone joined using your referral link!

**Reward:** +{reward} bypasses added to your account
**Total Referrals:** {total_referrals}

Keep sharing to earn more!
"""
    
    # Notification Messages
    PREMIUM_EXPIRING = """
⏰ **Premium Subscription Expiring**

Your premium subscription will expire in {days} days!

**Expires on:** {expiry_date}

Want to extend? Contact @YourAdminChannel
"""
    
    PREMIUM_EXPIRED = """
💎 **Premium Subscription Expired**

Your premium subscription has ended.

**What you can do:**
• Use /refer to invite friends
• Contact admin for renewal
• Continue with free plan

Thank you for being a premium member!
"""
    
    FORCE_SUB = """
🔒 **Subscription Required**

To use this bot, you must join our channel/group:

{channels}

After joining, press the button below to verify.
"""
    
    # Error Messages
    ERROR_INVALID_URL = "❌ Invalid URL format. Please send a valid link."
    ERROR_UNSUPPORTED_SITE = "❌ This site is not supported yet. Use /request to request support."
    ERROR_LIMIT_REACHED = """
⛔ **Daily Limit Reached**

You've used all {limit} bypasses for today.

**Options:**
• Wait until tomorrow for reset
• Use /refer to invite friends
• Use /premium to upgrade
• Contact admin for reset key
"""
    ERROR_BANNED = "🚫 You are banned from using this bot."
    ERROR_NO_PERMISSION = "⛔ You don't have permission to use this command."
    ERROR_INVALID_TOKEN = "❌ Invalid or expired access token."
    ERROR_TOKEN_USED = "❌ This token has already been used."
    ERROR_INVALID_GROUP = "⛔ This bot is not authorized in this group."
    
    @staticmethod
    def format(template: str, **kwargs) -> str:
        """
        Format message template with provided values
        
        Args:
            template: Message template string
            **kwargs: Values to insert
        
        Returns:
            Formatted message
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Error formatting message: Missing key {e}"


# Alias for easier access
MSG = Messages()
