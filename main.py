from adapter_api import APIAdapter
from bitget_ws import BitgetWebSocket
from strategy import Strategy
import time
# ----------------------
# 1. 初始化 APIAdapter（完全不关心交易所内部实现）
# ----------------------
API_KEY = "bg_9c95b568e303c94288691867695b44e4"
API_SECRET = "1c008b114f40f20d9c97cc155df7c7d519ab77ae61e8b8e7280f88d28f70c99e"
PASSPHRASE = "492513492513"
TEST = True

adapter_api = APIAdapter(
    "bitget",
    TEST,
    API_KEY,
    API_SECRET,
    PASSPHRASE,
    base_url="https://api.bitget.com"
)
strategy = Strategy(adapter_api, symbol="BTCUSDT", productType="USDT-FUTURES", marginCoin="USDT", window_size=100)

ws_client = BitgetWebSocket("wss://ws.bitget.com/v2/ws/public", proxy_host="127.0.0.1", proxy_port=10809, proxy_type="http", inst_type="USDT-FUTURES", symbol="BTCUSDT", candle_interval="15m", on_candle=strategy.run)
thread = ws_client.connect()
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