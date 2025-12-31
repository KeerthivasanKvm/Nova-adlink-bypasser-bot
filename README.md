# 🚀 Nova Link Bypasser Bot

A powerful, professional Telegram bot that bypasses ad links with 10 advanced methods, premium features, and MongoDB integration.

## ✨ Features

### 🔓 Advanced Bypass Methods (10 Methods)
1. **HTML Form Bypass** - Pure HTML sites with forms and meta tags
2. **CSS Hidden Elements** - CSS-only protection detection
3. **JavaScript Execution** - Complex JavaScript site handling
4. **Countdown Timer Bypass** - Automatic timer skip
5. **Dynamic Content** - AJAX/dynamic loading handling
6. **Cloudflare Bypass** - Advanced Cloudflare protection
7. **Redirect Chain** - Multi-step redirect following
8. **Base64 Decode** - Base64 encoded links
9. **URL Decode** - URL encoded content
10. **Browser Automation** - Full browser automation as fallback

### 💎 Premium System
- **Free Tier** - Limited daily/monthly bypasses
- **Premium Tier** - Unlimited bypasses
- **One-Time Access Tokens** - Flexible duration (hours/days/months)
- **Universal Reset Keys** - Admin-generated reset for free users

### 👥 User Management
- **Referral System** - Earn extra bypasses by inviting friends
- **Force Subscribe** - Require channel/group membership
- **Group Permissions** - Admin-controlled group access
- **Usage Statistics** - Track bypass history

### 🛡️ Admin Features
- **Token Management** - Generate time-based access tokens
- **Site Management** - Add/remove supported sites
- **Broadcast System** - Message all users
- **User Control** - Ban/unban, view stats
- **Rate Limiting** - Customizable limits
- **Referral Toggle** - Enable/disable referral system

### 🔧 Technical Features
- **MongoDB Caching** - Smart link caching (bypass once, use everywhere)
- **Dual Mode** - Both Webhook & Polling support
- **Flask Web Interface** - API endpoints & health checks
- **Error Reporting** - Users can report broken links (sent to admin PM)
- **Site Requests** - Users can request new site support
- **Premium Notifications** - Expiry reminders
- **Cloudflare Scraper** - Advanced protection bypass

## 📋 Commands

### User Commands
```
/start - Start the bot
/help - Show help menu
/bypass <link> or /b <link> - Bypass a link
/premium - Check premium status
/stats - View usage statistics
/refer - Get referral link
/report <link> - Report broken link
/request <site> - Request new site support
/sites - List supported sites
```

### Admin Commands
```
/broadcast <message> - Broadcast to all users
/generate_token <duration> - Generate access token (1h, 1d, 1m, 1y)
/generate_reset - Generate universal reset key
/addsite <domain> - Add supported site
/removesite <domain> - Remove site
/addgroup <group_id> - Allow bot in group
/removegroup <group_id> - Remove group permission
/ban <user_id> - Ban user
/unban <user_id> - Unban user
/set_limit <number> - Set free user limit
/toggle_referral - Enable/disable referral system
/users - View user statistics
/settings - View bot settings
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Firebase project with Firestore (free tier works!)
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- API ID & Hash from [my.telegram.org](https://my.telegram.org)

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Nova-Link-Bypasser-Bot.git
cd Nova-Link-Bypasser-Bot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
# Setup Firebase - see FIREBASE_SETUP.md
```

5. **Run the bot**
```bash
# Polling mode (local development)
python bot.py

# Webhook mode (with Flask)
python app.py
```

## 🚀 Deployment on Render

### Method 1: Using render.yaml (Recommended)

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/Nova-Link-Bypasser-Bot.git
git push -u origin main
```

2. **Deploy on Render**
- Go to [render.com](https://render.com)
- Click "New +" → "Blueprint"
- Connect your GitHub repository
- Render will automatically detect `render.yaml`
- Add environment variables in Render dashboard
- Deploy!

### Method 2: Manual Setup

1. **Create Web Service**
- Type: Web Service
- Build Command: `pip install -r requirements.txt && playwright install chromium`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 4`

2. **Create Worker Service** (Optional for polling)
- Type: Background Worker
- Build Command: `pip install -r requirements.txt && playwright install chromium`
- Start Command: `python bot.py`

3. **Add Environment Variables**
```
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
MONGODB_URI=mongodb+srv://...
OWNER_ID=your_telegram_id
WEBHOOK_MODE=true
WEBHOOK_URL=https://your-app.onrender.com
```

## 📊 Firebase Setup

### Using Firebase Firestore (Free)

1. Create Firebase project at [firebase.google.com](https://firebase.google.com)
2. Enable Firestore Database
3. Download service account credentials
4. Place `firebase-credentials.json` in project root
5. Update `FIREBASE_PROJECT_ID` in `.env`

**Detailed guide:** See [FIREBASE_SETUP.md](FIREBASE_SETUP.md)

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BOT_TOKEN` | Telegram bot token | ✅ | - |
| `API_ID` | Telegram API ID | ✅ | - |
| `API_HASH` | Telegram API Hash | ✅ | - |
| `FIREBASE_CREDENTIALS` | Path to Firebase JSON | ✅ | firebase-credentials.json |
| `FIREBASE_PROJECT_ID` | Firebase project ID | ✅ | - |
| `OWNER_ID` | Your Telegram user ID | ✅ | - |
| `ADMIN_IDS` | Comma-separated admin IDs | ❌ | - |
| `WEBHOOK_MODE` | Enable webhook mode | ❌ | false |
| `WEBHOOK_URL` | Your app URL | ⚠️ | - |
| `FREE_USER_DAILY_LIMIT` | Daily bypass limit for free users | ❌ | 10 |
| `REFERRAL_ENABLED` | Enable referral system | ❌ | true |
| `FORCE_SUB_ENABLED` | Require channel subscription | ❌ | false |

⚠️ Required only if `WEBHOOK_MODE=true`

## 🔒 Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use strong MongoDB password** - Generate random password
3. **Whitelist IPs** - Restrict MongoDB access if possible
4. **Rotate tokens** - Change bot token if compromised
5. **Admin IDs** - Keep admin list updated and secure

## 📈 Usage Statistics

The bot tracks:
- Total bypasses per user
- Daily/monthly usage
- Cache hit rate
- Premium vs Free usage
- Referral statistics

## 🐛 Troubleshooting

### Common Issues

**Bot not responding:**
- Check bot token is correct
- Verify webhook URL (if using webhook mode)
- Check MongoDB connection

**Bypass failing:**
- Check site is in supported list
- Verify Cloudflare bypass is working
- Check browser automation dependencies

**Database errors:**
- Verify Firebase credentials file exists
- Check project ID matches Firebase Console
- Ensure Firestore is enabled
- Verify network connectivity

### Logs

View logs on Render:
- Dashboard → Your Service → Logs
- Real-time log streaming
- Download historical logs

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This bot is for educational purposes only. Users are responsible for complying with website terms of service and applicable laws.

## 💬 Support

- Create an issue on GitHub
- Contact: [@YourUsername](https://t.me/yourusername)

## 🙏 Acknowledgments

Built with:
- python-telegram-bot
- Flask
- MongoDB
- Playwright
- BeautifulSoup4
- Selenium

---

Made with ❤️ by [Your Name]

**Star ⭐ this repository if you find it helpful!**
