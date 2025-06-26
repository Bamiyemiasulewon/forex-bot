import asyncio
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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
import httpx
import telebot
from app.security.credential_manager import CredentialManager
from app.mt5.mt5_manager import MT5Manager

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

# --- Personal Menu Keyboard ---
def create_personalized_keyboard(user_id):
    # Final: Only show the current, correct buttons
    keyboard = [
        [InlineKeyboardButton("📈 My Signals", callback_data="my_signals:view:all")],
        [InlineKeyboardButton("📋 My Trades", callback_data="my_trades:filter:all"), InlineKeyboardButton("📜 Commands", callback_data="my_commands:view:all")],
        [InlineKeyboardButton("⚙️ My Settings", callback_data="my_settings:view:main"), InlineKeyboardButton("📞 Get Help", callback_data="my_help:contact:direct")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="my_refresh:action:now"), InlineKeyboardButton("❌ Close", callback_data="my_menu:close:main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Persistent Reply Keyboard ---
def get_reply_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📋 Menu")]], resize_keyboard=True, one_time_keyboard=False
    )

# --- User Preferences (Stub) ---
def get_user_preferences(user_id):
    # TODO: Replace with real DB lookup
    return {"risk_profile": "medium", "trading_style": "swing"}

def update_user_activity(user_id, action):
    # TODO: Log user activity to DB
    pass

# --- Send Personal Message ---
def send_personal_message(chat_id, text, keyboard, context):
    return context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode='Markdown')

# --- Show Personal Menu ---
async def show_personal_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Trader"
    prefs = get_user_preferences(user_id)
    menu_text = f"""👋 Hi {user_name}!!\n\nWelcome to your *Personal Forex Assistant Menu*.\n\nSelect an option below to manage your trading or get help.\n\n*Your risk profile:* {prefs.get('risk_profile', 'N/A')}\n*Trading style:* {prefs.get('trading_style', 'N/A')}\n"""
    keyboard = create_personalized_keyboard(user_id)
    if update.message:
        await update.message.reply_text(menu_text, reply_markup=keyboard, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(menu_text, reply_markup=keyboard, parse_mode='Markdown')

# --- Handle Personal Menu Callbacks ---
async def handle_personal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()
    update_user_activity(user_id, data)
    try:
        action, type_, param = data.split(":", 2)
    except ValueError:
        await query.edit_message_text("❌ Invalid action.")
        return
    loading_msg = "⏳ Loading your data..."

    async def safe_api_call(endpoint, retries=1):
        for attempt in range(retries + 1):
            try:
                logger.info(f"Making API call: {endpoint} (attempt {attempt+1})")
                return await api_service.make_api_call(endpoint)
            except httpx.TimeoutException:
                logger.warning(f"Timeout on {endpoint} (attempt {attempt+1})")
                if attempt == retries:
                    return 'timeout'
            except httpx.RequestError as e:
                logger.error(f"Request error on {endpoint}: {e}")
                return 'request_error'
            except Exception as e:
                logger.error(f"General error on {endpoint}: {e}")
                return str(e)
        return None

    if action == "my_signals":
        await query.edit_message_text(loading_msg)
        result = await safe_api_call("/api/signals", retries=1)
        if result == 'timeout':
            await query.edit_message_text("⏳ The signal service is taking too long to respond. Please try again in a few minutes.")
            return
        if result == 'request_error':
            await query.edit_message_text("🌐 Could not connect to the signal service. Please check your connection and try again.")
            return
        if isinstance(result, str):
            await query.edit_message_text(f"❌ Error fetching signals: {result}")
            return
        response_data = result
        if not response_data:
            await query.edit_message_text("📈 No signals available at the moment.")
            return
        formatted_signals = "📈 *Your Personalized Signals*\n\n"
        for signal in response_data:
            formatted_signals += (
                f"🔹 *{signal['pair']}* ({signal['strategy']})\n"
                f"   Entry: `{signal['entry_range']}` | SL: `{signal.get('stop_loss', 'N/A')}` | TP: `{signal.get('take_profit', 'N/A')}`\n"
                f"   Confidence: *{signal['confidence']}* | R:R: `{signal.get('risk_reward_ratio', 'N/A')}`\n\n"
            )
        formatted_signals += "✅ *Signals updated*"
        await query.edit_message_text(formatted_signals, parse_mode='Markdown')
    elif action == "my_trades":
        await query.edit_message_text(loading_msg)
        result = await safe_api_call("/api/trades", retries=1)
        if result == 'timeout':
            await query.edit_message_text("⏳ The trade history service is taking too long to respond. Please try again in a few minutes.")
            return
        if result == 'request_error':
            await query.edit_message_text("🌐 Could not connect to the trade history service. Please check your connection and try again.")
            return
        if isinstance(result, str):
            await query.edit_message_text(f"❌ Error fetching trade history: {result}")
            return
        data = result
        if not data:
            await query.edit_message_text("📋 No trades found in your history.")
            return
        response = "📋 *Your Trade History*\n\n"
        for trade in data[:10]:
            status_emoji = "🟢" if trade.get('status') == "closed" else "🟡"
            response += (
                f"{status_emoji} *{trade.get('symbol', 'N/A')}* ({trade.get('order_type', '').upper()})\n"
                f"   Entry: `{trade.get('entry_price', 'N/A')}` | Status: `{trade.get('status', 'N/A')}`\n"
            )
            if trade.get('close_price'):
                response += f"   Exit: `{trade.get('close_price')}` | P&L: `${trade.get('pnl', 0):.2f}`\n"
            response += "\n"
        response += "✅ *Trade history updated*"
        await query.edit_message_text(response, parse_mode='Markdown')
    elif action == "my_commands":
        commands_list = (
            "\n".join([
                "`/signals` - Get the latest forex signals",
                "`/market [PAIR]` - View live market data (e.g., `/market EURUSD`)",
                "`/analysis [PAIR]` - Technical analysis for a pair",
                "`/trades` - View your trade history",
                "`/risk [PAIR] [RISK%] [SL PIPS]` - Calculate position size",
                "`/pipcalc [PAIR] [SIZE]` - Calculate pip values",
                "`/strategies` - Learn about our strategies",
                "`/donate` - Support the bot",
                "`/help` - Show this command list"
            ])
        )
        await query.edit_message_text(f"📜 *Available Commands*\n\n{commands_list}", parse_mode='Markdown')
    elif action == "my_settings":
        await query.edit_message_text(loading_msg)
        result = await safe_api_call(f"/api/settings?telegram_id={user_id}", retries=1)
        if result == 'timeout':
            await query.edit_message_text("⏳ The settings service is taking too long to respond. Please try again in a few minutes.")
            return
        if result == 'request_error':
            await query.edit_message_text("🌐 Could not connect to the settings service. Please check your connection and try again.")
            return
        if isinstance(result, str):
            await query.edit_message_text(f"❌ Error fetching settings: {result}")
            return
        data = result
        if not data:
            await query.edit_message_text("⚙️ No settings found for your account.")
            return
        settings_text = (
            f"⚙️ *Your Settings*\n\n"
            f"Preferred pairs: `{data.get('preferred_pairs', 'N/A')}`\n"
            f"Default risk: `{data.get('default_risk', 'N/A')}%`"
        )
        await query.edit_message_text(settings_text, parse_mode='Markdown')
    elif action == "my_help":
        await query.edit_message_text(loading_msg)
        result = await safe_api_call(f"/api/help?telegram_id={user_id}", retries=1)
        if result == 'timeout':
            await query.edit_message_text("⏳ The help service is taking too long to respond. Please try again in a few minutes.")
            return
        if result == 'request_error':
            await query.edit_message_text("🌐 Could not connect to the help service. Please check your connection and try again.")
            return
        if isinstance(result, str):
            await query.edit_message_text(f"❌ Error fetching help info: {result}")
            return
        data = result
        if not data or 'message' not in data:
            await query.edit_message_text("❓ No help info found.")
            return
        await query.edit_message_text(f"📞 {data['message']}", parse_mode='Markdown')
    elif action == "my_refresh":
        await show_personal_menu(update, context)
    elif action == "my_menu" and type_ == "close":
        await query.edit_message_text("❌ Menu closed. Type /menu to open again.")
    else:
        await query.edit_message_text("❓ This feature is coming soon!")

# --- Command Handlers (Frontend Logic Only) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "Trader"
    await update.message.reply_text(
        welcome_message.format(name=user_name),
        reply_markup=get_reply_keyboard()
    )
    await show_personal_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_personal_menu(update, context)

async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send loading message
    loading_msg = await update.message.reply_text("🔄 Fetching latest signals...")
    
    try:
        response_data = await api_service.make_api_call("/api/signals")
        
        # This part will now only be reached on success (200 OK)
        formatted_signals = "📊 **Latest Trading Signals**\n\n"
        for signal in response_data:
            formatted_signals += (
                f"🔹 **{signal['pair']}** ({signal['strategy']})\n"
                f"   Entry: `{signal['entry_range']}` | SL: `{signal.get('stop_loss', 'N/A')}` | TP: `{signal.get('take_profit', 'N/A')}`\n"
                f"   Confidence: **{signal['confidence']}** | R:R: `{signal.get('risk_reward_ratio', 'N/A')}`\n\n"
            )
        
        formatted_signals += "✅ *Signals updated*"
        await loading_msg.edit_text(formatted_signals, parse_mode='Markdown')
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await loading_msg.edit_text("📊 No new signals found. The market is quiet. Check back later!")
        elif e.response.status_code == 503:
            await loading_msg.edit_text("⚠️ The signal service is temporarily unavailable. Please try again in a few minutes.")
        else:
            await loading_msg.edit_text("❌ A server error occurred. Please try again later.")
    except httpx.RequestError:
        await loading_msg.edit_text("🌐 Could not connect to the server. Please check your connection and try again.")
    except Exception:
        await loading_msg.edit_text("An unexpected error occurred. Please try again.")

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

    loading_msg = await update.message.reply_text("🔄 Calculating pip value...")

    try:
        data = await api_service.make_api_call(f"/api/pipcalc/{pair}/{trade_size}")
        if not data or "error" in data:
            error_msg = data.get("error", "Could not calculate pip value.")
            await loading_msg.edit_text(f"❌ {error_msg}")
            return

        pip_value = data['pip_value_usd']
        contract_size = trade_size * 100000

        pip_movements = {
            "1 pip": pip_value * 1,
            "5 pips": pip_value * 5,
            "10 pips": pip_value * 10,
            "20 pips": pip_value * 20,
            "50 pips": pip_value * 50,
            "100 pips": pip_value * 100,
        }
        
        table = "\n".join([f"• {pips} = ${value:,.2f}" for pips, value in pip_movements.items()])

        response = (
            f"📏 **Pip Calculator - {data['pair']}**\n\n"
            f"💰 **Trade Size:** `{data['trade_size']}` lots ({int(contract_size):,} units)\n"
            f"📊 **Pip Value:** `${pip_value:,.2f}`\n\n"
            f"**Pip Movement Table:**\n{table}\n\n"
            f"💡 *Each pip movement is worth ${pip_value:,.2f} of profit or loss.*"
        )

        await loading_msg.edit_text(response, parse_mode='Markdown')

    except Exception as e:
        await loading_msg.edit_text("❌ An unexpected error occurred. Please try again.")

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

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_personal_menu(update, context)

async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_personal_menu(update, context)

# --- Persistent Reply Keyboard Handler ---
async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📋 Menu":
        await show_personal_menu(update, context)

# --- Button Handler (Route to Personal or Old) ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("my_"):
        await handle_personal_callback(update, context)
        return
    await query.answer()
    COMMAND_MAP = {
        'signals': signals,
        'market_menu': lambda u,c: u.message.reply_text("To get market data, use the command: `/market [PAIR]`"),
        'tools_menu': lambda u,c: u.message.reply_text("Available tools:\n`/risk [PAIR] [RISK%] [SL PIPS]`\n`/pipcalc [PAIR] [SIZE]`"),
        'donate': donate,
        'help': help_command,
    }
    if query.data in COMMAND_MAP:
        await COMMAND_MAP[query.data](query, context)
    else:
        await query.edit_message_text(text=f"Coming soon: {query.data}")

def setup_handlers(app: Application):
    """Sets up all the command and message handlers for the bot."""
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CommandHandler('commands', commands_command))
    app.add_handler(CommandHandler('signals', signals))
    app.add_handler(CommandHandler('market', market))
    app.add_handler(CommandHandler('analysis', analysis))
    app.add_handler(CommandHandler('risk', risk))
    app.add_handler(CommandHandler('pipcalc', pipcalc))
    app.add_handler(CommandHandler('donate', donate))
    app.add_handler(CommandHandler('trades', trades))
    app.add_handler(CommandHandler('strategies', strategies))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(TFilters.TEXT & (~TFilters.COMMAND), reply_keyboard_handler))

bot = telebot.TeleBot(os.getenv("TELEGRAM_FOREX_BOT_TOKEN"))
cred_mgr = CredentialManager("forex_bot.db", "eKnjQbB073B0TfMthgsOzoGPo9w1xjgBOM-eWl8hGq4=")
mt5_mgr = MT5Manager()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome! Use /connect to link your MT5 account.")

@bot.message_handler(commands=['connect'])
def connect(message):
    # Placeholder: In production, ask for login, password, server interactively
    bot.send_message(message.chat.id, "Please send your MT5 login, password, and server (format: login,password,server)")
    bot.register_next_step_handler(message, process_credentials)

def process_credentials(message):
    try:
        login, password, server = message.text.split(",")
        cred_mgr.store_credentials(message.from_user.id, login, password, server)
        success, msg = mt5_mgr.connect(message.from_user.id, login, password, server)
        if success:
            bot.send_message(message.chat.id, "Connected to your MT5 account!")
        else:
            bot.send_message(message.chat.id, f"Connection failed: {msg}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

@bot.message_handler(commands=['account'])
def account(message):
    creds = cred_mgr.get_credentials(message.from_user.id)
    if not creds:
        bot.send_message(message.chat.id, "No credentials found. Use /connect first.")
        return
    if not mt5_mgr.is_connected(message.from_user.id):
        bot.send_message(message.chat.id, "Not connected. Use /connect.")
        return
    # Placeholder: Fetch and display account info from MT5
    bot.send_message(message.chat.id, "[Account info will be shown here]")

@bot.message_handler(commands=['disconnect'])
def disconnect(message):
    mt5_mgr.disconnect(message.from_user.id)
    bot.send_message(message.chat.id, "Disconnected from MT5 account.")

@bot.message_handler(commands=['status'])
def status(message):
    connected = mt5_mgr.is_connected(message.from_user.id)
    bot.send_message(message.chat.id, f"MT5 connection status: {'Connected' if connected else 'Not connected'}")

if __name__ == "__main__":
    bot.polling()