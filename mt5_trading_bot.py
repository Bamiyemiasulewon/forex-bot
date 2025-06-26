import MetaTrader5 as mt5
import pandas as pd
import time
import logging
from datetime import datetime, timedelta, timezone
from app.services.strategy_engine import order_block_rsi_fib_strategy

# --- CONFIGURATION ---
ACCOUNT = 10006802801
PASSWORD = "_b6pOTw"
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
    filemode='a' # Append to the log file
)

def log(msg):
    """Prints a message and logs it to the file."""
    print(msg)
    logging.info(msg)

# --- MT5 CONNECTION ---
def connect():
    """Initializes and connects to the MetaTrader 5 terminal."""
    log(f"MT5 package version: {mt5.__version__}")
    
    log("Waiting 5 seconds before attempting to connect to MT5 terminal...")
    time.sleep(5)
    
    log("Attempting to connect to a running MT5 terminal (no path)...")
    if mt5.initialize():
        log("Connected to running MT5 terminal!")
    else:
        log(f"Failed to connect to running MT5 terminal. Error: {mt5.last_error()}")
        log("Trying to launch MT5 terminal with explicit path...")
        if not mt5.initialize(path=MT5_PATH):
            log(f"Initialization failed. Could not connect to or launch MT5 terminal. Error code: {mt5.last_error()}")
            log("Please ensure the MT5 terminal is installed at the specified path and you have permission to launch it.")
            mt5.shutdown()
            return False
        else:
            log("Launched and connected to MT5 terminal!")

    log("MT5 initialized successfully.")
    
    terminal_info = mt5.terminal_info()
    if not terminal_info:
        log(f"Failed to get terminal info: {mt5.last_error()}")
        mt5.shutdown()
        return False
    log(f"Connected to MT5 terminal: {terminal_info.name} (build {terminal_info.build})")

    account_info = mt5.account_info()
    if account_info is None:
        log(f"Failed to get account info: {mt5.last_error()}")
        mt5.shutdown()
        return False
        
    log(f"Connected to account #{account_info.login} on {account_info.server}.")
    log(f"Account Info: {account_info}")
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

# --- TRADING STRATEGY ---
# def check_crossover_signal(df):
#     ... (old code commented out)

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
        "comment": "Order Block + RSI + Fib Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log(f"Order send failed, retcode={result.retcode}, comment: {result.comment}")
    else:
        log(f"Order sent successfully, ticket #{result.order}")
    return result

# --- RISK MANAGEMENT & SESSION FILTERS ---
trades_today = 0
max_trades_per_day = 3
max_daily_loss = 0.10  # 10% drawdown
initial_balance = ACCOUNT_SIZE
current_drawdown = 0.0
from datetime import datetime as dt

def in_trading_session():
    now = dt.utcnow()
    hour = now.hour
    # London: 7-11 GMT, NY: 12-16 GMT
    return (7 <= hour < 11) or (12 <= hour < 16)

# --- HELPER FUNCTIONS FOR RISK & TRADE MANAGEMENT ---
def get_pip_value(symbol, lot):
    info = mt5.symbol_info(symbol)
    if info is None:
        return 10.0  # fallback
    # For most FX pairs, pip = 0.0001, pip value = lot * contract size * pip
    pip = 0.0001 if info.digits == 5 or info.digits == 4 else 0.01
    return lot * info.trade_contract_size * pip

def calculate_lot_size(balance, risk_percent, entry, stop, symbol):
    risk_amount = balance * risk_percent
    pip_distance = abs(entry - stop)
    pip_value_per_lot = get_pip_value(symbol, 1.0)
    if pip_distance == 0 or pip_value_per_lot == 0:
        return 0.01  # fallback
    lot = risk_amount / (pip_distance * pip_value_per_lot)
    return max(0.01, round(lot, 2))

def get_closed_trades_today():
    today = datetime.utcnow().date()
    history = mt5.history_deals_get(datetime(today.year, today.month, today.day), datetime.utcnow())
    if history is None:
        return []
    return [deal for deal in history if deal.magic == MAGIC]

def get_daily_pnl():
    deals = get_closed_trades_today()
    pnl = sum(deal.profit for deal in deals)
    return pnl

def update_trailing_stop(symbol, signal_type, entry, stop, rr=1.0):
    positions = mt5.positions_get(symbol=symbol)
    if not positions:
        return
    for pos in positions:
        if pos.magic != MAGIC:
            continue
        # For buy, trail SL to entry after 1:1 RR; for sell, vice versa
        if signal_type == 'buy':
            if pos.price_current >= entry + (entry - stop) * rr:
                if pos.sl < entry:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": entry,
                        "tp": pos.tp,
                        "symbol": symbol,
                        "magic": MAGIC,
                        "comment": "Trailing SL to BE"
                    }
                    mt5.order_send(request)
        elif signal_type == 'sell':
            if pos.price_current <= entry - (stop - entry) * rr:
                if pos.sl > entry:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": entry,
                        "tp": pos.tp,
                        "symbol": symbol,
                        "magic": MAGIC,
                        "comment": "Trailing SL to BE"
                    }
                    mt5.order_send(request)

# --- MAIN BOT LOOP ---
def run_bot():
    global trades_today, current_drawdown
    log("Starting MT5 Trading Bot...")
    if not connect():
        return # Cannot start if connection fails

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
                    strat_result = order_block_rsi_fib_strategy(df)
                    signal = strat_result.get('signal')
                    if signal in ('buy', 'sell'):
                        log(f"=== SIGNAL DETECTED: {signal.upper()} ===")
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
                else:
                    log("Could not retrieve market data.")
            # Trailing stop management for open trades
            df = get_rates(SYMBOL, TIMEFRAME)
            if df is not None:
                strat_result = order_block_rsi_fib_strategy(df)
                signal = strat_result.get('signal')
                if signal in ('buy', 'sell'):
                    update_trailing_stop(
                        SYMBOL, signal,
                        strat_result.get('entry_zone'),
                        strat_result.get('stop_loss'),
                        rr=1.0
                    )
            time.sleep(1)

    except KeyboardInterrupt:
        log("Bot stopped by user.")
    except Exception as e:
        log(f"An unexpected error occurred: {e}")
    finally:
        shutdown()

if __name__ == "__main__":
    run_bot() 