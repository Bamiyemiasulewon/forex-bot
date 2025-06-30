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
from app.telegram.orderblock_commands import (
    orderblock_command, orderblock_status_command, scan_orderblocks_command
)

logger = logging.getLogger(__name__)

# Global application instance for proper shutdown
application = None

# Global shutdown event
shutdown_event = None

def initialize_shutdown_event():
    """Initialize the global shutdown event."""
    global shutdown_event
    if shutdown_event is None:
        shutdown_event = asyncio.Event()
    return shutdown_event

# --- Network Configuration ---
TELEGRAM_API_TIMEOUT = 30.0
LOCAL_API_TIMEOUT = 60.0  # Increased for MT5 operations
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
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        return result == 0
    except Exception:
        return False

async def test_api_connectivity():
    """Test API connectivity with proper error handling."""
    try:
        async with httpx.AsyncClient(timeout=LOCAL_API_TIMEOUT) as client:
            response = await client.get("http://127.0.0.1:8000/health")
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

**MT5 Trading**
/start - Initialize bot
/connect - Connect to MT5 (prompts for login details)
/status - Check MT5 connection
/balance - Show account balance
/account - Show account info
/buy - Place buy market order
/sell - Place sell market order
/positions - Show open positions
/orders - Show pending orders
/close - Close specific position
/closeall - Close all positions
/modify - Modify SL/TP
/cancel - Cancel pending order
/price - Get current price
/summary - Trading summary
/profit - Current P&L

**Trading & Analysis**
/signals - Get the latest forex signals
/market [PAIR] - View live market data (e.g., /market EURUSD)
/analysis [PAIR] - Technical analysis for a pair
/trades - View your trade history

**Order Block Strategy**
/orderblock - Show Order Block strategy info
/orderblock_status - Show current Order Block strategy status
/scan_orderblocks - Scan for Order Block setups

**Calculators & Tools**
/risk [PAIR] [RISK%] [SL PIPS] - Calculate position size

**Information**
/strategies - Learn about our strategies
/help - Show this command list

💡 **Tips:**
• Use /risk without parameters for help
• All commands support major currency pairs
• Risk % should be 0.1-5% for safety'''

donation_message = ''

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
    menu_text = f"""👋 Hi {user_name}!!\n\nWelcome to your Personal Forex Assistant Menu.\n\nSelect an option below to manage your trading or get help.\n\nYour risk profile: {prefs.get('risk_profile', 'N/A')}\nTrading style: {prefs.get('trading_style', 'N/A')}\n\nNB: Click on the Menu button to see list on commands"""
    await update.message.reply_text(menu_text)

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
                "`/strategies` - Learn about our strategies",
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
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Trader"
    prefs = get_user_preferences(user_id)
    menu_text = f"""👋 Hi {user_name}!!\n\nWelcome to your Personal Forex Assistant Menu.\n\nSelect an option below to manage your trading or get help.\n\nYour risk profile: {prefs.get('risk_profile', 'N/A')}\nTrading style: {prefs.get('trading_style', 'N/A')}\n\nNB: Click on the Menu button to see list on commands"""
    await update.message.reply_text(menu_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(commands_message, parse_mode='Markdown')

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
    """Show available trading strategies."""
    strategies_text = '''📊 **TRADING STRATEGIES**

🎯 **Order Block + RSI + Fibonacci (Primary)**
• Break of structure detection
• Order block identification  
• Fibonacci retracement alignment (38.2%, 50%, 61.8%)
• RSI confirmation (oversold < 30, overbought > 70)
• Risk: 10% per trade, max 3 trades/day
• Sessions: London (7-11 AM GMT), NY (12-4 PM GMT)

📈 **RSI Strategy (Fallback)**
• RSI oversold/overbought signals
• Dynamic stop-loss based on ATR
• 1:2 risk-reward ratio

💡 **Use /orderblock for detailed strategy info**'''
    
    await update.message.reply_text(strategies_text, parse_mode='Markdown')

async def orderblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed Order Block + RSI + Fibonacci strategy information."""
    from app.services.order_block_strategy import order_block_strategy
    
    strategy_info = order_block_strategy.get_strategy_info()
    
    orderblock_text = f'''🎯 **Order Block + RSI + Fibonacci Strategy**

📊 **Current Status:**
• Strategy: {strategy_info['strategy_name']}
• Timeframe: {strategy_info['timeframe']}
• Risk per trade: {strategy_info['risk_per_trade']}
• Max trades per day: {strategy_info['max_trades_per_day']}
• Max daily loss: {strategy_info['max_daily_loss']}
• Daily trades: {strategy_info['daily_trades']}/{strategy_info['max_trades_per_day']}
• Daily P&L: ${strategy_info['daily_pnl']:.2f}
• In trading session: {'✅ Yes' if strategy_info['in_session'] else '❌ No'}

⏰ **Trading Sessions:**
• London: {strategy_info['trading_sessions']['london']}
• New York: {strategy_info['trading_sessions']['new_york']}

🎯 **Entry Conditions:**

**BUY SETUP:**
1. Break of structure to the upside
2. Identify bullish Order Block
3. OB aligns with Fibonacci retracement
4. RSI is below 30 (oversold)
5. Enter at OB zone

**SELL SETUP:**
1. Break of structure to the downside
2. Identify bearish Order Block
3. OB aligns with Fibonacci retracement
4. RSI is above 70 (overbought)
5. Enter at OB zone

📈 **Risk Management:**
• Entry: At Order Block zone
• Stop Loss: Just beyond the order block
• Take Profit: 1:2 risk-reward ratio
• Trailing stop: Optional after 1:1 RR

💡 **Commands:**
• `/orderblock_status` - Current strategy status
• `/orderblock_signals` - Recent signals
• `/orderblock_performance` - Performance metrics
• `/orderblock_settings` - Strategy settings'''
    
    await update.message.reply_text(orderblock_text, parse_mode='Markdown')

async def orderblock_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current Order Block strategy status."""
    from app.services.order_block_strategy import order_block_strategy
    from app.services.risk_service import risk_service
    
    strategy_info = order_block_strategy.get_strategy_info()
    risk_summary = risk_service.get_risk_summary()
    
    status_text = f'''📊 **Order Block Strategy Status**

🟢 **Strategy Active: {'Yes' if strategy_info['in_session'] else 'No'}**
⏰ **Current Session: {'London' if 7 <= datetime.now(timezone.utc).hour < 11 else 'New York' if 12 <= datetime.now(timezone.utc).hour < 16 else 'Outside Trading Hours'}**

📈 **Daily Statistics:**
• Trades today: {strategy_info['daily_trades']}/{strategy_info['max_trades_per_day']}
• Daily P&L: ${strategy_info['daily_pnl']:.2f}
• Daily loss limit: {strategy_info['max_daily_loss']}
• Can trade: {'✅ Yes' if strategy_info['daily_trades'] < strategy_info['max_trades_per_day'] and abs(strategy_info['daily_pnl']) < float(strategy_info['max_daily_loss'].rstrip('%')) * 100 else '❌ No'}

🎯 **Risk Parameters:**
• Risk per trade: {risk_summary['risk_per_trade']}
• Risk/Reward ratio: {risk_summary['risk_reward_ratio']}
• Max daily loss: {risk_summary['max_daily_loss']}

⏰ **Next Session:**
• London: {strategy_info['trading_sessions']['london']} GMT
• New York: {strategy_info['trading_sessions']['new_york']} GMT'''
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def orderblock_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent Order Block signals."""
    from app.services.signal_service import signal_service
    
    try:
        signals = await signal_service.generate_signals()
        
        if not signals:
            await update.message.reply_text("📊 **No recent signals found.**\n\nThis could mean:\n• No Order Block setups detected\n• Outside trading sessions\n• Market conditions not suitable")
            return
        
        # Filter for Order Block signals
        orderblock_signals = [s for s in signals if 'Order Block' in s.get('strategy', '')]
        
        if not orderblock_signals:
            await update.message.reply_text("📊 **No Order Block signals in recent data.**\n\nOther signals available:\n" + "\n".join([f"• {s['pair']}: {s['strategy']}" for s in signals[:3]]))
            return
        
        signals_text = "🎯 **Recent Order Block Signals:**\n\n"
        
        for i, signal in enumerate(orderblock_signals[:5], 1):
            signals_text += f"**{i}. {signal['pair']}**\n"
            signals_text += f"• Signal: {signal['signal'].upper()}\n"
            signals_text += f"• Strategy: {signal['strategy']}\n"
            signals_text += f"• Confidence: {signal['confidence']}%\n"
            if 'entry_price' in signal:
                signals_text += f"• Entry: {signal['entry_price']:.5f}\n"
            if 'stop_loss' in signal:
                signals_text += f"• Stop Loss: {signal['stop_loss']:.5f}\n"
            if 'take_profit' in signal:
                signals_text += f"• Take Profit: {signal['take_profit']:.5f}\n"
            if 'reasoning' in signal:
                signals_text += f"• Reason: {signal['reasoning']}\n"
            signals_text += "\n"
        
        await update.message.reply_text(signals_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting Order Block signals: {e}")
        await update.message.reply_text("❌ Error retrieving signals. Please try again later.")

async def orderblock_performance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Order Block strategy performance metrics."""
    from app.services.order_block_strategy import order_block_strategy
    
    strategy_info = order_block_strategy.get_strategy_info()
    
    # Calculate performance metrics (placeholder - would need database integration)
    total_trades = strategy_info['daily_trades']
    daily_pnl = strategy_info['daily_pnl']
    
    if total_trades == 0:
        performance_text = '''📊 **Order Block Strategy Performance**

📈 **Today's Performance:**
• Total trades: 0
• Win rate: N/A
• Average RR: N/A
• Daily P&L: $0.00

📊 **Historical Performance:**
• Total trades: 0
• Win rate: N/A
• Average RR: N/A
• Best trade: N/A
• Worst trade: N/A

💡 **Start trading to see performance metrics!**'''
    else:
        # Placeholder calculations (would need real data)
        win_rate = "N/A"  # Would calculate from database
        avg_rr = "1:2"  # Strategy target
        
        performance_text = f'''📊 **Order Block Strategy Performance**

📈 **Today's Performance:**
• Total trades: {total_trades}
• Win rate: {win_rate}
• Average RR: {avg_rr}
• Daily P&L: ${daily_pnl:.2f}

📊 **Historical Performance:**
• Total trades: {total_trades}
• Win rate: {win_rate}
• Average RR: {avg_rr}
• Best trade: N/A
• Worst trade: N/A

💡 **Performance tracking requires database integration**'''
    
    await update.message.reply_text(performance_text, parse_mode='Markdown')

async def orderblock_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show and allow modification of Order Block strategy settings."""
    from app.services.order_block_strategy import order_block_strategy
    
    strategy_info = order_block_strategy.get_strategy_info()
    
    settings_text = f'''⚙️ **Order Block Strategy Settings**

📊 **Current Configuration:**
• RSI Period: {order_block_strategy.rsi_period}
• RSI Oversold: {order_block_strategy.rsi_oversold}
• RSI Overbought: {order_block_strategy.rsi_overbought}
• Fibonacci Levels: {order_block_strategy.fib_levels}
• Lookback Period: {order_block_strategy.lookback_period}
• ATR Period: {order_block_strategy.atr_period}

💰 **Risk Management:**
• Risk per trade: {strategy_info['risk_per_trade']}
• Max trades per day: {strategy_info['max_trades_per_day']}
• Max daily loss: {strategy_info['max_daily_loss']}

⏰ **Trading Sessions:**
• London: {strategy_info['trading_sessions']['london']}
• New York: {strategy_info['trading_sessions']['new_york']}

💡 **Settings are currently read-only.**
Contact admin for configuration changes.'''
    
    await update.message.reply_text(settings_text, parse_mode='Markdown')

async def scan_orderblocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan for current Order Block setups across all pairs."""
    from app.services.signal_service import signal_service
    
    await update.message.reply_text("🔍 **Scanning for Order Block setups...**")
    
    try:
        signals = await signal_service.generate_signals()
        
        if not signals:
            await update.message.reply_text("📊 **No Order Block setups found.**\n\nMarket conditions may not be suitable for Order Block entries.")
            return
        
        # Filter for Order Block signals
        orderblock_signals = [s for s in signals if 'Order Block' in s.get('strategy', '')]
        
        if not orderblock_signals:
            await update.message.reply_text("📊 **No Order Block setups detected.**\n\nThis could mean:\n• No break of structure detected\n• Order blocks not aligning with Fibonacci levels\n• RSI conditions not met\n• Outside optimal trading sessions")
            return
        
        scan_text = f"🎯 **Order Block Setups Found: {len(orderblock_signals)}**\n\n"
        
        for signal in orderblock_signals:
            scan_text += f"**{signal['pair']}** - {signal['signal'].upper()}\n"
            scan_text += f"• Confidence: {signal['confidence']}%\n"
            if 'fibonacci_level' in signal:
                scan_text += f"• Fibonacci Level: {signal['fibonacci_level']}\n"
            if 'rsi_value' in signal:
                scan_text += f"• RSI: {signal['rsi_value']:.1f}\n"
            if 'reasoning' in signal:
                scan_text += f"• Setup: {signal['reasoning']}\n"
            scan_text += "\n"
        
        await update.message.reply_text(scan_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error scanning for Order Blocks: {e}")
        await update.message.reply_text("❌ Error scanning for setups. Please try again later.")

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
            
            if data is None:
                await loading_msg.edit_text("❌ **Connection Failed:** API server is not running. Please start the server first.")
                return
            
            if data.get("success"):
                await loading_msg.edit_text("✅ **MT5 Connected Successfully!**\n\nAccount ready for trading.")
            else:
                error_msg = data.get("error", "Connection failed. Please check your credentials.")
                await loading_msg.edit_text(f"❌ **Connection Failed:** {error_msg}")
                
        except Exception as e:
            await loading_msg.edit_text(f"❌ **Connection Failed:** {str(e)}")
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
        
        if data is None:
            await loading_msg.edit_text("❌ **Status Check Failed:** API server is not running. Please start the server first.")
            return
        
        if data.get("connected"):
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
        await loading_msg.edit_text(f"❌ **Status Check Failed:** {str(e)}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show account balance"""
    loading_msg = await update.message.reply_text("💰 Fetching account balance...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/balance")
        
        if data is None:
            await loading_msg.edit_text("❌ **Balance Check Failed:** API server is not running. Please start the server first.")
            return
        
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
        await loading_msg.edit_text(f"❌ **Balance Check Failed:** {str(e)}")

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed account info"""
    loading_msg = await update.message.reply_text("📊 Fetching account info...")
    
    try:
        data = await api_service.make_api_call("/api/mt5/account")
        
        if data is None:
            await loading_msg.edit_text("❌ **Account Check Failed:** API server is not running. Please start the server first.")
            return
        
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
        await loading_msg.edit_text(f"❌ **Account Check Failed:** {str(e)}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiates a multi-step process to place a buy order."""
    user_id = update.effective_user.id
    session_manager.create_session(user_id, "buy_order")
    
    await update.message.reply_text(
        "📈 **Buy Order Setup**\n\n"
        "Please enter the symbol you want to buy (e.g., EURUSD, GBPJPY).",
        parse_mode='Markdown'
    )

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiates a multi-step process to place a sell order."""
    user_id = update.effective_user.id
    session_manager.create_session(user_id, "sell_order")
    
    await update.message.reply_text(
        "📉 **Sell Order Setup**\n\n"
        "Please enter the symbol you want to sell (e.g., EURUSD, GBPJPY).",
        parse_mode='Markdown'
    )

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
            "💡 *Use /symbols to see available symbols*"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    symbol = context.args[0].upper()
    loading_msg = await update.message.reply_text(f"💰 Fetching price for {symbol}...")
    
    endpoint = f"/api/mt5/price/{symbol}"
    logger.info(f"Calling price endpoint: {api_service.base_url}{endpoint}")

    try:
        data = await api_service.make_api_call(endpoint)
        
        if data:
            if "error" in data:
                logger.error(f"API returned an error for /price: {data['error']}")
                await loading_msg.edit_text(f"❌ Error: {data['error']}")
            else:
                response = (
                    f"💰 **{symbol} Current Price**\n\n"
                    f"**Bid:** {data.get('bid', 'N/A')}\n"
                    f"**Ask:** {data.get('ask', 'N/A')}\n"
                    f"**Spread:** {data.get('spread', 'N/A')} pips"
                )
                await loading_msg.edit_text(response, parse_mode='Markdown')
        else:
            response = f"❌ Could not fetch price for {symbol}. The API server might be down or the symbol is invalid."
            await loading_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Exception in /price command for symbol {symbol}: {e}", exc_info=True)
        await loading_msg.edit_text("❌ An unexpected error occurred while fetching the price. Please check the logs.")

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

async def modify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiates a multi-step process to modify a position."""
    user_id = update.effective_user.id
    
    # Start a new session for modifying a position
    session_manager.create_session(user_id, "modify_position")
    
    # Ask for the ticket number
    await update.message.reply_text(
        "📝 **Modify Position**\n\n"
        "Please enter the ticket number of the position you want to modify.\n\n"
        "You can find the ticket number using the /positions command.",
        parse_mode='Markdown'
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_personal_menu(update, context)

async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reply keyboard button presses and multi-step command responses."""
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    
    # Check if user has an active session
    session = session_manager.get_session(user_id)
    
    if session:
        session_type = session.get('type')
        if session_type == 'mt5_connect':
            await handle_mt5_connect_step(update, context, text, session)
            return
        elif session_type in ['buy_order', 'sell_order']:
            await handle_order_step(update, context, text, session)
            return
        elif session_type == 'modify_position':
            await handle_modify_step(update, context, text, session)
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
            
            if data is None:
                await loading_msg.edit_text("❌ **Connection Failed:** API server is not running. Please start the server first.")
                return
            
            if data.get("success"):
                await loading_msg.edit_text("✅ **MT5 Connected Successfully!**\n\nAccount ready for trading.")
            else:
                error_msg = data.get("error", "Connection failed. Please check your credentials.")
                await loading_msg.edit_text(f"❌ **Connection Failed:** {error_msg}")
                
        except Exception as e:
            await loading_msg.edit_text(f"❌ **Connection Failed:** {str(e)}")
        
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

async def handle_order_step(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, session: dict):
    """Handle individual steps of the order placement process."""
    user_id = update.effective_user.id
    current_data = session['data']
    order_type = session['type'].split('_')[0] # 'buy' or 'sell'

    if 'symbol' not in current_data:
        # Step 1: Collect symbol
        session_manager.update_session(user_id, 'symbol', text.upper())
        
        keyboard = [
            [InlineKeyboardButton("0.01 lots", callback_data="order_lot:0.01"), InlineKeyboardButton("0.1 lots", callback_data="order_lot:0.1")],
            [InlineKeyboardButton("0.5 lots", callback_data="order_lot:0.5"), InlineKeyboardButton("1.0 lots", callback_data="order_lot:1.0")]
        ]
        
        await update.message.reply_text(
            "What lot size do you want to use?\n\nYou can select a size or type your own.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif 'lot' not in current_data:
        # Step 2: Collect lot size
        try:
            lot = float(text)
            if lot <= 0:
                await update.message.reply_text("Lot size must be positive. Please try again.")
                return
            session_manager.update_session(user_id, 'lot', lot)
            keyboard = [[InlineKeyboardButton("Skip SL/TP", callback_data="order_skip_sltp")]]
            await update.message.reply_text(
                "Enter the Stop Loss price (or skip).",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except ValueError:
            await update.message.reply_text("Invalid number. Please enter a valid lot size.")

    elif 'sl' not in current_data:
        # Step 3: Collect Stop Loss
        try:
            sl = float(text) if text.lower() != 'skip' else 0.0
            session_manager.update_session(user_id, 'sl', sl)
            keyboard = [[InlineKeyboardButton("Skip TP", callback_data="order_skip_tp")]]
            await update.message.reply_text(
                "Enter the Take Profit price (or skip).",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except ValueError:
            await update.message.reply_text("Invalid price. Please enter a valid number for Stop Loss.")

    elif 'tp' not in current_data:
        # Step 4: Collect Take Profit and confirm
        try:
            tp = float(text) if text.lower() != 'skip' else 0.0
            session_manager.update_session(user_id, 'tp', tp)

            # All data collected, show confirmation
            await show_order_confirmation(update, context, session)

        except ValueError:
            await update.message.reply_text("Invalid price. Please enter a valid number for Take Profit.")

async def show_order_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
    """Display order details and ask for confirmation."""
    order_data = session['data']
    order_type = session['type'].split('_')[0].upper()
    
    confirmation_text = (
        f"**Confirm Your Order**\n\n"
        f"**Type:** {order_type}\n"
        f"**Symbol:** {order_data['symbol']}\n"
        f"**Lot Size:** {order_data['lot']}\n"
        f"**Stop Loss:** {order_data['sl'] if order_data['sl'] > 0 else 'N/A'}\n"
        f"**Take Profit:** {order_data['tp'] if order_data['tp'] > 0 else 'N/A'}\n\n"
        "Do you want to place this order?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="order_confirm"),
         InlineKeyboardButton("❌ Cancel", callback_data="order_cancel")]
    ]
    await update.message.reply_text(confirmation_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from the order process."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = session_manager.get_session(user_id)
    if not session:
        await query.edit_message_text("Your session has expired. Please start over.")
        return

    action = query.data.split(':')[0]
    
    if action == "order_lot":
        lot = float(query.data.split(':')[1])
        session_manager.update_session(user_id, 'lot', lot)
        keyboard = [[InlineKeyboardButton("Skip SL/TP", callback_data="order_skip_sltp")]]
        await query.edit_message_text(
            f"Lot size set to {lot}. Now, enter the Stop Loss price (or skip).",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action == "order_skip_sltp":
        session_manager.update_session(user_id, 'sl', 0.0)
        session_manager.update_session(user_id, 'tp', 0.0)
        await show_order_confirmation(query, context, session)

    elif action == "order_skip_tp":
        session_manager.update_session(user_id, 'tp', 0.0)
        await show_order_confirmation(query, context, session)

    elif action == "order_confirm":
        await place_final_order(query, context, session)

    elif action == "order_cancel":
        session_manager.clear_session(user_id)
        await query.edit_message_text("Order cancelled.")

async def place_final_order(query: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
    """Place the final order after confirmation."""
    await query.edit_message_text("Placing order...")
    
    order_data = session['data']
    order_type = session['type'].split('_')[0]
    
    api_payload = {
        "symbol": order_data['symbol'],
        "lot": order_data['lot'],
        "type": order_type,
    }
    if order_data['sl'] > 0:
        api_payload['sl'] = order_data['sl']
    if order_data['tp'] > 0:
        api_payload['tp'] = order_data['tp']
        
    try:
        data = await api_service.make_api_call("/api/mt5/order", method="POST", json=api_payload)
        
        if data and data.get("success"):
            ticket = data.get("ticket", "N/A")
            await query.edit_message_text(f"✅ **Order Placed Successfully!**\n\n**Ticket:** {ticket}")
        else:
            error_msg = data.get("error", "Order failed. Please check your inputs.")
            await query.edit_message_text(f"❌ **Order Failed:** {error_msg}")
            
    except Exception as e:
        await query.edit_message_text("❌ Error placing order. Please try again.")
    finally:
        session_manager.clear_session(query.from_user.id)

async def handle_modify_step(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, session: dict):
    """Handle individual steps of the position modification process."""
    user_id = update.effective_user.id
    current_data = session['data']

    if 'ticket' not in current_data:
        # Step 1: Collect Ticket Number
        try:
            ticket = int(text)
            session_manager.update_session(user_id, 'ticket', ticket)
            await update.message.reply_text("Enter the new Stop Loss price. Type '0' to remove it.")
        except ValueError:
            await update.message.reply_text("Invalid ticket number. Please enter a valid number.")

    elif 'sl' not in current_data:
        # Step 2: Collect new Stop Loss
        try:
            sl = float(text)
            session_manager.update_session(user_id, 'sl', sl)
            await update.message.reply_text("Enter the new Take Profit price. Type '0' to remove it.")
        except ValueError:
            await update.message.reply_text("Invalid price. Please enter a valid number for Stop Loss.")

    elif 'tp' not in current_data:
        # Step 3: Collect new Take Profit and confirm
        try:
            tp = float(text)
            session_manager.update_session(user_id, 'tp', tp)
            
            # All data collected, show confirmation
            ticket = current_data['ticket']
            sl = current_data['sl']

            confirmation_text = (
                f"**Confirm Modification**\n\n"
                f"**Ticket:** {ticket}\n"
                f"**New Stop Loss:** {sl if sl > 0 else 'Remove'}\n"
                f"**New Take Profit:** {tp if tp > 0 else 'Remove'}\n\n"
                "Do you want to apply these changes?"
            )
            keyboard = [
                [InlineKeyboardButton("✅ Confirm", callback_data="modify_confirm"),
                 InlineKeyboardButton("❌ Cancel", callback_data="modify_cancel")]
            ]
            await update.message.reply_text(confirmation_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

        except ValueError:
            await update.message.reply_text("Invalid price. Please enter a valid number for Take Profit.")

async def handle_modify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from the modify process."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = session_manager.get_session(user_id)
    if not session:
        await query.edit_message_text("Your session has expired. Please start over with /modify.")
        return

    action = query.data

    if action == "modify_confirm":
        await place_final_modification(query, context, session)
    elif action == "modify_cancel":
        session_manager.clear_session(user_id)
        await query.edit_message_text("Modification cancelled.")

async def place_final_modification(query: Update, context: ContextTypes.DEFAULT_TYPE, session: dict):
    """Send the final modification request to the API."""
    await query.edit_message_text("Applying changes...")

    modify_data = session['data']
    
    api_payload = {
        "ticket": modify_data['ticket'],
        "sl": modify_data['sl'],
        "tp": modify_data['tp'],
    }
    
    try:
        data = await api_service.make_api_call("/api/mt5/modify", method="POST", json=api_payload)
        
        if data and data.get("success"):
            await query.edit_message_text(f"✅ **Position {modify_data['ticket']} Modified Successfully!**")
        else:
            error_msg = data.get("error", "Failed to modify position.")
            await query.edit_message_text(f"❌ **Modification Failed:** {error_msg}")
            
    except Exception as e:
        await query.edit_message_text("❌ An unexpected error occurred during modification.")
    finally:
        session_manager.clear_session(query.from_user.id)

def setup_handlers(app: Application):
    """Sets up all the command and message handlers for the bot."""
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CommandHandler('signals', signals))
    app.add_handler(CommandHandler('market', market))
    app.add_handler(CommandHandler('analysis', analysis))
    app.add_handler(CommandHandler('risk', risk))
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
    app.add_handler(CallbackQueryHandler(handle_order_callback, pattern='^order_'))
    app.add_handler(CallbackQueryHandler(handle_modify_callback, pattern='^modify_'))
    app.add_handler(MessageHandler(TFilters.TEXT & (~TFilters.COMMAND), reply_keyboard_handler))
    app.add_handler(CommandHandler('cancel', cancel))
    app.add_handler(CommandHandler("orderblock", orderblock_command))
    app.add_handler(CommandHandler("orderblock_status", orderblock_status_command))
    app.add_handler(CommandHandler("scan_orderblocks", scan_orderblocks_command))
    app.add_handler(CommandHandler("orderblock_signals", orderblock_signals))
    app.add_handler(CommandHandler("orderblock_performance", orderblock_performance))
    app.add_handler(CommandHandler("orderblock_settings", orderblock_settings))
    app.add_handler(CommandHandler("modify", modify_command))

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
        logger.warning("⚠️ Local API server is not running on port 8000")
    if not diagnostics["api_connectivity"]:
        logger.warning("⚠️ Local API server is not responding to health checks")
    return diagnostics

async def start_telegram_bot(telegram_token: str = None, shutdown_event_param: asyncio.Event = None):
    """Start the Telegram bot asynchronously."""
    global telegram_app, bot_task, shutdown_event
    
    # Use provided token or fallback to environment variable
    if telegram_token is None:
        telegram_token = os.getenv("TELEGRAM_TOKEN", "8071906329:AAH4BbllY9vwwcx0vukm6t6JPQdNWnnz-aY")
    
    # Use provided shutdown event or global one
    if shutdown_event_param is None:
        shutdown_event_param = shutdown_event or initialize_shutdown_event()
    
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
        
        # Set bot commands for Telegram UI
        await set_bot_commands(telegram_app)
        
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
        asyncio.create_task(periodic_session_cleanup(shutdown_event_param))
        
        # Keep the bot running until shutdown
        while not shutdown_event_param.is_set():
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ Error starting Telegram bot: {e}")
        return
    finally:
        await shutdown_bot()

async def periodic_session_cleanup(shutdown_event_param: asyncio.Event = None):
    """Periodically clean up expired sessions."""
    if shutdown_event_param is None:
        shutdown_event_param = shutdown_event
    
    while not shutdown_event_param.is_set():
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
    # Set the shutdown event to stop the bot
    global shutdown_event
    if shutdown_event:
        shutdown_event.set()

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("🚀 Starting Forex Trading Bot...")
    
    # Initialize shutdown event
    global shutdown_event
    shutdown_event = initialize_shutdown_event()
    
    # Add signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the bot asynchronously using the global shutdown event
        asyncio.run(start_telegram_bot())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Please check:")
        logger.error("1. Internet connection")
        logger.error("2. DNS settings (try 8.8.8.8 or 1.1.1.1)")
        logger.error("3. Local API server is running on http://127.0.0.1:8000")
        logger.error("4. Firewall/antivirus is not blocking Python")
        logger.error("5. Bot token is valid")
    finally:
        try:
            if telegram_app:
                run_async_safely(shutdown_bot())
        except Exception as e:
            logger.error(f"Error during final shutdown: {e}")
        tracemalloc.stop()
        logger.info("Tracemalloc stopped")

if __name__ == "__main__":
    main()

async def set_bot_commands(application):
    await application.bot.set_my_commands([
        ("start", "Initialize bot"),
        ("connect", "Connect to MT5 (prompts for login details)"),
        ("status", "Check MT5 connection"),
        ("balance", "Show account balance"),
        ("account", "Show account info"),
        ("buy", "Place buy market order"),
        ("sell", "Place sell market order"),
        ("positions", "Show open positions"),
        ("orders", "Show pending orders"),
        ("close", "Close specific position"),
        ("closeall", "Close all positions"),
        ("modify", "Modify SL/TP"),
        ("cancel", "Cancel pending order"),
        ("price", "Get current price"),
        ("summary", "Trading summary"),
        ("strategies", "Learn about our strategies"),
        ("help", "Show this command list")
    ])