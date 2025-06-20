def format_signal_alert(pair, action, entry, sl, tp1, tp2, rr, confidence, strategy):
    return f"""
🔔 FOREX SIGNAL ALERT
💱 Pair: {pair} | 📊 Action: {action}\n💰 Entry: {entry} | 🛑 SL: {sl}\n🎯 TP1: {tp1} | 🎯 TP2: {tp2}\n📈 R:R: {rr} | ⚡ Confidence: {confidence}%\n📋 Strategy: {strategy}
""".strip()

def format_entry_signal(signal_id, pair, action, entry, sl, tp1, tp2, rr, confidence, rationale):
    return f"""
🎯 SIGNAL #{signal_id}
💱 {pair} {action} | 💰 Entry: {entry}\n🛑 SL: {sl} | 🎯 TP1: {tp1} | TP2: {tp2}\n📈 R:R: {rr} | ⚡ Confidence: {confidence}%\n💡 {rationale}\n#{pair.replace('/', '')} #{action.upper()}
""".strip()

def format_trade_result(pair, action, entry, exit, pips, duration, percent, signal_id, rating):
    return f"""
✅ {pair} {action} CLOSED
📊 Entry: {entry} → Exit: {exit}\n💰 {pips} pips PROFIT | ⏱️ {duration}\n📈 {percent}% return\n🎊 Signal #{signal_id} - Rating: {rating}
""".strip()

def format_performance(stats):
    return f"""
📊 DAILY PERFORMANCE
✅ Signals: {stats['signals']} | 🎯 Targets Hit: {stats['targets_hit']} | ❌ Stops: {stats['stops']}\n📈 Win Rate: {stats['win_rate']:.1f}% | 💰 Pips: {stats['pips']}\n📊 R:R: {stats['rr']:.2f} | ⭐ Score: {stats['score']}/10
""".strip()

def format_educational_tip(title, content, pro_tip):
    return f"""
📚 FOREX TIP: {title}
{content}\n💡 Pro Tip: {pro_tip}
""".strip() 