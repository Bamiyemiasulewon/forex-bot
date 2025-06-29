"""
Order Block + RSI + Fibonacci Strategy Commands
"""

import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from app.services.order_block_strategy import order_block_strategy
from app.services.signal_service import signal_service
from app.services.risk_service import risk_service

logger = logging.getLogger(__name__)

async def orderblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Order Block strategy information."""
    strategy_info = order_block_strategy.get_strategy_info()
    
    text = f'''🎯 **Order Block + RSI + Fibonacci Strategy**

📊 **Status:**
• Active: {'✅ Yes' if strategy_info['in_session'] else '❌ No'}
• Trades today: {strategy_info['daily_trades']}/{strategy_info['max_trades_per_day']}
• Daily P&L: ${strategy_info['daily_pnl']:.2f}

⏰ **Sessions:**
• London: {strategy_info['trading_sessions']['london']}
• New York: {strategy_info['trading_sessions']['new_york']}

💡 **Commands:**
• `/orderblock_status` - Current status
• `/orderblock_signals` - Recent signals
• `/scan_orderblocks` - Scan for setups'''
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def orderblock_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current strategy status."""
    strategy_info = order_block_strategy.get_strategy_info()
    
    current_hour = datetime.now(timezone.utc).hour
    if 7 <= current_hour < 11:
        session = "London"
    elif 12 <= current_hour < 16:
        session = "New York"
    else:
        session = "Outside Hours"
    
    text = f'''📊 **Order Block Status**

🟢 **Active: {'Yes' if strategy_info['in_session'] else 'No'}**
⏰ **Session: {session}**

📈 **Today:**
• Trades: {strategy_info['daily_trades']}/{strategy_info['max_trades_per_day']}
• P&L: ${strategy_info['daily_pnl']:.2f}
• Can trade: {'✅ Yes' if strategy_info['daily_trades'] < strategy_info['max_trades_per_day'] else '❌ No'}'''
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def orderblock_signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent Order Block signals."""
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

async def orderblock_performance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Order Block strategy performance metrics."""
    strategy_info = order_block_strategy.get_strategy_info()
    
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
        performance_text = f'''📊 **Order Block Strategy Performance**

📈 **Today's Performance:**
• Total trades: {total_trades}
• Win rate: N/A (requires database)
• Average RR: 1:2 (target)
• Daily P&L: ${daily_pnl:.2f}

📊 **Historical Performance:**
• Total trades: {total_trades}
• Win rate: N/A (requires database)
• Average RR: 1:2 (target)
• Best trade: N/A
• Worst trade: N/A

💡 **Performance tracking requires database integration**'''
    
    await update.message.reply_text(performance_text, parse_mode='Markdown')

async def orderblock_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Order Block strategy settings."""
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

async def scan_orderblocks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan for Order Block setups."""
    await update.message.reply_text("🔍 Scanning for Order Block setups...")
    
    try:
        signals = await signal_service.generate_signals()
        orderblock_signals = [s for s in signals if 'Order Block' in s.get('strategy', '')]
        
        if not orderblock_signals:
            await update.message.reply_text("📊 No Order Block setups found.")
            return
        
        text = f"🎯 **Found {len(orderblock_signals)} setups:**\n\n"
        
        for signal in orderblock_signals:
            text += f"**{signal['pair']}** - {signal['signal'].upper()}\n"
            text += f"• Confidence: {signal['confidence']}%\n"
            if 'reasoning' in signal:
                text += f"• {signal['reasoning']}\n"
            text += "\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error scanning: {e}")
        await update.message.reply_text("❌ Error scanning. Try again later.")

# Command mapping
ORDERBLOCK_COMMANDS = {
    'orderblock': orderblock_command,
    'orderblock_status': orderblock_status_command,
    'orderblock_signals': orderblock_signals_command,
    'orderblock_performance': orderblock_performance_command,
    'orderblock_settings': orderblock_settings_command,
    'scan_orderblocks': scan_orderblocks_command,
} 