import json
import threading
import time
from websocket import WebSocketApp
from core.event_bus import event_bus


class BitgetWebSocket:
    def __init__(self, ws_url, proxy_host=None, proxy_port=None, proxy_type=None,
                 inst_type="SPOT", symbol="BTCUSDT", candle_interval="1m"):
        """
        inst_type: "USDT-FUTURES" / "SPOT" / "MARGIN" ...
        symbol:    交易对，如 "BTCUSDT"
        candle_interval: K线周期，"1m","5m","1H"
        """
        self.wsAPP = None
        self.ws_url = ws_url
        self.inst_type = inst_type
        self.symbol = symbol
        self.candle_interval = candle_interval
        self.reconnect_attempts = 0
        self.max_reconnects = 3
        self.stop_flag = False
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_type = proxy_type

    def _on_open(self, ws):
        print("✅ WebSocket 已连接")
        self.reconnect_attempts = 0
        sub_msg = {
            "op": "subscribe",
            "args": [{
                "instType": self.inst_type,
                "channel": f"candle{self.candle_interval}",
                "instId": self.symbol
            }]
        }
        ws.send(json.dumps(sub_msg))
        print("📡 已订阅:", sub_msg)
        # 发出连接成功事件
        import asyncio
        asyncio.run(event_bus.emit("system.ws_connected", {"symbol": self.symbol}))

    def _on_message(self, ws, message):
        try:
            msg = json.loads(message)
        except Exception as e:
            print("非 JSON 消息：", message, e)
            return

        # 触发 candle 更新事件
        if "data" in msg:
            import asyncio
            asyncio.run(event_bus.emit("market.candle_update", msg["data"]))

    def _on_error(self, ws, error):
        print("❌ WebSocket 错误:", error)
        import asyncio
        asyncio.run(event_bus.emit("system.ws_error", {"error": error}))

    def _on_close(self, ws, code, msg):
        if self.stop_flag:
            print("🛑 手动关闭 WebSocket，退出。")
            return

        print(f"⚠️ WebSocket 关闭: code={code}, msg={msg}")
        import asyncio
        asyncio.run(event_bus.emit("system.ws_closed", {"code": code, "msg": msg}))

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
        thread.start()
        return thread

    def close(self):
        self.stop_flag = True
        self.wsAPP.close()
