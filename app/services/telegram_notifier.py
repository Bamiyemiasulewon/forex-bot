# forex-bot/app/services/telegram_notifier.py
import logging
from telegram import Bot
from typing import Dict
import os
import json

logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # Set this in your environment if you want admin notifications
CHAT_ID_FILE = 'registered_chat_ids.json'

class AITelegramNotifier:
    def __init__(self, bot: Bot, chat_id: str, user_id: int = None):
        self.bot = bot
        self.chat_id = chat_id
        self.user_id = user_id

    async def send_trade_opened_notification(self, trade_info: Dict):
        """Sends a notification when a new AI trade is opened."""
        message = (
            f"🤖 **AI Trade Opened**\n\n"
            f"**Symbol:** {trade_info['symbol']} {trade_info['type']}\n"
            f"**Risk:** ${trade_info['risk_amount']:.2f} (5%)\n"
            f"**Target:** ${trade_info['profit_target']:.2f}\n"
            f"**Balance:** ${trade_info['balance']:.2f}"
        )
        await self._send_message(message)

    async def send_trade_closed_notification(self, trade_info: Dict):
        """Sends a notification when a trade is closed."""
        pnl = trade_info['pnl']
        emoji = "✅" if pnl >= 0 else "❌"
        message = (
            f"{emoji} **Trade Closed**\n\n"
            f"**Symbol:** {trade_info['symbol']} {trade_info['type']}\n"
            f"**P&L:** ${pnl:.2f}\n"
            f"**New Balance:** ${trade_info['new_balance']:.2f}\n"
            f"**Next Risk:** ${trade_info['next_risk']:.2f} (5%)"
        )
        await self._send_message(message)

    async def send_daily_summary(self, summary: Dict):
        """Sends a daily risk and performance summary."""
        message = (
            f"📊 **Daily AI Summary**\n\n"
            f"**Risk Used:** ${summary['risk_used']:.2f} ({summary['risk_percent']:.1f}%)\n"
            f"**Trades:** {summary['trades_made']}/{summary['max_trades']}\n"
            f"**P&L:** ${summary['pnl']:.2f}"
        )
        await self._send_message(message)
    
    async def send_shadow_trade_notification(self, trade_info: Dict):
        """Sends a notification for a trade that would have been placed in Shadow Mode."""
        message = (
            f"👻 **Shadow Mode Signal**\n\n"
            f"**Action:** Would place a {trade_info['type']} order\n"
            f"**Symbol:** {trade_info['symbol']}\n"
            f"**Lot Size:** {trade_info['lot_size']:.2f}"
        )
        await self._send_message(message)

    async def send_error_notification(self, error_message: str):
        """Sends an error notification."""
        # Escape special characters that might break Markdown
        safe_error = self._escape_markdown(error_message)
        message = f"⚠️ **AI Bot Alert**\n\n{safe_error}"
        await self._send_message(message)
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special characters that might break Markdown parsing."""
        # Replace characters that have special meaning in Markdown
        replacements = {
            '_': '\\_',
            '*': '\\*',
            '`': '\\`',
            '[': '\\[',
            ']': '\\]',
            '(': '\\(',
            ')': '\\)',
            '#': '\\#',
            '+': '\\+',
            '-': '\\-',
            '=': '\\=',
            '|': '\\|',
            '{': '\\{',
            '}': '\\}',
            '.': '\\.',
            '!': '\\!'
        }
        
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        
        return text

    async def _send_message(self, text: str):
        """Helper method to send a message to the configured chat."""
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='Markdown')
        except Exception as e:
            if 'chat not found' in str(e).lower():
                logger.error(f"Telegram notification failed: Chat not found for chat_id={self.chat_id}. Marking as invalid.")
                return
            logger.warning(f"Markdown parsing failed, trying without parse_mode: {e}")
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=text)
            except Exception as e2:
                if 'chat not found' in str(e2).lower():
                    logger.error(f"Telegram notification failed: Chat not found for chat_id={self.chat_id}. Marking as invalid.")
                    return
                logger.error(f"Failed to send Telegram notification: {e2}")
                try:
                    simple_text = text.replace('*', '').replace('_', '').replace('`', '')
                    await self.bot.send_message(chat_id=self.chat_id, text=simple_text)
                except Exception as e3:
                    logger.error(f"Failed to send even simplified message: {e3}") 