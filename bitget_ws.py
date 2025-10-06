import json
import threading
import time
from websocket import WebSocketApp


class BitgetWebSocket:
    def __init__(self, ws_url, proxy_host, proxy_port, proxy_type, inst_type, symbol, candle_interval, on_candle=None):
        """
        inst_type: "USDT-FUTURES" / "SPOT" / "MARGIN" ...
        symbol:    交易对，如 "BTCUSDT"
        candle_interval: K线周期，"1m","5m","1H"
        on_candle: 收到K线更新后的回调 (candle_data)
        """
        self.wsAPP = None
        self.ws_url = ws_url
        self.inst_type = inst_type
        self.symbol = symbol
        self.candle_interval = candle_interval
        self.on_candle = on_candle or (lambda msg: print("recv:", msg))
        self.reconnect_attempts = 0
        self.max_reconnects = 3
        self.stop_flag = False 
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_type = proxy_type

    def _on_open(self, ws):
        print("✅ WebSocket 已连接")
        self.reconnect_attempts = 0  # 成功连接后重置计数
        sub_msg = {
            "op": "subscribe",
            "args": [
                {
                    "instType": self.inst_type,
                    "channel": f"candle{self.candle_interval}",
                    "instId": self.symbol
                }
            ]
        }
        ws.send(json.dumps(sub_msg))
        print("📡 已订阅:", sub_msg)

    def _on_message(self, ws, message):
        try:
            msg = json.loads(message)
        except Exception as e:
            print("非 JSON 消息：", message, e)
            return
        if "data" in msg and self.on_candle:
            self.on_candle(msg["data"])  # 推送给策略

    def _on_error(self, ws, error):
        print("❌ WebSocket 错误:", error)

    def _on_close(self, ws, code, msg):
        if self.stop_flag:
            print("🛑 手动关闭 WebSocket，退出。")
            return
        print(f"⚠️ WebSocket 关闭: code={code}, msg={msg}")
        # 自动重连最多self.max_reconnects次
        if self.reconnect_attempts < self.max_reconnects:
            self.reconnect_attempts += 1
            delay = 3 * self.reconnect_attempts
            print(f"🔁 尝试第 {self.reconnect_attempts}/{self.max_reconnects} 次重连，{delay}s 后重试...")
            time.sleep(delay)
            self.connect()
        else:
            print("❌ 多次重连失败，程序退出。")

    def connect(self):
        self.wsAPP = WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        thread = threading.Thread(
            target=self.wsAPP.run_forever, 
            kwargs={
                "http_proxy_host": self.proxy_host,
                "http_proxy_port": self.proxy_port,
                "proxy_type": self.proxy_type,
                "ping_interval": 30,
                "ping_timeout": 10
            }
        )
        #thread.daemon = True
        thread.start()
        return thread

    def close(self):
        self.stop_flag = True
        self.wsAPP.close()