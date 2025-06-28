import MetaTrader5 as mt5
import pandas as pd
import time
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# --- CONFIGURATION ---
ACCOUNT = 94067211
PASSWORD = "IgS-7mAj"
SERVER = "MetaQuotes-Demo"
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
SYMBOL = "EURUSD"
LOT = 0.1
STOP_LOSS_PIPS = 20
TAKE_PROFIT_PIPS = 40
TIMEFRAME = mt5.TIMEFRAME_H1
MAGIC = 123456
ACCOUNT_SIZE = 1000

# --- LOGGING SETUP ---
logging.basicConfig(
    filename="mt5_trading_bot.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    filemode='a'
)

def log(msg):
    """Prints a message and logs it to the file."""
    print(msg)
    logging.info(msg)

# --- SIMPLE STRATEGY (No external dependencies) ---
def calculate_rsi(series, period=14):
    """Calculate RSI indicator."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def simple_strategy(df):
    """Simple RSI-based strategy that doesn't require external modules."""
    if len(df) < 50:
        return {'signal': None, 'confidence': 0, 'strategy': 'Insufficient data'}
    
    try:
        rsi = calculate_rsi(df['close'], 14)
        current_rsi = rsi.iloc[-1]
        
        # Simple RSI strategy
        if current_rsi < 30:
            return {
                'signal': 'buy', 
                'confidence': 70, 
                'strategy': 'RSI Oversold',
                'entry_zone': df['close'].iloc[-1],
                'stop_loss': df['close'].iloc[-1] - 0.0020,
                'take_profit': df['close'].iloc[-1] + 0.0040
            }
        elif current_rsi > 70:
            return {
                'signal': 'sell', 
                'confidence': 70, 
                'strategy': 'RSI Overbought',
                'entry_zone': df['close'].iloc[-1],
                'stop_loss': df['close'].iloc[-1] + 0.0020,
                'take_profit': df['close'].iloc[-1] - 0.0040
            }
        
        return {'signal': None, 'confidence': 0, 'strategy': 'No signal'}
    except Exception as e:
        log(f"Error in simple strategy: {e}")
        return {'signal': None, 'confidence': 0, 'strategy': f'Error: {e}'}

# --- MT5 CONNECTION ---
def connect():
    """Initializes and connects to the MetaTrader 5 terminal."""
    log(f"MT5 package version: {mt5.__version__}")
    
    # Shutdown any existing connection
    mt5.shutdown()
    time.sleep(2)
    
    # Method 1: Try to connect to running terminal
    log("Method 1: Attempting to connect to a running MT5 terminal...")
    if mt5.initialize():
        log("✓ Connected to running MT5 terminal!")
    else:
        error = mt5.last_error()
        log(f"✗ Failed to connect to running MT5 terminal. Error: {error}")
        
        # Method 2: Try to launch terminal with explicit path
        log("Method 2: Trying to launch MT5 terminal with explicit path...")
        if not mt5.initialize(path=MT5_PATH):
            error = mt5.last_error()
            log(f"✗ Failed to launch terminal with path. Error: {error}")
            
            # Method 3: Try with server credentials
            log("Method 3: Trying to connect with server credentials...")
            if not mt5.initialize(server=SERVER, login=ACCOUNT, password=PASSWORD):
                error = mt5.last_error()
                log(f"✗ All connection methods failed. Error: {error}")
                log("\nTroubleshooting tips:")
                log("1. Make sure MT5 terminal is installed and running")
                log("2. Verify your account credentials")
                log("3. Check if the server name is correct")
                log("4. Try running MT5 as administrator")
                log("5. Check if antivirus is blocking the connection")
                mt5.shutdown()
                return False
            else:
                log("✓ Connected with server credentials!")

    log("MT5 initialized successfully.")
    
    # Test login if not already logged in
    account_info = mt5.account_info()
    if account_info is None:
        log("Attempting to login with credentials...")
        if not mt5.login(login=ACCOUNT, password=PASSWORD, server=SERVER):
            error = mt5.last_error()
            log(f"✗ Login failed: {error}")
            log("Please verify your account credentials and server name.")
            mt5.shutdown()
            return False
        else:
            log("✓ Login successful!")
            account_info = mt5.account_info()
    
    terminal_info = mt5.terminal_info()
    if not terminal_info:
        log(f"Failed to get terminal info: {mt5.last_error()}")
        mt5.shutdown()
        return False
    log(f"Connected to MT5 terminal: {terminal_info.name} (build {terminal_info.build})")

    if account_info is None:
        log(f"Failed to get account info: {mt5.last_error()}")
        mt5.shutdown()
        return False
        
    log(f"Connected to account #{account_info.login} on {account_info.server}.")
    log(f"Account Balance: ${account_info.balance:.2f}")
    log(f"Account Equity: ${account_info.equity:.2f}")
    return True

def shutdown():
    """Shuts down the connection to the MetaTrader 5 terminal."""
    mt5.shutdown()
    log("Disconnected from MT5.")

# --- DATA FETCHING ---
def get_rates(symbol, timeframe, n=250):
    """Fetches historical price data from MT5."""
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
        if rates is None or len(rates) < 200:
            log(f"Could not get {n} bars for {symbol}, got {len(rates) if rates is not None else 0}")
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    except Exception as e:
        log(f"Error fetching rates: {e}")
        return None

# --- POSITION & ORDER MANAGEMENT ---
def close_opposite_positions(symbol, signal_type):
    """Closes all positions that are opposite to the new signal."""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        return # No positions to close

    opposite_type = mt5.POSITION_TYPE_SELL if signal_type == "buy" else mt5.POSITION_TYPE_BUY
    
    for pos in positions:
        if pos.type == opposite_type:
            log(f"Closing opposite position {pos.ticket}...")
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_BUY if pos.type == mt5.POSITION_TYPE_SELL else mt5.ORDER_TYPE_SELL,
                "position": pos.ticket,
                "deviation": 20,
                "magic": MAGIC,
                "comment": "Closing opposite trade"
            }
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                log(f"Failed to close position {pos.ticket}: {result.comment}")
            else:
                log(f"Position {pos.ticket} closed successfully.")

def execute_trade(symbol, signal_type, lot, entry_price, stop_loss, take_profit):
    """Executes a trade based on the signal and custom entry/SL/TP."""
    point = mt5.symbol_info(symbol).point
    if signal_type == "buy":
        order_type = mt5.ORDER_TYPE_BUY
        price = entry_price
        sl = stop_loss
        tp = take_profit
    elif signal_type == "sell":
        order_type = mt5.ORDER_TYPE_SELL
        price = entry_price
        sl = stop_loss
        tp = take_profit
    else:
        return # Invalid signal type

    log(f"Executing {signal_type} order for {symbol} at {price} with SL={sl} TP={tp}")
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC,
        "comment": "Simple RSI Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log(f"Order send failed, retcode={result.retcode}, comment: {result.comment}")
    else:
        log(f"Order sent successfully, ticket #{result.order}")
    return result

# --- RISK MANAGEMENT ---
trades_today = 0
max_trades_per_day = 3
max_daily_loss = 0.10  # 10% drawdown
initial_balance = ACCOUNT_SIZE
current_drawdown = 0.0

def in_trading_session():
    """Check if current time is within trading session."""
    now = datetime.now(timezone.utc)
    hour = now.hour
    # London: 7-11 GMT, NY: 12-16 GMT
    return (7 <= hour < 11) or (12 <= hour < 16)

def calculate_lot_size(balance, risk_percent, entry, stop, symbol):
    """Calculate position size based on risk management."""
    risk_amount = balance * risk_percent
    pip_distance = abs(entry - stop)
    if pip_distance == 0:
        return 0.01  # fallback
    # Simplified lot calculation
    lot = risk_amount / (pip_distance * 10000)  # Assuming 1 pip = $10 for 1 lot
    return max(0.01, round(lot, 2))

def get_closed_trades_today():
    """Get closed trades for today."""
    today = datetime.now(timezone.utc).date()
    history = mt5.history_deals_get(datetime(today.year, today.month, today.day), datetime.now(timezone.utc))
    if history is None:
        return []
    return [deal for deal in history if deal.magic == MAGIC]

def get_daily_pnl():
    """Calculate daily P&L."""
    deals = get_closed_trades_today()
    pnl = sum(deal.profit for deal in deals)
    return pnl

# --- MAIN BOT LOOP ---
def run_bot():
    global trades_today, current_drawdown
    log("Starting MT5 Trading Bot...")
    
    if not connect():
        log("Failed to connect to MT5. Exiting.")
        return

    try:
        while True:
            # Check for a new bar
            current_time = datetime.now(timezone.utc)
            if current_time.second == 0:
                if not in_trading_session():
                    log("Outside trading session. No trades will be taken.")
                    time.sleep(1)
                    continue
                
                # Update drawdown and trades_today from closed trades
                daily_pnl = get_daily_pnl()
                current_drawdown = -daily_pnl / initial_balance
                trades_today = len(get_closed_trades_today())
                
                if trades_today >= max_trades_per_day:
                    log("Max trades per day reached. No more trades today.")
                    time.sleep(1)
                    continue
                    
                if current_drawdown >= max_daily_loss:
                    log("Max daily loss hit. Stopping trading for the day.")
                    time.sleep(1)
                    continue
                
                df = get_rates(SYMBOL, TIMEFRAME)
                if df is not None:
                    try:
                        strat_result = simple_strategy(df)
                        signal = strat_result.get('signal')
                        if signal in ('buy', 'sell'):
                            log(f"=== SIGNAL DETECTED: {signal.upper()} ===")
                            log(f"Strategy: {strat_result.get('strategy')}")
                            log(f"Entry: {strat_result.get('entry_zone')}, SL: {strat_result.get('stop_loss')}, TP: {strat_result.get('take_profit')}")
                            
                            close_opposite_positions(SYMBOL, signal)
                            
                            account_info = mt5.account_info()
                            balance = account_info.balance if account_info else initial_balance
                            
                            # Dynamic lot sizing
                            lot = calculate_lot_size(
                                balance, 0.10, strat_result.get('entry_zone'), strat_result.get('stop_loss'), SYMBOL
                            )
                            
                            result = execute_trade(
                                SYMBOL, signal, lot,
                                strat_result.get('entry_zone'),
                                strat_result.get('stop_loss'),
                                strat_result.get('take_profit')
                            )
                            log(f"Trade executed with lot size: {lot}")
                        else:
                            log("No new trading signal.")
                    except Exception as e:
                        log(f"Error in strategy execution: {e}")
                else:
                    log("Could not retrieve market data.")
            
            time.sleep(1)

    except KeyboardInterrupt:
        log("Bot stopped by user.")
    except Exception as e:
        log(f"An unexpected error occurred: {e}")
    finally:
        shutdown()

if __name__ == "__main__":
    run_bot() 