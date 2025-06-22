import asyncio
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder, 
    CommandHandler, 
    ContextTypes, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters as TFilters
)
from app.telegram.message_templates import format_signal_alert, format_performance, format_educational_tip

logger = logging.getLogger(__name__)

# Message templates
welcome_message = '''🤖 Welcome to ProfitPro Bot!

Hi {name}! 👋

I'm your personal forex trading assistant, delivering high-quality trading signals and market analysis 24/7.

🎯 What I do:
• Send profitable forex signals
• Provide real-time market analysis  
• Offer risk management tools
• Share trading education

Let me show you around... 📊'''

features_message = '''⚡ KEY FEATURES

🔔 LIVE SIGNALS
• 5-15 signals daily
• 75%+ win rate
• Real-time notifications
• Multiple timeframes

📊 MARKET ANALYSIS
• Daily market outlook
• Currency strength meter
• Economic calendar alerts
• Technical analysis

🛡️ RISK MANAGEMENT
• Position size calculator
• Risk/reward optimization
• Stop loss suggestions
• Portfolio tracking'''

commands_message = '''🎮 **BOT COMMANDS**

**Trading & Analysis**
`/signals` - Get the latest forex signals
`/market` - View live market data
`/analysis [PAIR]` - Technical analysis for a pair
`/news` - Fetch latest forex news
`/calendar` - View economic event calendar
`/trades` - View your open/closed trades

**Calculators & Tools**
`/risk` - Calculate position size
`/pipcalc` - Calculate pip values
`/alerts` - Set price or news alerts

**Information**
`/strategies` - Learn about trading strategies
`/performance` - View bot's performance stats
`/help` - Show this command list
`/settings` - Adjust your preferences'''

plans_message = '''💎 SUBSCRIPTION PLANS

🆓 FREE PLAN (Current)
• 3 signals per day
• Basic market updates
• Standard support

⭐ PREMIUM - $29/month
• Unlimited signals
• Priority notifications
• Advanced analysis
• 1-on-1 support

💎 VIP - $99/month
• All Premium features
• Private VIP group
• Video analysis
• Direct analyst access

Type /upgrade to unlock premium features!'''

quick_start_message = '''🚀 QUICK START GUIDE

1️⃣ Set your preferences:
   /notifications - Customize alerts
   /timezone - Set your location

2️⃣ Get your first signals:
   /signals - See active signals
   /analysis - Market overview

3️⃣ Join our community:
   📢 Channel: @ForexProSignals
   💬 Chat: @ForexProChat

4️⃣ Need help?
   /help - Complete guide
   /support - Contact support

Ready to start trading? 🎯'''

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Get Signals", callback_data='signals'),
         InlineKeyboardButton("📈 Market Analysis", callback_data='analysis')],
        [InlineKeyboardButton("🔧 Tools", callback_data='tools'),
         InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
        [InlineKeyboardButton("💎 Upgrade", callback_data='upgrade'),
         InlineKeyboardButton("❓ Help", callback_data='help')],
        [InlineKeyboardButton("📢 Join Channel", url='https://t.me/ForexProSignals'),
         InlineKeyboardButton("💬 Join Chat", url='https://t.me/ForexProChat')]
    ]
    return InlineKeyboardMarkup(keyboard)

MESSAGE_DELAYS = {
    'welcome_to_features': 2,
    'features_to_commands': 3,
    'commands_to_plans': 2,
    'plans_to_guide': 3,
    'guide_to_keyboard': 2
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "Trader"
    chat_id = update.effective_chat.id
    # Message 1: Welcome
    await context.bot.send_message(chat_id=chat_id, text=welcome_message.format(name=user_name))
    await asyncio.sleep(MESSAGE_DELAYS['welcome_to_features'])
    # Message 2: Features
    await context.bot.send_message(chat_id=chat_id, text=features_message)
    await asyncio.sleep(MESSAGE_DELAYS['features_to_commands'])
    # Message 3: Commands
    await context.bot.send_message(chat_id=chat_id, text=commands_message)
    await asyncio.sleep(MESSAGE_DELAYS['commands_to_plans'])
    # Message 4: Plans
    await context.bot.send_message(chat_id=chat_id, text=plans_message)
    await asyncio.sleep(MESSAGE_DELAYS['plans_to_guide'])
    # Message 5: Quick Start
    await context.bot.send_message(chat_id=chat_id, text=quick_start_message)
    await asyncio.sleep(MESSAGE_DELAYS['guide_to_keyboard'])
    # Message 6: Interactive Keyboard
    await context.bot.send_message(chat_id=chat_id, text="Choose your next action:", reply_markup=get_main_keyboard())

async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: fetch and send latest signals
    msg = """
🤖 AI SIGNAL #2847
💱 EURUSD | 📊 TREND BREAKOUT
💰 Entry: 1.0850-1.0860
🛑 SL: 1.0830 | 🎯 TP: 1.0900
📈 R:R: 1:2.5 | ⚡ AI Confidence: 87%
🔬 Strategy: Multi-timeframe + Volume
⏰ Valid: 4 hours
"""
    await update.message.reply_text(msg)

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: send analysis for a pair
    await update.message.reply_text('Analysis for requested pair (placeholder).')

async def performance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
📊 WEEKLY PERFORMANCE
🤖 AI Trend: 12W-3L (+184 pips)
🎯 Breakout: 8W-2L (+96 pips)  
📈 Scalping: 45W-15L (+67 pips)
💰 Total: +347 pips | 🎯 78% Win Rate
"""
    await update.message.reply_text(msg)

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: position size calculator
    await update.message.reply_text('Risk calculator (placeholder).')

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: set custom price alerts
    await update.message.reply_text('Set custom price alerts (placeholder).')

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: notification preferences
    keyboard = [[InlineKeyboardButton('On', callback_data='notif_on'), InlineKeyboardButton('Off', callback_data='notif_off')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Notification preferences:', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the help message with all available commands."""
    await update.message.reply_text(commands_message)

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for showing current market data."""
    await update.message.reply_text(
        "📈 **Market Data**\n\n"
        "This command will display current bid/ask prices and daily changes for major forex pairs. (Implementation pending)"
    )

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for providing currency pair analysis."""
    pair = " ".join(context.args) if context.args else "EURUSD"
    await update.message.reply_text(
        f"🔍 **Analysis for {pair.upper()}**\n\n"
        f"This command will provide technical and fundamental analysis for the specified pair. (Implementation pending)"
    )

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for setting price or news alerts."""
    await update.message.reply_text(
        "🔔 **Set Alert**\n\n"
        "This command will allow you to set price and news alerts (e.g., `/alerts USDJPY 150.00`). (Implementation pending)"
    )

async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for displaying trades."""
    await update.message.reply_text(
        "📋 **Open/Recent Trades**\n\n"
        "This command will show your open and recent trades or allow you to log new trade ideas. (Implementation pending)"
    )

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for showing the economic calendar."""
    await update.message.reply_text(
        "📅 **Economic Calendar**\n\n"
        "This command will display upcoming high-impact economic events. (Implementation pending)"
    )

async def pipcalc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for calculating pip value."""
    await update.message.reply_text(
        "➗ **Pip Calculator**\n\n"
        "This command will calculate pip value or profit/loss for a trade. (Implementation pending)"
    )

async def strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for describing trading strategies."""
    await update.message.reply_text(
        "💡 **Trading Strategies**\n\n"
        "This command will provide information on various forex trading strategies. (Implementation pending)"
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for fetching forex news."""
    await update.message.reply_text(
        "📰 **Forex News**\n\n"
        "This command will fetch the latest forex-related news headlines. (Implementation pending)"
    )

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for calculating position size."""
    await update.message.reply_text(
        "🛡️ **Risk Calculator**\n\n"
        "This command will calculate the appropriate position size based on your risk percentage and stop loss. (Implementation pending)"
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles regular text messages."""
    await update.message.reply_text(
        "I'm a bot and I only understand commands. Please use /help to see the list of available commands."
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")

async def strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /strategy [mode]
    await update.message.reply_text('Strategy control (trend/scalp/mixed) set (placeholder).')

async def ai_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('AI mode enabled (placeholder).')

async def correlation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Pair correlation check (placeholder).')

async def market_regime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Current market regime: trending (placeholder).')

async def volatility_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Volatility analysis (placeholder).')

async def news_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Upcoming news events (placeholder).')

async def pair_strength(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Currency strength meter (placeholder).')

async def session_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Current trading session: London (placeholder).')

def setup_handlers(app: Application):
    """Sets up all the command and message handlers for the bot."""
    if not app:
        logger.warning("Application object is None, skipping handler setup.")
        return
        
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('signals', signals))
    app.add_handler(CommandHandler('performance', performance))
    app.add_handler(CommandHandler('settings', settings))

    # New Forex Commands
    app.add_handler(CommandHandler('market', market))
    app.add_handler(CommandHandler('analysis', analysis))
    app.add_handler(CommandHandler('alerts', alerts))
    app.add_handler(CommandHandler('trades', trades))
    app.add_handler(CommandHandler('calendar', calendar))
    app.add_handler(CommandHandler('pipcalc', pipcalc))
    app.add_handler(CommandHandler('strategies', strategies))
    app.add_handler(CommandHandler('risk', risk))

    # Existing Commands
    app.add_handler(CommandHandler('strategy', strategy))
    app.add_handler(CommandHandler('ai_mode', ai_mode))
    app.add_handler(CommandHandler('correlation', correlation))
    app.add_handler(CommandHandler('market_regime', market_regime))
    app.add_handler(CommandHandler('volatility_report', volatility_report))
    app.add_handler(CommandHandler('news_calendar', news_calendar))
    app.add_handler(CommandHandler('pair_strength', pair_strength))
    app.add_handler(CommandHandler('session_info', session_info))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(TFilters.TEXT & ~TFilters.COMMAND, handle_text_message)) 