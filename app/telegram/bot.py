import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import asyncio
import logging
import socket
import time
import tracemalloc
import signal

# Enable tracemalloc for debugging memory leaks
tracemalloc.start()

# --- Session Management for Multi-step Commands ---
class SessionManager:
    def __init__(self):
        self.sessions = {}  # user_id -> session_data
        self.timeout = 120  # 2 minutes timeout
    
    def create_session(self, user_id: int, session_type: str):
        """Create a new session for a user."""
        self.sessions[user_id] = {
            'type': session_type,
            'data': {},
            'created_at': time.time()
        }
        logger.info(f"Created {session_type} session for user {user_id}")
    
    def get_session(self, user_id: int):
        """Get session data for a user."""
        if user_id not in self.sessions:
            return None
        
        session = self.sessions[user_id]
        if time.time() - session['created_at'] > self.timeout:
            del self.sessions[user_id]
            return None
        
        return session
    
    def update_session(self, user_id: int, key: str, value: str):
        """Update session data."""
        if user_id in self.sessions:
            self.sessions[user_id]['data'][key] = value
            self.sessions[user_id]['created_at'] = time.time()  # Reset timeout
    
    def clear_session(self, user_id: int):
        """Clear session for a user."""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Cleared session for user {user_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired_users = [
            user_id for user_id, session in self.sessions.items()
            if current_time - session['created_at'] > self.timeout
        ]
        for user_id in expired_users:
            del self.sessions[user_id]
            logger.info(f"Cleaned up expired session for user {user_id}")

# Global session manager
session_manager = SessionManager()

# --- Utility for safe async calls ---
def run_async_safely(coro):
    """Run an async coroutine safely, regardless of event loop state."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.ensure_future(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

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
from app.services.api_service import api_service, ApiService  # Import the instance and class
import httpx
from app.security.credential_manager import CredentialManager
from app.mt5.mt5_manager import MT5Manager

logger = logging.getLogger(__name__)

# Global application instance for proper shutdown
application = None

# --- Network Configuration ---
TELEGRAM_API_TIMEOUT = 30.0
LOCAL_API_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_DELAY = 5.0

# --- Network Health Check Functions ---
def check_internet_connectivity():
    """Check if internet connection is available."""
    try:
        # Try to resolve a known domain
        socket.gethostbyname("8.8.8.8")
        return True
    except socket.gaierror:
        return False

def check_telegram_api():
    """Check if Telegram API is reachable."""
    try:
        socket.gethostbyname("api.telegram.org")
        return True
    except socket.gaierror:
        return False

def check_local_server():
    """Check if local API server is running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 8001))
        sock.close()
        return result == 0
    except Exception:
        return False

async def test_api_connectivity():
    """Test API connectivity with proper error handling."""
    try:
        async with httpx.AsyncClient(timeout=LOCAL_API_TIMEOUT) as client:
            response = await client.get("http://127.0.0.1:8001/health")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"Local API server not reachable: {e}")
        return False

# --- Enhanced API Service with Retry Logic ---
async def safe_api_call_with_retry(endpoint, max_retries=MAX_RETRIES):
    """Make API call with retry logic and proper error handling."""
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Making API call: {endpoint} (attempt {attempt+1}/{max_retries+1})")
            if not await test_api_connectivity():
                logger.warning("Local API server is not running - returning None")
                return None
            result = await api_service.make_api_call(endpoint)
            if result is not None:
                return result
        except httpx.TimeoutException:
            logger.warning(f"Timeout on {endpoint} (attempt {attempt+1})")
            if attempt == max_retries:
                return None
        except httpx.RequestError as e:
            logger.error(f"Request error on {endpoint}: {e}")
            if attempt == max_retries:
                return None
        except Exception as e:
            logger.error(f"General error on {endpoint}: {e}")
            if attempt == max_retries:
                return None
        if attempt < max_retries:
            await asyncio.sleep(RETRY_DELAY)
    return None

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
    return {"risk_profile": "medium", "trading_style": "swing"}

def update_user_activity(user_id, action):
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
        return await safe_api_call_with_retry(endpoint, retries)

    if action == "my_signals":
        await query.edit_message_text(loading_msg)
        result = await safe_api_call("/api/signals", retries=2)
        if result is None:
            await query.edit_message_text("🔧 Local API server is not running. Please start the server and try again.")
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
        result = await safe_api_call("/api/trades", retries=2)
        if result is None:
            await query.edit_message_text("🔧 Local API server is not running. Please start the server and try again.")
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
        result = await safe_api_call(f"/api/settings?telegram_id={user_id}", retries=2)
        if result is None:
            await query.edit_message_text("🔧 Local API server is not running. Please start the server and try again.")
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
        result = await safe_api_call(f"/api/help?telegram_id={user_id}", retries=2)
        if result is None:
            await query.edit_message_text("🔧 Local API server is not running. Please start the server and try again.")
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
    loading_msg = await update.message.reply_text("🔍 Fetching latest signals...")
    try:
        data = await safe_api_call_with_retry("/api/signals")
        if not data:
            await loading_msg.edit_text("😕 Could not fetch signals. The API server may be unavailable. Please try again later.")
            return
        response = "📊 **Latest Forex Signals**\n\n"
        for signal in data:
            response += f"**{signal['pair']}** - {signal['strategy']}\n"
            response += f"Entry: `{signal['entry_range']}`\n"
            response += f"SL: `{signal['stop_loss']}` | TP: `{signal['take_profit']}`\n"
            response += f"Confidence: {signal['confidence']} | R:R {signal['risk_reward_ratio']}\n\n"
        response += "⚠️ **Risk Warning:** This is not financial advice. Always do your own analysis."
        await loading_msg.edit_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in signals command: {e}")
        await loading_msg.edit_text("😕 An error occurred while fetching signals. Please try again later.")

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify a currency pair. Example: `/market EURUSD`")
        return
    pair = context.args[0].upper()
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
    data = await api_service.make_api_call(f"/api/market/{pair}")
    if not data:
        await update.message.reply_text(f"📉 Sorry, market data for **{pair}** is currently unavailable.")
        return
    price = data.get('price', 0)
    high = data.get('high', price)
    low = data.get('low', price)
    open_price = data.get('open', price)
    daily_range = high - low if high and low else 0
    price_change = price - open_price if open_price else 0
    price_change_pct = (price_change / open_price * 100) if open_price else 0
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
    loading_msg = await update.message.reply_text("📋 Fetching trade history...")
    try:
        data = await safe_api_call_with_retry("/api/trades")
        if not data:
            await loading_msg.edit_text("😕 Could not fetch trades. The API server may be unavailable. Please try again later.")
            return
        response = "📊 **Trade History**\n\n"
        for trade in data:
            status_emoji = "✅" if trade['status'] == 'closed' else "⏳"
            pnl_text = f"${trade['pnl']:.2f}" if trade['pnl'] is not None else "N/A"
            response += f"{status_emoji} **{trade['symbol']}** ({trade['order_type'].upper()})\n"
            response += f"Entry: `{trade['entry_price']}`"
            if trade['close_price']:
                response += f" | Exit: `{trade['close_price']}`"
            response += f"\nP&L: `{pnl_text}` | Status: {trade['status'].title()}\n\n"
        await loading_msg.edit_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in trades command: {e}")
        await loading_msg.edit_text("😕 An error occurred while fetching trades. Please try again later.")

async def strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await safe_api_call_with_retry("/api/strategies")
    if not data:
        await update.message.reply_text("😕 Could not fetch strategies. The API server may be unavailable. Please try again later.")
        return
    
    response = "📚 **Trading Strategies**\n\n"
    for strategy in data['strategies']:
        response += f"• **{strategy}**\n"
    
    response += f"\n{data['message']}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

# --- MT5 Trading Commands ---

async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Multi-step MT5 connection process"""
    user_id = update.effective_user.id
    
    # Clean up expired sessions first
    session_manager.cleanup_expired_sessions()
    
    # If user has arguments, use the old single-step method for backward compatibility
    if context.args and len(context.args) >= 3:
        login, password, server = context.args[0], context.args[1], context.args[2]
        loading_msg = await update.message.reply_text("🔗 Connecting to MT5...")
        
        try:
            data = await api_service.make_api_call("/api/mt5/connect", method="POST", json={
                "login": login,
                "password": password,
                "server": server
            })
            
            if data and data.get("success"):
                await loading_msg.edit_text("✅ **MT5 Connected Successfully!**\n\nAccount ready for trading.")
            else:
                error_msg = data.get("error", "Connection failed. Please check your credentials.")
                await loading_msg.edit_text(f"❌ **Connection Failed:** {error_msg}")
                
        except Exception as e:
            await loading_msg.edit_text("❌ Connection error. Please try again.")
        return
    
    # Start multi-step process
    session_manager.create_session(user_id, "mt5_connect")
    await update.message.reply_text(
        "🔗 **MT5 Connection Setup**\n\n"
        "Please enter your MT5 login ID:\n\n"
        "💡 *You can use /cancel at any time to stop this process*",
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check MT5 connection status"""
    loading_msg = await update.message.reply_text("🔍 Checking MT5 status...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/status")
        
        if data and data.get("connected"):
            account_info = data.get("account", {})
            response = (
                f"✅ **MT5 Connected**\n\n"
                f"**Account:** {account_info.get('login', 'N/A')}\n"
                f"**Server:** {account_info.get('server', 'N/A')}\n"
                f"**Balance:** ${account_info.get('balance', 0):,.2f}\n"
                f"**Equity:** ${account_info.get('equity', 0):,.2f}"
            )
        else:
            response = "❌ **MT5 Not Connected**\n\nUse `/connect` to establish connection."
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await loading_msg.edit_text("❌ Error checking status. Please try again.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show account balance"""
    loading_msg = await update.message.reply_text("💰 Fetching account balance...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/balance")
        
        if data:
            response = (
                f"💰 **Account Balance**\n\n"
                f"**Balance:** ${data.get('balance', 0):,.2f}\n"
                f"**Equity:** ${data.get('equity', 0):,.2f}\n"
                f"**Margin:** ${data.get('margin', 0):,.2f}\n"
                f"**Free Margin:** ${data.get('free_margin', 0):,.2f}\n"
                f"**Margin Level:** {data.get('margin_level', 0):,.2f}%"
            )
        else:
            response = "❌ Could not fetch balance. Check MT5 connection."
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await loading_msg.edit_text("❌ Error fetching balance. Please try again.")

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed account info"""
    loading_msg = await update.message.reply_text("📊 Fetching account info...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/account")
        
        if data:
            response = (
                f"📊 **Account Information**\n\n"
                f"**Login:** {data.get('login', 'N/A')}\n"
                f"**Server:** {data.get('server', 'N/A')}\n"
                f"**Balance:** ${data.get('balance', 0):,.2f}\n"
                f"**Equity:** ${data.get('equity', 0):,.2f}\n"
                f"**Margin:** ${data.get('margin', 0):,.2f}\n"
                f"**Free Margin:** ${data.get('free_margin', 0):,.2f}\n"
                f"**Margin Level:** {data.get('margin_level', 0):,.2f}%\n"
                f"**Currency:** {data.get('currency', 'N/A')}"
            )
        else:
            response = "❌ Could not fetch account info. Check MT5 connection."
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await loading_msg.edit_text("❌ Error fetching account info. Please try again.")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buy market order"""
    if len(context.args) < 2:
        help_text = (
            "📈 **Buy Market Order Help:**\n\n"
            "**Format:** `/buy [symbol] [lot] [sl] [tp]`\n"
            "**Examples:**\n"
            "• `/buy EURUSD 0.1` - Buy 0.1 lot EURUSD\n"
            "• `/buy GBPUSD 0.05 1.2500 1.2700` - With SL and TP\n\n"
            "💡 *Use 5-digit prices, decimal lots (0.01, 0.1, 1.0)*"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    symbol = context.args[0].upper()
    try:
        lot = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid lot size. Please enter a valid number.")
        return
    
    sl = float(context.args[2]) if len(context.args) > 2 else None
    tp = float(context.args[3]) if len(context.args) > 3 else None
    
    loading_msg = await update.message.reply_text(f"📈 Placing buy order for {symbol}...")
    
    try:
        order_data = {
            "symbol": symbol,
            "lot": lot,
            "type": "buy"
        }
        if sl:
            order_data["sl"] = sl
        if tp:
            order_data["tp"] = tp
        
        data = await api_service.make_api_call("/api/mt5/order", method="POST", json=order_data)
        
        if data and data.get("success"):
            ticket = data.get("ticket", "N/A")
            await loading_msg.edit_text(f"✅ **Buy Order Placed Successfully!**\n\n**Ticket:** {ticket}\n**Symbol:** {symbol}\n**Lot:** {lot}")
        else:
            error_msg = data.get("error", "Order failed. Please check your inputs.")
            await loading_msg.edit_text(f"❌ **Order Failed:** {error_msg}")
            
    except Exception as e:
        await loading_msg.edit_text("❌ Error placing order. Please try again.")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sell market order"""
    if len(context.args) < 2:
        help_text = (
            "📉 **Sell Market Order Help:**\n\n"
            "**Format:** `/sell [symbol] [lot] [sl] [tp]`\n"
            "**Examples:**\n"
            "• `/sell EURUSD 0.1` - Sell 0.1 lot EURUSD\n"
            "• `/sell GBPUSD 0.05 1.2700 1.2500` - With SL and TP\n\n"
            "💡 *Use 5-digit prices, decimal lots (0.01, 0.1, 1.0)*"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    symbol = context.args[0].upper()
    try:
        lot = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid lot size. Please enter a valid number.")
        return
    
    sl = float(context.args[2]) if len(context.args) > 2 else None
    tp = float(context.args[3]) if len(context.args) > 3 else None
    
    loading_msg = await update.message.reply_text(f"📉 Placing sell order for {symbol}...")
    
    try:
        order_data = {
            "symbol": symbol,
            "lot": lot,
            "type": "sell"
        }
        if sl:
            order_data["sl"] = sl
        if tp:
            order_data["tp"] = tp
        
        data = await api_service.make_api_call("/api/mt5/order", method="POST", json=order_data)
        
        if data and data.get("success"):
            ticket = data.get("ticket", "N/A")
            await loading_msg.edit_text(f"✅ **Sell Order Placed Successfully!**\n\n**Ticket:** {ticket}\n**Symbol:** {symbol}\n**Lot:** {lot}")
        else:
            error_msg = data.get("error", "Order failed. Please check your inputs.")
            await loading_msg.edit_text(f"❌ **Order Failed:** {error_msg}")
            
    except Exception as e:
        await loading_msg.edit_text("❌ Error placing order. Please try again.")

async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show open positions"""
    loading_msg = await update.message.reply_text("📊 Fetching open positions...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/positions")
        
        if data and len(data) > 0:
            response = "📊 **Open Positions**\n\n"
            for pos in data:
                pnl = pos.get('profit', 0)
                pnl_emoji = "🟢" if pnl >= 0 else "🔴"
                response += (
                    f"{pnl_emoji} **{pos['symbol']}** ({pos['type'].upper()})\n"
                    f"**Ticket:** {pos['ticket']} | **Lot:** {pos['lot']}\n"
                    f"**Entry:** {pos['price_open']} | **Current:** {pos.get('price_current', 'N/A')}\n"
                    f"**P&L:** ${pnl:,.2f}\n\n"
                )
        else:
            response = "📊 **No Open Positions**\n\nNo active trades at the moment."
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await loading_msg.edit_text("❌ Error fetching positions. Please try again.")

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending orders"""
    loading_msg = await update.message.reply_text("⏳ Fetching pending orders...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/orders")
        
        if data and len(data) > 0:
            response = "⏳ **Pending Orders**\n\n"
            for order in data:
                response += (
                    f"📋 **{order['symbol']}** ({order['type'].upper()})\n"
                    f"**Ticket:** {order['ticket']} | **Lot:** {order['lot']}\n"
                    f"**Price:** {order['price']}\n\n"
                )
        else:
            response = "⏳ **No Pending Orders**\n\nNo pending orders at the moment."
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await loading_msg.edit_text("❌ Error fetching orders. Please try again.")

async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close specific position"""
    if not context.args:
        help_text = (
            "❌ **Close Position Help:**\n\n"
            "**Format:** `/close [ticket]`\n"
            "**Example:** `/close 12345678`\n\n"
            "💡 *Use `/positions` to see ticket numbers*"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    try:
        ticket = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid ticket number. Please enter a valid number.")
        return
    
    loading_msg = await update.message.reply_text(f"❌ Closing position {ticket}...")
    
    try:
        data = await api_service.make_api_call(f"/api/mt5/close/{ticket}", method="POST")
        
        if data and data.get("success"):
            await loading_msg.edit_text(f"✅ **Position Closed Successfully!**\n\n**Ticket:** {ticket}")
        else:
            error_msg = data.get("error", "Failed to close position.")
            await loading_msg.edit_text(f"❌ **Close Failed:** {error_msg}")
            
    except Exception as e:
        await loading_msg.edit_text("❌ Error closing position. Please try again.")

async def closeall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close all positions"""
    loading_msg = await update.message.reply_text("❌ Closing all positions...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/closeall", method="POST")
        
        if data and data.get("success"):
            closed_count = data.get("closed_count", 0)
            await loading_msg.edit_text(f"✅ **All Positions Closed!**\n\n**Closed:** {closed_count} positions")
        else:
            error_msg = data.get("error", "Failed to close positions.")
            await loading_msg.edit_text(f"❌ **Close Failed:** {error_msg}")
            
    except Exception as e:
        await loading_msg.edit_text("❌ Error closing positions. Please try again.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current price for symbol"""
    if not context.args:
        help_text = (
            "💰 **Price Check Help:**\n\n"
            "**Format:** `/price [symbol]`\n"
            "**Examples:**\n"
            "• `/price EURUSD`\n"
            "• `/price GBPUSD`\n\n"
            "💡 *Use `/symbols` to see available symbols*"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    symbol = context.args[0].upper()
    loading_msg = await update.message.reply_text(f"💰 Fetching price for {symbol}...")
    
    try:
        data = await api_service.make_api_call(f"/api/mt5/price/{symbol}")
        
        if data:
            response = (
                f"💰 **{symbol} Current Price**\n\n"
                f"**Bid:** {data.get('bid', 'N/A')}\n"
                f"**Ask:** {data.get('ask', 'N/A')}\n"
                f"**Spread:** {data.get('spread', 'N/A')} pips"
            )
        else:
            response = f"❌ Could not fetch price for {symbol}."
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await loading_msg.edit_text("❌ Error fetching price. Please try again.")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trading summary"""
    loading_msg = await update.message.reply_text("📊 Generating trading summary...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/summary")
        
        if data:
            response = (
                f"📊 **Trading Summary**\n\n"
                f"**Total P&L:** ${data.get('total_pnl', 0):,.2f}\n"
                f"**Open Positions:** {data.get('open_positions', 0)}\n"
                f"**Pending Orders:** {data.get('pending_orders', 0)}\n"
                f"**Balance:** ${data.get('balance', 0):,.2f}\n"
                f"**Equity:** ${data.get('equity', 0):,.2f}"
            )
        else:
            response = "❌ Could not fetch trading summary."
        
        await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await loading_msg.edit_text("❌ Error fetching summary. Please try again.")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_personal_menu(update, context)

async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reply keyboard button presses and multi-step command responses."""
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    
    # Check if user has an active session
    session = session_manager.get_session(user_id)
    
    if session and session['type'] == 'mt5_connect':
        # Handle MT5 connection multi-step process
        await handle_mt5_connect_step(update, context, text, session)
        return
    
    # Default reply keyboard handling
    if text == "📋 Menu":
        await show_personal_menu(update, context)
    else:
        # Default response for unrecognized text
        await update.message.reply_text(
            "Use /help to see available commands or press the '📋 Menu' button.",
            reply_markup=get_reply_keyboard()
        )

async def handle_mt5_connect_step(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, session: dict):
    """Handle individual steps of the MT5 connection process."""
    user_id = update.effective_user.id
    
    # Get current step based on what data we have
    current_data = session['data']
    
    if 'login' not in current_data:
        # Step 1: Collect login
        session_manager.update_session(user_id, 'login', text)
        await update.message.reply_text(
            "Now enter your password:\n\n"
            "💡 *You can use /cancel at any time to stop this process*",
            parse_mode='Markdown'
        )
        
    elif 'password' not in current_data:
        # Step 2: Collect password
        session_manager.update_session(user_id, 'password', text)
        await update.message.reply_text(
            "Finally, enter your server name:\n\n"
            "💡 *You can use /cancel at any time to stop this process*",
            parse_mode='Markdown'
        )
        
    elif 'server' not in current_data:
        # Step 3: Collect server and attempt connection
        session_manager.update_session(user_id, 'server', text)
        
        # Get all collected data
        login = current_data['login']
        password = current_data['password']
        server = text
        
        # Attempt connection
        loading_msg = await update.message.reply_text("🔗 Connecting to MT5...")
        
        try:
            data = await api_service.make_api_call("/api/mt5/connect", method="POST", json={
                "login": login,
                "password": password,
                "server": server
            })
            
            if data and data.get("success"):
                await loading_msg.edit_text("✅ **Connected successfully.**")
            else:
                error_msg = data.get("error", "Connection failed. Please check your credentials and try again.")
                await loading_msg.edit_text(f"❌ **Connection failed:** {error_msg}")
        except Exception as e:
            await loading_msg.edit_text(f"❌ **Connection failed:** {str(e)}")
        
        # Clear session after connection attempt
        session_manager.clear_session(user_id)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any active multi-step process."""
    user_id = update.effective_user.id
    session = session_manager.get_session(user_id)
    
    if session:
        session_manager.clear_session(user_id)
        await update.message.reply_text(
            "❌ **Process cancelled.**\n\nYou can start over with `/connect` when ready.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "ℹ️ No active process to cancel.",
            parse_mode='Markdown'
        )

def setup_handlers(app: Application):
    """Sets up all the command and message handlers for the bot."""
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CommandHandler('signals', signals))
    app.add_handler(CommandHandler('market', market))
    app.add_handler(CommandHandler('analysis', analysis))
    app.add_handler(CommandHandler('risk', risk))
    app.add_handler(CommandHandler('pipcalc', pipcalc))
    app.add_handler(CommandHandler('donate', donate))
    app.add_handler(CommandHandler('trades', trades))
    app.add_handler(CommandHandler('strategies', strategies))
    
    # MT5 Trading Commands
    app.add_handler(CommandHandler('connect', connect))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('balance', balance))
    app.add_handler(CommandHandler('account', account))
    app.add_handler(CommandHandler('buy', buy))
    app.add_handler(CommandHandler('sell', sell))
    app.add_handler(CommandHandler('positions', positions))
    app.add_handler(CommandHandler('orders', orders))
    app.add_handler(CommandHandler('close', close))
    app.add_handler(CommandHandler('closeall', closeall))
    app.add_handler(CommandHandler('price', price))
    app.add_handler(CommandHandler('summary', summary))
    app.add_handler(CallbackQueryHandler(handle_personal_callback))
    app.add_handler(MessageHandler(TFilters.TEXT & (~TFilters.COMMAND), reply_keyboard_handler))
    app.add_handler(CommandHandler('cancel', cancel))

async def run_network_diagnostics():
    """Run comprehensive network diagnostics."""
    logger.info("Running network diagnostics...")
    diagnostics = {
        "internet": check_internet_connectivity(),
        "telegram_api": check_telegram_api(),
        "local_server": check_local_server(),
        "api_connectivity": await test_api_connectivity()
    }
    logger.info(f"Network diagnostics: {diagnostics}")
    if not diagnostics["internet"]:
        logger.error("❌ No internet connection detected")
    if not diagnostics["telegram_api"]:
        logger.error("❌ Cannot resolve api.telegram.org - DNS issue detected")
    if not diagnostics["local_server"]:
        logger.warning("⚠️ Local API server is not running on port 8001")
    if not diagnostics["api_connectivity"]:
        logger.warning("⚠️ Local API server is not responding to health checks")
    return diagnostics

async def start_telegram_bot(telegram_token: str = None, shutdown_event: asyncio.Event = None):
    """Start the Telegram bot asynchronously."""
    global telegram_app, bot_task
    
    # Use provided token or fallback to environment variable
    if telegram_token is None:
        telegram_token = os.getenv("TELEGRAM_TOKEN", "8071906329:AAH4BbllY9vwwcx0vukm6t6JPQdNWnnz-aY")
    
    # Use provided shutdown event or create a default one
    if shutdown_event is None:
        shutdown_event = asyncio.Event()
    
    try:
        logger.info("🤖 Initializing Telegram bot...")
        
        # Create and configure the Telegram application
        telegram_app = (
            Application.builder()
            .token(telegram_token)
            .connect_timeout(30.0)
            .pool_timeout(30.0)
            .build()
        )
        
        # Setup bot handlers
        setup_handlers(telegram_app)
        
        # Initialize the application
        await telegram_app.initialize()
        
        # Delete any existing webhook to ensure polling mode
        try:
            webhook_info = await telegram_app.bot.get_webhook_info()
            if webhook_info.url:
                logger.info(f"Deleting existing webhook: {webhook_info.url}")
                await telegram_app.bot.delete_webhook()
        except Exception as e:
            logger.warning(f"Error deleting webhook: {e}")
        
        # Start the bot in polling mode
        await telegram_app.start()
        await telegram_app.updater.start_polling(
            timeout=30,
            drop_pending_updates=True
        )
        
        logger.info("✅ Telegram bot started successfully!")
        
        # Start periodic session cleanup task
        asyncio.create_task(periodic_session_cleanup(shutdown_event))
        
        # Keep the bot running until shutdown
        while not shutdown_event.is_set():
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Error starting Telegram bot: {e}")
        # Don't raise the exception to prevent crashing the entire application
        # Just log the error and continue
        return
    finally:
        await stop_telegram_bot()

async def periodic_session_cleanup(shutdown_event: asyncio.Event = None):
    """Periodically clean up expired sessions."""
    if shutdown_event is None:
        shutdown_event = asyncio.Event()
    
    while not shutdown_event.is_set():
        try:
            session_manager.cleanup_expired_sessions()
            await asyncio.sleep(60)  # Run every minute
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
            await asyncio.sleep(60)

async def shutdown_bot():
    """Properly shutdown the bot application."""
    global telegram_app
    if telegram_app:
        try:
            logger.info("🛑 Shutting down bot...")
            if telegram_app.running:
                await telegram_app.stop()
                await telegram_app.shutdown()
            logger.info("✅ Bot shutdown complete")
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")
        finally:
            telegram_app = None

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(shutdown_bot())
    else:
        asyncio.run(shutdown_bot())

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("🚀 Starting Forex Trading Bot...")
    
    # Add signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = start_bot()
        if not success:
            logger.error("Failed to start bot.")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Please check:")
        logger.error("1. Internet connection")
        logger.error("2. DNS settings (try 8.8.8.8 or 1.1.1.1)")
        logger.error("3. Local API server is running on http://127.0.0.1:8001")
        logger.error("4. Firewall/antivirus is not blocking Python")
        logger.error("5. Bot token is valid")
    finally:
        try:
            if application:
                run_async_safely(shutdown_bot())
        except Exception as e:
            logger.error(f"Error during final shutdown: {e}")
        tracemalloc.stop()
        logger.info("Tracemalloc stopped")

if __name__ == "__main__":
    main()