import asyncio
import os
import logging
import feedparser
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
from sqlalchemy.orm import Session
from app.services.database_service import get_db, get_or_create_user
from app.services.forex_api_service import forex_api_service

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

async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the user's open and closed trades."""
    with get_db() as db:
        user = get_or_create_user(db, update.effective_user.id)
        trades_data = db.query(Trade).filter(Trade.user_id == user.id).order_by(Trade.created_at.desc()).limit(20).all()
    
    if not trades_data:
        response = "📊 **Your Trades**\n\nYou have no trades yet. Use `/signals` to find opportunities!"
    else:
        open_trades = []
        closed_trades = []
        for t in trades_data:
            trade_line = f"🔹 **{t.symbol}** ({t.order_type.title()})\n" \
                         f"   Entry: `{t.entry_price}` | SL: `{t.stop_loss}` | TP: `{t.take_profit}`"
            if t.status == 'open':
                open_trades.append(trade_line)
            else:
                pnl_str = f"| PnL: `${t.pnl:,.2f}`" if t.pnl is not None else ""
                closed_trades.append(f"{trade_line}\n   Closed at `{t.close_price}` {pnl_str}")

        response = "📊 **Your Trades**\n\n"
        if open_trades:
            response += "🔴 **Open Trades**\n" + "\n".join(open_trades) + "\n\n"
        if closed_trades:
            response += "🟢 **Closed Trades**\n" + "\n".join(closed_trades)
        
    await update.message.reply_text(response, parse_mode='Markdown')

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
    """Provides a basic technical analysis for a given currency pair."""
    if not context.args:
        await update.message.reply_text("Please specify a currency pair. Example: `/analysis EURUSD`")
        return

    pair = context.args[0].upper()
    data = await forex_api_service.get_market_data(pair)

    if not data or not data.get('price'):
        await update.message.reply_text(f"📉 Sorry, analysis for **{pair}** is currently unavailable. Please check the pair and try again.")
        return

    price = data['price']
    open_price = data['open']
    high = data['high']
    low = data['low']

    trend = "Sideways"
    if price > open_price * 1.001:
        trend = "Uptrend"
    elif price < open_price * 0.999:
        trend = "Downtrend"

    response = (
        f"📊 **Technical Analysis for {pair}**\n\n"
        f"**Current Price:** `{price:,.5f}`\n\n"
        f"**Session Analysis:**\n"
        f"  - **Trend:** `{trend}`\n"
        f"  - **Open:** `{open_price:,.5f}`\n"
        f"  - **High:** `{high:,.5f}`\n"
        f"  - **Low:** `{low:,.5f}`\n\n"
        f"**Summary:**\n"
        f"The market for {pair} is currently in a **{trend.lower()}** phase. "
        f"The price is trading at `{price:,.5f}`, with a daily range between `{low:,.5f}` and `{high:,.5f}`."
    )
    await update.message.reply_text(response, parse_mode='Markdown')

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
    """Calculates position size based on risk percentage and stop-loss."""
    try:
        if len(context.args) != 3:
            await update.message.reply_text("❌ Invalid format. Use: `/risk [pair] [risk %] [stop-loss pips]`\n\nExample: `/risk EURUSD 2 20`")
            return
        
        pair, risk_percent, stop_loss_pips = context.args[0].upper(), float(context.args[1]), float(context.args[2])
        if risk_percent <= 0 or stop_loss_pips <= 0:
            await update.message.reply_text("❌ Risk and stop-loss must be positive numbers.")
            return

        with get_db() as db:
            user = get_or_create_user(db, update.effective_user.id)
            account_balance = user.account_balance  # Fetch real balance

        pip_value_per_lot = await forex_api_service.get_pip_value_in_usd(pair, 100000) # 1 standard lot

        if pip_value_per_lot is None:
            await update.message.reply_text("❌ Could not calculate pip value. Please check the currency pair or try again later.")
            return

        risk_amount_usd = account_balance * (risk_percent / 100)
        sl_cost_per_lot = stop_loss_pips * pip_value_per_lot
        
        if sl_cost_per_lot == 0:
            await update.message.reply_text("❌ Stop loss cost cannot be zero. Please check your inputs.")
            return
            
        position_size_lots = risk_amount_usd / sl_cost_per_lot
        
        response = (
            f"🛡️ **Risk Calculation**\n\n"
            f"💰 Account Balance: `${account_balance:,.2f}`\n"
            f"📈 Risk: `{risk_percent}%` (${risk_amount_usd:,.2f})\n"
            f"📉 Stop-Loss: `{stop_loss_pips}` pips\n\n"
            f"**Recommended Position Size for {pair}:**\n"
            f"✅ **`{position_size_lots:.2f}` lots**"
        )
        await update.message.reply_text(response, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ Invalid input. Please use numbers for risk and stop-loss.\n\nExample: `/risk EURUSD 2 20`")
    except Exception as e:
        logger.error(f"Error in /risk command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

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
    await update.message.reply_text(commands_message, parse_mode='Markdown')

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and displays live market data for a given currency pair."""
    if not context.args:
        await update.message.reply_text("Please specify a currency pair. Example: `/market EURUSD`")
        return

    pair = context.args[0].upper()
    data = await forex_api_service.get_market_data(pair)
    
    if not data or not data.get('price'):
        await update.message.reply_text(f"📉 Sorry, market data for **{pair}** is currently unavailable. Please check the pair and try again.")
        return

    response = (
        f"📈 **Market Data for {data['pair']}**\n\n"
        f"**Price:** `{data['price']:,.5f}`\n"
        f"**Open:** `{data['open']:,.5f}`\n"
        f"**Day's High:** `{data['high']:,.5f}`\n"
        f"**Day's Low:** `{data['low']:,.5f}`\n"
        f"**Volume:** `{data['volume']:,}`\n\n"
        f"**52-Week Range:**\n`{data['low_52wk']:,.5f}` - `{data['high_52wk']:,.5f}`"
    )
        
    await update.message.reply_text(response, parse_mode='Markdown')

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: show economic event calendar
    await update.message.reply_text('📅 Economic calendar feature is coming soon! It will include events from major economies.')

async def pipcalc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculates the value of pips for a given pair and lot size."""
    try:
        if len(context.args) != 3:
            await update.message.reply_text("❌ Invalid format. Use: `/pipcalc [pair] [lot size] [pips]`\n\nExample: `/pipcalc EURUSD 1.0 50`")
            return

        pair, lot_size_str, pips_str = context.args[0].upper(), context.args[1], context.args[2]
        lot_size = float(lot_size_str)
        pips = float(pips_str)

        if lot_size <= 0 or pips <= 0:
            await update.message.reply_text("❌ Lot size and pips must be positive numbers.")
            return

        # lot_size is in lots, convert to currency units (1 lot = 100,000 units)
        trade_size_units = lot_size * 100000

        pip_value_usd = await forex_api_service.get_pip_value_in_usd(pair, trade_size_units)

        if pip_value_usd is None:
            await update.message.reply_text("❌ Could not calculate pip value. Please check the currency pair or try again later.")
            return
        
        total_value = pip_value_usd * pips
        
        response = (
            f"🧮 **Pip Value Calculation**\n\n"
            f"PAIR: `{pair}`\n"
            f"LOT SIZE: `{lot_size}`\n"
            f"PIPS: `{pips}`\n\n"
            f"Pip Value (1 pip): **${pip_value_usd / lot_size:.5f}** per mini lot (0.1)\n"
            f"Total Value: **${total_value:,.2f}** for `{pips}` pips"
        )

        await update.message.reply_text(response, parse_mode='Markdown')

    except ValueError:
        await update.message.reply_text("❌ Invalid input. Please use numbers for lot size and pips.\n\nExample: `/pipcalc EURUSD 1.0 50`")
    except Exception as e:
        logger.error(f"Error in /pipcalc command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

async def strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: explain trading strategies
    response = (
        "📈 **Trading Strategies**\n\n"
        "This bot uses a combination of strategies to generate signals:\n\n"
        "1.  **Trend Following:** Identifies and follows the dominant market trend using moving averages.\n"
        "2.  **Mean Reversion:** Looks for prices to return to their historical average.\n"
        "3.  **Breakout:** Enters the market when the price moves beyond a defined support or resistance level.\n\n"
        "Each signal specifies the strategy used."
    )
    await update.message.reply_text(response)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches the latest forex news from an RSS feed."""
    try:
        # Using DailyFX RSS feed as an example
        feed_url = "https://www.dailyfx.com/feeds/forex-news"
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            await update.message.reply_text("Couldn't fetch forex news at the moment. Please try again later.")
            return

        response = "📰 **Latest Forex News**\n\n"
        for entry in feed.entries[:5]: # Get latest 5 articles
            response += f"▪️ <a href='{entry.link}'>{entry.title}</a>\n"
        
        await update.message.reply_text(response, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        await update.message.reply_text("An error occurred while fetching the news.")

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
    await update.message.reply_text('Session info (placeholder).')

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