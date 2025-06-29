"""
MT5 Trading Service
Provides integration with MetaTrader 5 for trading operations.
Uses actual MT5 API calls for real trading functionality.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class MT5Service:
    """Service for MT5 trading operations."""
    
    def __init__(self):
        self.connected = False
        self.account_info = {}
        
    async def connect(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to MT5 terminal."""
        try:
            logger.info(f"Connecting to MT5: {login}@{server}")
            MT5_PATH = r"C:\\Program Files\\MetaTrader 5\\terminal64.exe"
            # Initialize MT5 with explicit path
            if not mt5.initialize(path=MT5_PATH):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return {"success": False, "error": f"Failed to initialize MT5: {error[1]}"}
            
            # Login to MT5
            if not mt5.login(login=int(login), password=password, server=server):
                error = mt5.last_error()
                logger.error(f"MT5 login failed: {error}")
                return {"success": False, "error": f"Login failed: {error[1]}"}
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                return {"success": False, "error": "Failed to get account info"}
            
            self.connected = True
            self.account_info = {
                "login": account_info.login,
                "server": account_info.server,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "company": account_info.company
            }
            
            logger.info(f"MT5 connection successful for {login}")
            return {
                "success": True,
                "message": "Connected successfully",
                "account_info": self.account_info
            }
            
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return {"success": False, "error": str(e)}
    
    async def disconnect(self):
        """Disconnect from MT5 terminal."""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                self.account_info = {}
                logger.info("Disconnected from MT5")
        except Exception as e:
            logger.error(f"MT5 disconnect error: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get connection status and account info."""
        if not self.connected:
            return {"connected": False, "error": "Not connected"}
        
        try:
            # Refresh account info
            account_info = mt5.account_info()
            if account_info is None:
                return {"connected": False, "error": "Failed to get account info"}
            
            self.account_info = {
                "login": account_info.login,
                "server": account_info.server,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "company": account_info.company
            }
            
            return {
                "connected": True,
                "account": self.account_info
            }
        except Exception as e:
            logger.error(f"MT5 status error: {e}")
            return {"connected": False, "error": str(e)}
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance information."""
        if not self.connected:
            return None
        
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return {
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "currency": account_info.currency
            }
        except Exception as e:
            logger.error(f"MT5 balance error: {e}")
            return None
    
    async def get_account(self) -> Dict[str, Any]:
        """Get detailed account information."""
        if not self.connected:
            return None
        
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return {
                "login": account_info.login,
                "server": account_info.server,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "company": account_info.company
            }
        except Exception as e:
            logger.error(f"MT5 account error: {e}")
            return None
    
    async def place_order(self, symbol: str, lot: float, order_type: str, 
                         sl: Optional[float] = None, tp: Optional[float] = None) -> Dict[str, Any]:
        """Place a market order."""
        if not self.connected:
            return {"success": False, "error": "Not connected to MT5"}
        
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {"success": False, "error": f"Symbol {symbol} not found"}
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return {"success": False, "error": f"Failed to select symbol {symbol}"}
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {"success": False, "error": f"Failed to get tick for {symbol}"}
            
            # Determine order type and price
            if order_type.lower() == "buy":
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = tick.ask
            elif order_type.lower() == "sell":
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                return {"success": False, "error": "Invalid order type. Use 'buy' or 'sell'"}
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type_mt5,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "python telegram bot order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add stop loss and take profit if provided
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            
            # Send order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {"success": False, "error": f"Order failed: {result.comment}"}
            
            logger.info(f"Order placed successfully: {result.order}")
            return {
                "success": True,
                "ticket": result.order,
                "symbol": symbol,
                "lot": lot,
                "type": order_type,
                "price": result.price,
                "sl": sl,
                "tp": tp
            }
            
        except Exception as e:
            logger.error(f"MT5 order error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions."""
        if not self.connected:
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            positions_list = []
            for position in positions:
                pos_dict = {
                    "ticket": position.ticket,
                    "symbol": position.symbol,
                    "type": "buy" if position.type == 0 else "sell",
                    "lot": position.volume,
                    "price_open": position.price_open,
                    "price_current": position.price_current,
                    "profit": position.profit,
                    "sl": position.sl,
                    "tp": position.tp,
                    "time": position.time
                }
                positions_list.append(pos_dict)
            
            return positions_list
            
        except Exception as e:
            logger.error(f"MT5 positions error: {e}")
            return []
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get pending orders."""
        if not self.connected:
            return []
        
        try:
            orders = mt5.orders_get()
            if orders is None:
                return []
            
            orders_list = []
            for order in orders:
                order_dict = {
                    "ticket": order.ticket,
                    "symbol": order.symbol,
                    "type": self._get_order_type_name(order.type),
                    "lot": order.volume,
                    "price": order.price_open,
                    "sl": order.sl,
                    "tp": order.tp,
                    "time": order.time_setup
                }
                orders_list.append(order_dict)
            
            return orders_list
            
        except Exception as e:
            logger.error(f"MT5 orders error: {e}")
            return []
    
    def _get_order_type_name(self, order_type: int) -> str:
        """Convert MT5 order type to string."""
        order_types = {
            mt5.ORDER_TYPE_BUY: "buy",
            mt5.ORDER_TYPE_SELL: "sell",
            mt5.ORDER_TYPE_BUY_LIMIT: "buylimit",
            mt5.ORDER_TYPE_SELL_LIMIT: "selllimit",
            mt5.ORDER_TYPE_BUY_STOP: "buystop",
            mt5.ORDER_TYPE_SELL_STOP: "sellstop"
        }
        return order_types.get(order_type, "unknown")
    
    async def close_position(self, ticket: int) -> Dict[str, Any]:
        """Close a specific position."""
        if not self.connected:
            return {"success": False, "error": "Not connected to MT5"}
        
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return {"success": False, "error": "Position not found"}
            
            position = position[0]
            
            # Get current tick
            tick = mt5.symbol_info_tick(position.symbol)
            if tick is None:
                return {"success": False, "error": f"Failed to get tick for {position.symbol}"}
            
            # Determine close order type
            if position.type == 0:  # Buy position
                close_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:  # Sell position
                close_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "python telegram bot close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {"success": False, "error": f"Close failed: {result.comment}"}
            
            logger.info(f"Position {ticket} closed successfully")
            return {
                "success": True,
                "ticket": ticket,
                "message": "Position closed successfully"
            }
            
        except Exception as e:
            logger.error(f"MT5 close position error: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_all_positions(self) -> Dict[str, Any]:
        """Close all positions."""
        if not self.connected:
            return {"success": False, "error": "Not connected to MT5"}
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return {"success": True, "closed_count": 0}
            
            closed_count = 0
            for position in positions:
                result = await self.close_position(position.ticket)
                if result["success"]:
                    closed_count += 1
            
            logger.info(f"All positions closed: {closed_count}")
            return {
                "success": True,
                "closed_count": closed_count,
                "message": "All positions closed successfully"
            }
            
        except Exception as e:
            logger.error(f"MT5 close all error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol."""
        if not self.connected:
            return None
        
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            # Calculate spread in pips
            spread_pips = (tick.ask - tick.bid) / symbol_info.point
            
            price_data = {
                "symbol": symbol.upper(),
                "bid": tick.bid,
                "ask": tick.ask,
                "spread": round(spread_pips, 1),
                "time": datetime.fromtimestamp(tick.time).isoformat()
            }
            
            return price_data
            
        except Exception as e:
            logger.error(f"MT5 price error: {e}")
            return None
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get trading summary."""
        if not self.connected:
            return None
        
        try:
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            # Get positions and orders
            positions = await self.get_positions()
            orders = await self.get_orders()
            
            # Calculate total P&L
            total_pnl = sum(pos.get("profit", 0) for pos in positions)
            
            summary_data = {
                "total_pnl": total_pnl,
                "open_positions": len(positions),
                "pending_orders": len(orders),
                "balance": account_info.balance,
                "equity": account_info.equity
            }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"MT5 summary error: {e}")
            return None

# Global MT5 service instance
mt5_service = MT5Service() 