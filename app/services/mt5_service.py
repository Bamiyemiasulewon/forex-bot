"""
MT5 Trading Service
Provides integration with MetaTrader 5 for trading operations.
Uses actual MT5 API calls for real trading functionality.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .ai_config import AIConfig
from app.services.database_service import get_db_dependency, Trade, get_or_create_user, SessionLocal

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

logger = logging.getLogger(__name__)

class MT5Service:
    """Service for MT5 trading operations."""
    
    def __init__(self):
        self.connected = False
        self.account_info = {}
        
    async def connect(self, login: str, password: str, server: str) -> Dict[str, Any]:
        """Connect to MT5 terminal."""
        if not MT5_AVAILABLE:
            return {"success": False, "error": "MetaTrader5 package not available. Please install: pip install MetaTrader5"}
            
        try:
            logger.info(f"Connecting to MT5: {login}@{server}")
            
            # First, shutdown any existing connection
            try:
                mt5.shutdown()
            except:
                pass
            
            # Try multiple connection methods
            connected = False
            
            # Method 1: Try to connect to running terminal
            logger.info("Method 1: Attempting to connect to running MT5 terminal...")
            if mt5.initialize():
                logger.info("✓ Connected to running MT5 terminal!")
                connected = True
            else:
                error = mt5.last_error()
                logger.warning(f"✗ Failed to connect to running terminal: {error}")
            
            # Method 2: Try to launch terminal with explicit path
            if not connected:
                logger.info("Method 2: Trying to launch MT5 terminal with explicit path...")
                MT5_PATH = r"C:\\Program Files\\MetaTrader 5\\terminal64.exe"
                if mt5.initialize(path=MT5_PATH):
                    logger.info("✓ Successfully launched and connected to MT5 terminal!")
                    connected = True
                else:
                    error = mt5.last_error()
                    logger.warning(f"✗ Failed to launch terminal: {error}")
            
            # Method 3: Try with server credentials
            if not connected:
                logger.info("Method 3: Trying to connect with server credentials...")
                if mt5.initialize(server=server, login=int(login), password=password):
                    logger.info("✓ Successfully connected with server credentials!")
                    connected = True
                else:
                    error = mt5.last_error()
                    logger.warning(f"✗ Failed to connect with server credentials: {error}")
            
            if not connected:
                return {"success": False, "error": "Failed to connect to MT5 terminal. Please ensure MT5 is installed and running."}
            
            # Login to MT5 if not already logged in
            account_info = mt5.account_info()
            if account_info is None:
                logger.info("Attempting to login with credentials...")
                if not mt5.login(login=int(login), password=password, server=server):
                    error = mt5.last_error()
                    logger.error(f"MT5 login failed: {error}")
                    return {"success": False, "error": f"Login failed: {error[1] if len(error) > 1 else str(error)}"}
                else:
                    logger.info("✓ Login successful!")
                    account_info = mt5.account_info()
            
            if account_info is None:
                return {"success": False, "error": "Failed to get account info after login"}
            
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
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    async def disconnect(self):
        """Disconnect from MT5 terminal."""
        if not MT5_AVAILABLE:
            return
            
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
        if not MT5_AVAILABLE:
            return {"connected": False, "error": "MetaTrader5 package not available"}
            
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
        if not MT5_AVAILABLE:
            return None
            
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
        if not MT5_AVAILABLE:
            return None
            
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
                        sl_pips: int = None, tp_pips: int = None, magic_number: int = 0, price: float = None, user_id: int = None) -> Dict[str, Any]:
        """
        Places a trade order on MT5. Includes Stop Loss and Take Profit in pips.
        Supports both market and limit orders.
        Records the trade in the database if user_id is provided.
        Always sets SL/TP if provided.
        """
        if not MT5_AVAILABLE:
            return {"success": False, "error": "MetaTrader5 package not available"}
            
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
            order_type_lower = order_type.lower()
            if order_type_lower == "buy":
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                market_price = tick.ask
            elif order_type_lower == "sell":
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                market_price = tick.bid
            else:
                return {"success": False, "error": "Invalid order type. Use 'buy' or 'sell'"}
            
            # --- Volume validation and rounding ---
            min_vol = symbol_info.volume_min
            step = symbol_info.volume_step
            # Round lot to nearest allowed step and ensure >= min_vol
            lot = max(min_vol, round(lot / step) * step)

            # --- Dynamically select supported filling mode ---
            # Default to FOK, fallback to RETURN, then IOC
            filling_mode = None
            if hasattr(mt5, 'ORDER_FILLING_FOK') and (symbol_info.filling_mode & mt5.ORDER_FILLING_FOK):
                filling_mode = mt5.ORDER_FILLING_FOK
            elif hasattr(mt5, 'ORDER_FILLING_RETURN') and (symbol_info.filling_mode & mt5.ORDER_FILLING_RETURN):
                filling_mode = mt5.ORDER_FILLING_RETURN
            elif hasattr(mt5, 'ORDER_FILLING_IOC') and (symbol_info.filling_mode & mt5.ORDER_FILLING_IOC):
                filling_mode = mt5.ORDER_FILLING_IOC
            else:
                # fallback to FOK if nothing else
                filling_mode = mt5.ORDER_FILLING_FOK if hasattr(mt5, 'ORDER_FILLING_FOK') else 0

            # --- Use supported filling mode ---
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type_mt5,
                "price": market_price,
                "deviation": 10,
                "magic": magic_number,
                "comment": "AI Trade",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode
            }
            # Calculate stop loss and take profit prices only if provided
            sl_price = None
            tp_price = None
            if sl_pips is not None and sl_pips != 0:
                if order_type_lower == "buy":
                    sl_price = market_price - abs(sl_pips) * symbol_info.point
                else:
                    sl_price = market_price + abs(sl_pips) * symbol_info.point
            if tp_pips is not None and tp_pips != 0:
                if order_type_lower == "buy":
                    tp_price = market_price + abs(tp_pips) * symbol_info.point
                else:
                    tp_price = market_price - abs(tp_pips) * symbol_info.point
            # Always set SL/TP if provided (AI trades must have them)
            if sl_price is not None:
                request["sl"] = sl_price
            if tp_price is not None:
                request["tp"] = tp_price

            logger.info(f"MT5 order request: {request}")
            # Send order
            result = mt5.order_send(request)
            logger.info(f"MT5 order result: {result}")
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {"success": False, "error": f"Order failed: {result.comment}"}
            
            logger.info(f"Order placed successfully: {result.order}")
            # Record trade in DB
            if user_id is not None:
                db = SessionLocal()
                try:
                    trade = Trade(
                        user_id=user_id,
                        symbol=symbol,
                        order_type=order_type,
                        entry_price=result.price,
                        stop_loss=sl_pips,
                        take_profit=tp_pips,
                        status='open',
                    )
                    db.add(trade)
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to record trade in DB: {e}")
                finally:
                    db.close()
            return {
                "success": True,
                "ticket": result.order,
                "symbol": symbol,
                "lot": lot,
                "type": order_type,
                "price": result.price,
                "sl": sl_pips,
                "tp": tp_pips
            }
            
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}", exc_info=True)
            return {"success": False, "error": f"An unexpected error occurred: {e}"}
    
    async def get_positions(self, symbol: str = None, magic_number: int = None) -> list:
        """
        Get all open positions, with optional filtering by symbol and/or magic number.
        """
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not available")
            return []
        
        if not self.connected:
            logger.warning("MT5 not connected")
            return []
        
        try:
            if symbol:
                if magic_number is not None:
                    positions = mt5.positions_get(symbol=symbol)
                    if positions:
                        return [p for p in positions if p.magic == magic_number]
                else:
                    return mt5.positions_get(symbol=symbol) or []
            else:
                if magic_number is not None:
                    positions = mt5.positions_get()
                    if positions:
                        return [p for p in positions if p.magic == magic_number]
                else:
                    positions = mt5.positions_get()
                    logger.info(f"Retrieved {len(positions) if positions else 0} positions from MT5")
                    return positions or []

        except Exception as e:
            logger.error(f"Error fetching positions: {e}", exc_info=True)
            return []
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        """Get pending orders."""
        if not MT5_AVAILABLE:
            return []
        
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
    
    async def close_position(self, ticket: int, user_id: int = None, reason: str = "manual") -> Dict[str, Any]:
        """Close a specific position and update trade in DB if user_id is provided. Logs the closure reason. Blocks non-manual closes for AI trades."""
        if not MT5_AVAILABLE:
            return {"success": False, "error": "MetaTrader5 package not available"}
        if not self.connected:
            return {"success": False, "error": "Not connected to MT5"}
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return {"success": False, "error": "Position not found"}
            position = position[0]
            # BLOCK: If AI trade and not manual close, do not allow
            if hasattr(position, 'magic') and position.magic == AIConfig.AI_MAGIC_NUMBER and reason != "manual":
                logger.warning(f"Blocked non-manual close attempt for AI trade ticket {ticket}.")
                return {"success": False, "error": "AI trades can only be closed manually or by SL/TP."}
            
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
            
            logger.info(f"Position {ticket} closed. Reason: {reason}. User: {user_id if user_id else 'N/A'}")
            # Update trade in DB
            if user_id is not None:
                db = SessionLocal()
                try:
                    trade = db.query(Trade).filter(Trade.user_id == user_id, Trade.symbol == position.symbol, Trade.status == 'open').order_by(Trade.created_at.desc()).first()
                    if trade:
                        trade.close_price = price
                        trade.status = 'closed'
                        trade.pnl = position.profit
                        db.commit()
                except Exception as e:
                    logger.error(f"Failed to update trade in DB: {e}")
                finally:
                    db.close()
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
        if not MT5_AVAILABLE:
            return {"success": False, "error": "MetaTrader5 package not available"}
            
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
        if not MT5_AVAILABLE:
            return None
        
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
            
            # Calculate spread in pips (standardized)
            if "JPY" in symbol:
                spread_pips = (tick.ask - tick.bid) / 0.01
            else:
                spread_pips = (tick.ask - tick.bid) / 0.0001
            
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
        if not MT5_AVAILABLE:
            return None
        
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

    async def modify_position(self, ticket: int, sl: float, tp: float) -> Dict[str, Any]:
        """Modify the Stop Loss and Take Profit of an open position."""
        if not MT5_AVAILABLE:
            return {"success": False, "error": "MetaTrader5 package not available"}
        if not self.connected:
            return {"success": False, "error": "Not connected to MT5"}

        try:
            # Get the position
            position = mt5.positions_get(ticket=ticket)
            if not position or len(position) == 0:
                return {"success": False, "error": f"Position with ticket {ticket} not found."}
            position = position[0]

            # Prepare the request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": sl,
                "tp": tp,
            }

            # Send the request
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Successfully modified position {ticket}. New SL: {sl}, New TP: {tp}")
                return {"success": True, "ticket": ticket, "sl": sl, "tp": tp}
            else:
                error_message = f"Failed to modify position {ticket}. Reason: {result.comment} (Code: {result.retcode})"
                logger.error(error_message)
                return {"success": False, "error": error_message}

        except Exception as e:
            error_message = f"An unexpected error occurred while modifying position {ticket}: {e}"
            logger.error(error_message, exc_info=True)
            return {"success": False, "error": error_message}

    async def get_pip_value(self, symbol: str, lot_size: float) -> float:
        """
        Calculates the value of one pip for a given symbol and lot size, for a USD account.
        """
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not available")
            return 0.0
            
        if not self.connected:
            logger.warning("MT5 not connected")
            return 0.0

        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger.error(f"Failed to get symbol info for {symbol}")
                return 0.0

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logger.error(f"Failed to get tick data for {symbol}")
                return 0.0

            # Use trade_contract_size instead of contract_size
            contract_size = getattr(symbol_info, 'trade_contract_size', 100000)  # Default to 100000 if not available
            point = symbol_info.point
            
            # Determine the pip size (e.g., 0.0001 for EURUSD, 0.01 for USDJPY)
            pip_size = point * 10 if "JPY" not in symbol else 0.01
            
            # Calculate the value of one pip in the quote currency
            pip_value_in_quote = pip_size * contract_size * lot_size

            quote_currency = symbol[3:]
            
            if quote_currency == 'USD':
                # If the quote currency is USD, the value is direct
                return pip_value_in_quote
            
            elif symbol.startswith('USD'):
                # For pairs like USD/JPY, USD/CAD
                return pip_value_in_quote / tick.ask

            else:
                # For cross pairs like EUR/GBP, GBP/JPY, we need to convert from quote to USD
                # We need the exchange rate for Quote/USD
                conversion_pair = f"{quote_currency}USD"
                conversion_tick = mt5.symbol_info_tick(conversion_pair)
                
                if conversion_tick:
                    return pip_value_in_quote * conversion_tick.ask
                else:
                    # If a direct conversion pair doesn't exist (e.g. AUDCAD -> CADUSD)
                    # try the inverse.
                    inverse_conversion_pair = f"USD{quote_currency}"
                    inverse_tick = mt5.symbol_info_tick(inverse_conversion_pair)
                    if inverse_tick:
                        return pip_value_in_quote / inverse_tick.ask
                    else:
                        logger.error(f"Cannot determine pip value for {symbol}. No USD conversion rate found for {quote_currency}.")
                        return 0.0
        except Exception as e:
            logger.error(f"Error calculating pip value for {symbol}: {e}")
            return 0.0

    async def get_candles(self, symbol: str, timeframe_str: str, count: int):
        """Fetches historical candle data from MT5."""
        if not self.connected:
            return None

        timeframe_map = {
            "1m": mt5.TIMEFRAME_M1,
            "5m": mt5.TIMEFRAME_M5,
            "15m": mt5.TIMEFRAME_M15,
            "30m": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "4h": mt5.TIMEFRAME_H4,
            "1d": mt5.TIMEFRAME_D1,
        }
        timeframe = timeframe_map.get(timeframe_str.lower())
        if timeframe is None:
            logger.error(f"Unsupported timeframe: {timeframe_str}")
            return None

        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"Could not fetch candle data for {symbol} on {timeframe_str}.")
                return None
            
            # Convert to pandas DataFrame for easier analysis
            import pandas as pd
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            logger.error(f"Error fetching candles for {symbol}: {e}", exc_info=True)
            return None

    async def get_server_time(self) -> datetime:
        """Get the current server/broker time from MT5. Returns UTC if not available."""
        if not MT5_AVAILABLE or not self.connected:
            return datetime.utcnow()
        try:
            server_time = mt5.symbol_info_tick(self.account_info.get('login', 'EURUSD')).time
            return datetime.utcfromtimestamp(server_time)
        except Exception as e:
            logger.error(f"Failed to fetch server time from MT5: {e}")
            return datetime.utcnow()

# Global MT5 service instance
mt5_service = MT5Service() 