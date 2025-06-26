import MetaTrader5 as mt5

if mt5.initialize(
    server="MexAtlantic-Demo",
    login=90404609,
    password="Mt1ms4Q*"
):
    print("Success!")
    print("Terminal:", mt5.terminal_info())
    mt5.shutdown()
else:
    print(f"Error: {mt5.last_error()}") 