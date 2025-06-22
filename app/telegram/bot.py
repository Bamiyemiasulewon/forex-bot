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
`/news` - Fetch latest forex news
`/calendar` - View economic event calendar
`/trades` - View your open/closed trades

**Calculators & Tools**
`/risk [PAIR] [RISK%] [SL PIPS]` - Calculate position size
`/pipcalc [PAIR] [LOTS] [PIPS]` - Calculate pip values

**Information**
`/strategies` - Learn about our strategies
`/donate` - Support the bot
`/help` - Show this command list'''

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
    response_data = await api_service.make_api_call("/api/signals")
    if not response_data:
        await update.message.reply_text("😕 Could not fetch signals. The server might be down. Please try again later.")
        return
    
    formatted_signals = "📊 **Latest Trading Signals**\n\n"
    for signal in response_data:
        formatted_signals += (
            f"🔹 **{signal['pair']}** ({signal['strategy']})\n"
            f"   Entry: `{signal['entry_range']}` | SL: `{signal['stop_loss']}` | TP: `{signal['take_profit']}`\n"
            f"   Confidence: **{signal['confidence']}** | R:R: `{signal['risk_reward_ratio']}`\n\n"
        )
    await update.message.reply_text(formatted_signals, parse_mode='Markdown')

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify a currency pair. Example: `/market EURUSD`")
        return
    pair = context.args[0].upper()
    data = await api_service.make_api_call(f"/api/market/{pair}")
    if not data:
        await update.message.reply_text(f"📉 Sorry, market data for **{pair}** is currently unavailable.")
        return

    response_text = (
        f"📈 **Market Data for {data['pair']}**\n\n"
        f"**Price:** `{data['price']:,.5f}`\n"
        f"**Open:** `{data.get('open', 'N/A'):,.5f}`\n"
        f"**Day's High:** `{data.get('high', 'N/A'):,.5f}`\n"
        f"**Day's Low:** `{data.get('low', 'N/A'):,.5f}`\n"
    )
    await update.message.reply_text(response_text, parse_mode='Markdown')

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify a currency pair. Example: `/analysis EURUSD`")
        return
    # This is a placeholder as the backend analysis is not fully implemented
    await update.message.reply_text("Analysis feature is being upgraded. Please check back later.")

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("❌ Invalid format. Use: `/risk [PAIR] [RISK%] [SL PIPS]`")
        return
    pair, risk_percent, sl_pips = context.args[0], context.args[1], context.args[2]
    data = await api_service.make_api_call(f"/api/risk/{pair}/{risk_percent}/{sl_pips}")
    if not data:
        await update.message.reply_text("😕 Calculation failed. Please check your inputs or try again.")
        return
    
    response = (
        f"🛡️ **Risk Calculation**\n\n"
        f"💰 Account Balance: `${data['account_balance']:,.2f}`\n"
        f"📈 Risk: `{data['risk_percent']}%` (${data['risk_amount_usd']:,.2f})\n"
        f"📉 Stop-Loss: `{data['stop_loss_pips']}` pips\n\n"
        f"**Recommended Position Size for {data['pair']}:**\n"
        f"✅ **`{data['position_size_lots']:.2f}` lots**"
    )
    await update.message.reply_text(response, parse_mode='Markdown')

async def pipcalc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is also a command to be implemented via API call
    await update.message.reply_text("Pip calculator feature is being upgraded.")

# async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     data = await api_service.make_api_call("/api/news")
#     if not data:
#         await update.message.reply_text("😕 Could not fetch news. Please try again later.")
#         return
#
#     response = "📰 **Latest Forex News**\n\n"
#     for item in data[:5]: # Show top 5
#         response += f"▪️ <a href='{item['link']}'>{item['title']}</a>\n"
#     await update.message.reply_text(response, parse_mode='HTML', disable_web_page_preview=True)

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(donation_message, parse_mode='Markdown', disable_web_page_preview=True)
    
async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The trade history feature is currently under maintenance.")

async def strategies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The strategies feature is currently under maintenance.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()

    COMMAND_MAP = {
        'signals': signals,
        'market_menu': lambda u,c: u.message.reply_text("To get market data, use the command: `/market [PAIR]`"),
        'tools_menu': lambda u,c: u.message.reply_text("Available tools:\n`/risk [PAIR] [RISK%] [SL PIPS]`\n`/pipcalc [PAIR] [LOTS] [PIPS]`"),
        # 'news': news,
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
    # app.add_handler(CommandHandler('news', news))
    app.add_handler(CommandHandler('donate', donate))
    app.add_handler(CommandHandler('trades', trades))
    app.add_handler(CommandHandler('strategies', strategies))
    app.add_handler(CallbackQueryHandler(button)) 