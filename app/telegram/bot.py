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
from app.services.api_service import api_service, ApiService # Import the instance and class

logger = logging.getLogger(__name__)

# --- Message Templates ---
welcome_message = '''🤖 Welcome to ProfitPro Bot!
Hi {name}! 👋 I'm your personal forex trading assistant. All features are 100% free.
Use /help to see what I can do.'''

commands_message = '''🎮 **BOT COMMANDS**

**Trading & Analysis**
`/signals` - Get the latest forex signals
`/market [PAIR]` - View live market data (e.g., `/market EURUSD`)
`/analysis [PAIR]` - Technical analysis for a pair
`/trades` - View your trade history

**Calculators & Tools**
`/risk [PAIR] [RISK%] [SL PIPS]` - Calculate position size
`/pipcalc [PAIR] [SIZE]` - Calculate pip values

**Information**
`/strategies` - Learn about our strategies
`/donate` - Support the bot
`/help` - Show this command list

💡 **Tips:**
• Use `/risk` or `/pipcalc` without parameters for help
• All commands support major currency pairs
• Risk % should be 0.1-5% for safety'''

donation_message = '''❤️ **Enjoying the Bot?**
This bot is, and always will be, 100% free. If you find it valuable, please consider supporting its development with a donation.
**[Link to your donation page/address]**'''

# --- Keyboards ---
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Signals", callback_data='signals'), InlineKeyboardButton("📈 Market", callback_data='market_menu')],
        [InlineKeyboardButton("🔧 Tools", callback_data='tools_menu'), InlineKeyboardButton("❓ Help", callback_data='help')],
        [InlineKeyboardButton("❤️ Donate", callback_data='donate')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Command Handlers (Frontend Logic Only) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "Trader"
    await update.message.reply_text(
        welcome_message.format(name=user_name),
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(commands_message, parse_mode='Markdown')

async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send loading message
    loading_msg = await update.message.reply_text("🔄 Fetching latest signals...")
    
    try:
        response_data = await api_service.make_api_call("/api/signals")
        
        if not response_data:
            await loading_msg.edit_text("😕 Could not fetch signals. The server might be down. Please try again later.")
            return
        
        formatted_signals = "📊 **Latest Trading Signals**\n\n"
        for signal in response_data:
            formatted_signals += (
                f"🔹 **{signal['pair']}** ({signal['strategy']})\n"
                f"   Entry: `{signal['entry_range']}` | SL: `{signal['stop_loss']}` | TP: `{signal['take_profit']}`\n"
                f"   Confidence: **{signal['confidence']}** | R:R: `{signal['risk_reward_ratio']}`\n\n"
            )
        
        formatted_signals += "✅ *Signals updated*"
        await loading_msg.edit_text(formatted_signals, parse_mode='Markdown')
        
    except Exception as e:
        error_msg = "❌ Could not fetch signals. Please try again later."
        if "timeout" in str(e).lower():
            error_msg = "⚠️ Connection timeout - please try again in a few seconds"
        elif "404" in str(e):
            error_msg = "📊 No signals available at the moment"
        
        await loading_msg.edit_text(error_msg)

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify a currency pair. Example: `/market EURUSD`")
        return
    
    pair = context.args[0].upper()
    
    # Send loading message
    loading_msg = await update.message.reply_text(f"🔄 Fetching market data for {pair}...")
    
    try:
        data = await api_service.make_api_call(f"/api/market/{pair}")
        
        if not data:
            await loading_msg.edit_text(f"📉 Sorry, market data for **{pair}** is currently unavailable.")
            return

        response_text = (
            f"📈 **Market Data for {data['pair']}**\n\n"
            f"**Price:** `{data['price']:,.5f}`\n"
            f"**Open:** `{data.get('open', 'N/A'):,.5f}`\n"
            f"**Day's High:** `{data.get('high', 'N/A'):,.5f}`\n"
            f"**Day's Low:** `{data.get('low', 'N/A'):,.5f}`\n\n"
            f"✅ *Data updated*"
        )
        
        await loading_msg.edit_text(response_text, parse_mode='Markdown')
        
    except Exception as e:
        error_msg = f"❌ Could not fetch market data for {pair}. Please try again later."
        if "timeout" in str(e).lower():
            error_msg = "⚠️ Connection timeout - please try again in a few seconds"
        elif "404" in str(e):
            error_msg = f"❌ Currency pair {pair} not supported"
        
        await loading_msg.edit_text(error_msg)

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify a currency pair. Example: `/analysis EURUSD`")
        return
    
    pair = context.args[0].upper()
    
    # Get market data for analysis
    data = await api_service.make_api_call(f"/api/market/{pair}")
    if not data:
        await update.message.reply_text(f"📉 Sorry, market data for **{pair}** is currently unavailable.")
        return

    # Simple technical analysis based on available data
    price = data.get('price', 0)
    high = data.get('high', price)
    low = data.get('low', price)
    open_price = data.get('open', price)
    
    # Calculate basic indicators
    daily_range = high - low if high and low else 0
    price_change = price - open_price if open_price else 0
    price_change_pct = (price_change / open_price * 100) if open_price else 0
    
    # Determine trend
    if price_change > 0:
        trend = "🟢 BULLISH"
        trend_emoji = "📈"
    elif price_change < 0:
        trend = "🔴 BEARISH"
        trend_emoji = "📉"
    else:
        trend = "🟡 NEUTRAL"
        trend_emoji = "➡️"
    
    analysis_text = (
        f"📊 **Technical Analysis: {pair}**\n\n"
        f"**Current Price:** `{price:,.5f}`\n"
        f"**Daily Range:** `{daily_range:,.5f}`\n"
        f"**Price Change:** `{price_change:,.5f}` ({price_change_pct:+.2f}%)\n"
        f"**Trend:** {trend_emoji} {trend}\n\n"
        f"**Support:** `{low:,.5f}`\n"
        f"**Resistance:** `{high:,.5f}`\n\n"
        f"💡 *This is a basic analysis. For advanced indicators, use our web platform.*"
    )
    
    await update.message.reply_text(analysis_text, parse_mode='Markdown')

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        help_text = (
            "💡 **Risk Calculator Help:**\n\n"
            "**Format:** `/risk [pair] [risk%] [stop loss pips]`\n"
            "**Example:** `/risk EURUSD 2 50`\n\n"
            "**Examples:**\n"
            "• `/risk EURUSD 1 30` - 1% risk, 30 pip stop loss\n"
            "• `/risk GBPJPY 2.5 45` - 2.5% risk, 45 pip stop loss\n"
            "• `/risk USDJPY 1.5 25` - 1.5% risk, 25 pip stop loss\n\n"
            "💡 *Tip: Risk percentage should be 0.1-5% for safety*"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    pair, risk_percent_str, sl_pips_str = context.args[0], context.args[1], context.args[2]
    
    # Validate inputs
    try:
        risk_percent = float(risk_percent_str)
        sl_pips = float(sl_pips_str)
    except ValueError:
        await update.message.reply_text("❌ Invalid numbers. Please use valid numbers for risk % and stop loss pips.")
        return
    
    if risk_percent <= 0 or risk_percent > 10:
        await update.message.reply_text("⚠️ Risk percentage should be between 0.1% and 10% for safety.")
        return
    
    if sl_pips <= 0:
        await update.message.reply_text("❌ Stop loss pips must be greater than 0.")
        return
    
    # Send loading message
    loading_msg = await update.message.reply_text("🔄 Calculating position size...")
    
    try:
        data = await api_service.make_api_call(f"/api/risk/{pair}/{risk_percent}/{sl_pips}")
        
        if not data or "error" in data:
            error_msg = data.get("error", "😕 Calculation failed. Please check your inputs or try again.")
            await loading_msg.edit_text(f"❌ {error_msg}")
            return
        
        response = (
            f"🛡️ **Risk Calculation**\n\n"
            f"💰 **Account Balance:** `${data['account_balance']:,.2f}`\n"
            f"📈 **Risk:** `{data['risk_percent']}%` (${data['risk_amount_usd']:,.2f})\n"
            f"📉 **Stop-Loss:** `{data['stop_loss_pips']}` pips\n\n"
            f"**Recommended Position Size for {data['pair']}:**\n"
            f"✅ **`{data['position_size_lots']:.2f}` lots**\n\n"
            f"💡 *This position size ensures you risk exactly {data['risk_percent']}% of your account*"
        )
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        error_msg = "❌ Could not calculate position size. Please try again later."
        if "timeout" in str(e).lower():
            error_msg = "⚠️ Calculation timeout - please try again"
        elif "404" in str(e):
            error_msg = "❌ Currency pair not supported"
        
        await loading_msg.edit_text(error_msg)

async def pipcalc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        help_text = (
            "📏 **Pip Calculator Help:**\n\n"
            "**Format:** `/pipcalc [pair] [trade size]`\n"
            "**Examples:**\n"
            "• `/pipcalc EURUSD 1` - 1 lot\n"
            "• `/pipcalc GBPJPY 0.5` - 0.5 lots\n"
            "• `/pipcalc USDJPY 0.1` - 0.1 lots\n\n"
            "💡 *Trade size is in lots (1 lot = 100,000 units)*"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    pair = context.args[0].upper()
    try:
        trade_size = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid trade size. Please enter a valid number.")
        return
    
    if trade_size <= 0:
        await update.message.reply_text("❌ Trade size must be greater than 0.")
        return
    
    # Send loading message
    loading_msg = await update.message.reply_text("🔄 Calculating pip value...")
    
    try:
        data = await api_service.make_api_call(f"/api/pipcalc/{pair}/{trade_size}")
        
        if not data:
            await loading_msg.edit_text("❌ Could not calculate pip value. Please check your inputs or try again.")
            return
        
        # Calculate additional pip values for common scenarios
        pip_value = data['pip_value_usd']
        ten_pips = pip_value * 10
        fifty_pips = pip_value * 50
        hundred_pips = pip_value * 100
        
        response = (
            f"💰 **Pip Calculator**\n\n"
            f"**Pair:** `{data['pair']}`\n"
            f"**Trade Size:** `{data['trade_size']}` lots\n"
            f"**Pip Value:** `${pip_value:.2f}` USD\n\n"
            f"**Common Scenarios:**\n"
            f"• 10 pips = `${ten_pips:.2f}`\n"
            f"• 50 pips = `${fifty_pips:.2f}`\n"
            f"• 100 pips = `${hundred_pips:.2f}`\n\n"
            f"💡 *This is the value of 1 pip movement for your position*"
        )
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        error_msg = "❌ Could not calculate pip value. Please try again later."
        if "timeout" in str(e).lower():
            error_msg = "⚠️ Calculation timeout - please try again"
        elif "404" in str(e):
            error_msg = "❌ Currency pair not supported"
        
        await loading_msg.edit_text(error_msg)

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(donation_message, parse_mode='Markdown', disable_web_page_preview=True)
    
async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send loading message
    loading_msg = await update.message.reply_text("🔄 Fetching trade history...")
    
    try:
        data = await api_service.make_api_call("/api/trades")
        
        if not data:
            await loading_msg.edit_text("📊 No trades found in your history.")
            return
        
        response = "📊 **Recent Trades**\n\n"
        for trade in data[:10]:  # Show last 10 trades
            status_emoji = "🟢" if trade.status == "closed" else "🟡"
            response += (
                f"{status_emoji} **{trade.symbol}** ({trade.order_type.upper()})\n"
                f"   Entry: `{trade.entry_price}` | Status: `{trade.status}`\n"
            )
            if trade.close_price:
                response += f"   Exit: `{trade.close_price}` | P&L: `${trade.pnl:.2f}`\n"
            response += "\n"
        
        response += "✅ *Trade history updated*"
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        error_msg = "❌ Could not fetch trade history. Please try again later."
        if "timeout" in str(e).lower():
            error_msg = "⚠️ Connection timeout - please try again in a few seconds"
        elif "404" in str(e):
            error_msg = "📊 No trade history available yet"
        elif "401" in str(e):
            error_msg = "🔒 Authentication required - please reconnect your account"
        
        await loading_msg.edit_text(error_msg)

async def strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await api_service.make_api_call("/api/strategies")
    if not data:
        await update.message.reply_text("😕 Could not fetch strategies. Please try again later.")
        return
    
    response = "📚 **Trading Strategies**\n\n"
    for strategy in data['strategies']:
        response += f"• **{strategy}**\n"
    
    response += f"\n{data['message']}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()

    COMMAND_MAP = {
        'signals': signals,
        'market_menu': lambda u,c: u.message.reply_text("To get market data, use the command: `/market [PAIR]`"),
        'tools_menu': lambda u,c: u.message.reply_text("Available tools:\n`/risk [PAIR] [RISK%] [SL PIPS]`\n`/pipcalc [PAIR] [SIZE]`"),
        'donate': donate,
        'help': help_command,
    }
    
    if query.data in COMMAND_MAP:
        # We pass the original update object to the command functions
        await COMMAND_MAP[query.data](query, context)
    else:
        await query.edit_message_text(text=f"Coming soon: {query.data}")

def setup_handlers(app: Application):
    """Sets up all the command and message handlers for the bot."""
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('signals', signals))
    app.add_handler(CommandHandler('market', market))
    app.add_handler(CommandHandler('analysis', analysis))
    app.add_handler(CommandHandler('risk', risk))
    app.add_handler(CommandHandler('pipcalc', pipcalc))
    app.add_handler(CommandHandler('donate', donate))
    app.add_handler(CommandHandler('trades', trades))
    app.add_handler(CommandHandler('strategies', strategies))
    app.add_handler(CallbackQueryHandler(button))