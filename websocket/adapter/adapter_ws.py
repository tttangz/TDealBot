from bitget_ws import BitgetWebSocket

class WebSocketAdapter:
    def __init__(self, exchange_name, ws_url, proxy_host=None, proxy_port=None, proxy_type=None,
                 inst_type="SPOT", symbol="BTCUSDT", candle_interval="1m"):
        self.exchange_name = exchange_name.lower()

        # 根据交易所选择具体 API 类
        if self.exchange_name == "bitget":
            self.ws = BitgetWebSocket(ws_url, proxy_host, proxy_port, proxy_type, inst_type, symbol, candle_interval)
        else:
            raise ValueError(f"暂不支持交易所: {exchange_name}")