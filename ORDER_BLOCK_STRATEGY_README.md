# Order Block + RSI + Fibonacci Strategy Implementation

## Strategy Overview

This implementation provides a complete Order Block + RSI + Fibonacci trading strategy for the forex bot, designed to identify high-probability trading opportunities using institutional order flow concepts.

## Strategy Components

### 1. Order Block Detection
- **Break of Structure (BOS)**: Identifies when price breaks above/below previous swing highs/lows
- **Order Block Zones**: Locates the last opposing candle before the directional move
- **Volume Confirmation**: Uses volume to validate order block significance

### 2. Fibonacci Retracement Integration
- **Key Levels**: 38.2%, 50%, 61.8% retracement zones
- **Alignment Check**: Verifies order block alignment with Fibonacci levels
- **Swing Point Detection**: Automatically identifies swing highs and lows

### 3. RSI Confirmation
- **Oversold Condition**: RSI < 30 for buy signals
- **Overbought Condition**: RSI > 70 for sell signals
- **Period**: 14-period RSI calculation

## Strategy Conditions

### Buy Setup
1. ✅ Break of structure to the upside
2. ✅ Identify bullish Order Block (last bearish candle before bullish move)
3. ✅ Draw Fibonacci from swing low to high
4. ✅ OB aligns with 38.2%, 50%, or 61.8% retracement zone
5. ✅ RSI is below 30 (oversold)
6. ✅ Enter buy trade at OB zone

### Sell Setup
1. ✅ Break of structure to the downside
2. ✅ Identify bearish Order Block (last bullish candle before bearish move)
3. ✅ Draw Fibonacci from swing high to low
4. ✅ OB aligns with 38.2%, 50%, or 61.8% retracement zone
5. ✅ RSI is above 70 (overbought)
6. ✅ Enter sell trade at OB zone

## Risk Management

### Position Sizing
- **Risk Per Trade**: 10% of account balance
- **Max Trades Per Day**: 3 trades maximum
- **Max Daily Loss Limit**: 10% of account balance
- **Stop Trading**: Automatically stops when 10% drawdown is hit

### Trade Management
- **Entry**: At Order Block zone (Fibonacci level alignment)
- **Stop Loss**: Just beyond the order block or last swing
- **Take Profit**: 1:2 risk-reward ratio (next fair value gap/support-resistance)
- **Trailing Stop**: Optional after 1:1 risk-reward achieved

## Trading Sessions

### Optimal Trading Times
- **London Session**: 7 AM - 11 AM GMT
- **New York Session**: 12 PM - 4 PM GMT
- **Timeframe**: 5-Minute (M5) chart for entries

### Session Detection
The bot automatically detects trading sessions and adjusts strategy parameters accordingly.

## Implementation Files

### Core Strategy Files
- `app/services/order_block_strategy.py` - Main strategy implementation
- `app/utils/indicators.py` - Enhanced indicators (Fibonacci, ATR, etc.)
- `app/services/risk_service.py` - Risk management (10% per trade)
- `app/services/strategy_engine.py` - Strategy integration

### Signal Generation
- `app/services/signal_service.py` - Signal generation with Order Block priority
- `app/services/market_service.py` - Market data integration

## Usage Examples

### Basic Strategy Usage
```python
from app.services.order_block_strategy import order_block_strategy

# Analyze a pair for signals
signal = order_block_strategy.analyze_pair(price_data)
if signal:
    print(f"Signal: {signal['signal']}")
    print(f"Entry: {signal['entry_price']}")
    print(f"Stop Loss: {signal['stop_loss']}")
    print(f"Take Profit: {signal['take_profit']}")
```

### Risk Management Check
```python
from app.services.risk_service import risk_service

# Check if new position can be opened
can_trade, reason = risk_service.can_open_new_position(
    open_positions=1,
    daily_loss=-500,
    pair_correlation=0.3,
    account_balance=10000
)
print(f"Can trade: {can_trade}, Reason: {reason}")
```

### Session Detection
```python
from app.services.order_block_strategy import order_block_strategy

# Check if currently in trading session
in_session = order_block_strategy.is_trading_session()
print(f"In trading session: {in_session}")
```

## Configuration

### Strategy Parameters
```python
# Order Block Strategy Configuration
rsi_period = 14
rsi_oversold = 30
rsi_overbought = 70
fib_levels = [0.382, 0.5, 0.618]
lookback_period = 20
atr_period = 14

# Risk Management
risk_per_trade = 0.10  # 10%
max_trades_per_day = 3
max_daily_loss = 0.10  # 10%

# Trading Sessions
london_session = {'start': 7, 'end': 11}  # 7 AM - 11 AM GMT
ny_session = {'start': 12, 'end': 16}     # 12 PM - 4 PM GMT
```

## Testing

### Run Strategy Tests
```bash
cd forex-bot
python test_order_block_strategy.py
```

### Test Components
- ✅ Order Block detection
- ✅ Fibonacci level calculation
- ✅ RSI confirmation
- ✅ Risk management rules
- ✅ Session detection
- ✅ Signal generation

## Integration with Existing System

### Signal Priority
1. **High Priority**: Order Block + RSI + Fibonacci signals
2. **Medium Priority**: RSI oversold/overbought signals
3. **Low Priority**: Other technical indicators

### Database Integration
Signals are stored with strategy identification for performance tracking and analysis.

### Telegram Integration
Order Block signals are sent with detailed reasoning and risk management information.

## Performance Monitoring

### Key Metrics
- Win rate by strategy type
- Average risk-reward ratio
- Session performance (London vs NY)
- Daily loss tracking
- Trade frequency compliance

### Reporting
- Daily strategy performance reports
- Risk management compliance
- Session-based analysis
- Fibonacci level effectiveness

## Troubleshooting

### Common Issues
1. **No Signals Generated**: Check if in trading session and sufficient data
2. **Risk Management Blocking**: Verify daily limits and account balance
3. **Order Block Not Found**: Ensure sufficient price history and volume data

### Debug Mode
Enable detailed logging to troubleshoot strategy decisions:
```python
import logging
logging.getLogger('app.services.order_block_strategy').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
- Multi-timeframe confirmation
- Advanced order block patterns
- Machine learning signal validation
- Enhanced Fibonacci extensions
- Volume profile integration

### Customization Options
- Adjustable risk percentages
- Custom Fibonacci levels
- Session-specific parameters
- Strategy combination weights

## Support

For questions or issues with the Order Block strategy implementation:
1. Check the troubleshooting guide
2. Review the test files for examples
3. Examine the logging output for debugging
4. Verify configuration parameters

---

**Note**: This strategy is designed for educational and research purposes. Always test thoroughly in a demo environment before live trading. 