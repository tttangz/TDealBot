from api.adapter.adapter_api import APIAdapter
from websocket.adapter.adapter_ws import WebSocketAdapter
from strategy.strategy import Strategy
# ----------------------
# 1. 初始化 APIAdapter（完全不关心交易所内部实现）
# ----------------------
API_KEY = "xx"
API_SECRET = "xx"
PASSPHRASE = "xx"
TEST = True

strategy = Strategy(
    APIAdapter(
        "bitget",
        TEST,
        API_KEY,
        API_SECRET,
        PASSPHRASE,
        base_url="https://api.bitget.com"
    ),
    symbol="BTCUSDT", 
    productType="USDT-FUTURES", 
    marginCoin="USDT", 
    window_size=100
)

ws_client = WebSocketAdapter(
    "bitget",
    "wss://ws.bitget.com/v2/ws/public", 
    proxy_host="127.0.0.1", 
    proxy_port=10809, 
    proxy_type="http", 
    inst_type="USDT-FUTURES", 
    symbol="BTCUSDT", 
    candle_interval="15m"
)

thread = ws_client.ws.connect()
# 保持主线程活着
try:
    while thread.is_alive():
        thread.join(timeout=1)  # 主线程阻塞，可响应 Ctrl+C
except KeyboardInterrupt:
    print("手动中断，关闭 WebSocket...")
    ws_client.close()  # 安全关闭
    thread.join()      # 等待线程结束
    print("程序已退出")

# 总余额
# print(adapter_api.get_account("USDT-FUTURES"))
# USDT余额
# print(adapter_api.get_available("USDT-FUTURES", "USDT"))
# 行情
# print(adapter_api.get_ticker("BTCUSDT", "USDT-FUTURES", ))
# 当前BTC币本位价格
