from api.bitget.bitget_api import BitgetApi
# 如果将来要接 OKX 或 Binance，可在这里 import 相应类

class APIAdapter:
    """
    通用接口适配类
    - 上层策略/主程序只需使用这个类
    - 内部根据交易所选择具体 API 实现
    """

    def __init__(self, exchange_name, test_flag, api_key, api_secret, passphrase, base_url=None):
        self.exchange_name = exchange_name.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase

        # 根据交易所选择具体 API 类
        if self.exchange_name == "bitget":
            self.api = BitgetApi(test_flag, api_key, api_secret, passphrase, base_url or "https://api.bitget.com")
        else:
            raise ValueError(f"暂不支持交易所: {exchange_name}")

    # -----------------------------
    # K线接口
    # -----------------------------
    def get_kline(self,symbol: str,
                    productType: str,
                    granularity: str,
                    startTime: int = None,
                    endTime: int = None,
                    kLineType: str = None,
                    limit: int = None):
        return self.api.get_kline(symbol, productType, granularity, startTime, endTime, kLineType, limit)

    # -----------------------------
    # 下单接口
    # -----------------------------
    def place_order(self, symbol, productType, marginMode, marginCoin, price, size, side, order_type, time_in_force="GTC", reduce_only=None, client_oid=None, tradeSide=None):
        return self.api.place_order(symbol, productType, marginMode, marginCoin, price, size, side, order_type, time_in_force, reduce_only, client_oid, tradeSide)

    # -----------------------------
    # 平仓接口
    # -----------------------------
    def close_position(self, symbol, productType, holdSide):
        return self.api.close_position(symbol, productType, holdSide)

    # -----------------------------
    # 行情接口
    # -----------------------------
    def get_ticker(self, symbol, productType):
        return self.api.get_ticker(symbol, productType)
    
    def get_last_price(self, symbol, productType):
        resp = self.get_ticker(symbol, productType)
        last_price = float(resp["data"][0]["lastPr"])
        return last_price
    
    

    # -----------------------------
    # 账户接口（统一入口）
    # product_type：
    # -----------------------------
    def get_account(self, productType="USDT-FUTURES"):
        # 返回所有账户记录
        return self.api.get_account(productType)
    
    # 单个合约持仓信息
    def get_single_position(self, symbol, productType, marginCoin):
        return self.api.get_single_position(symbol, productType, marginCoin)
    

    def get_available(self, productType="USDT-FUTURES", marginCoin="USDT"):
        # 返回账户某个币还有多少个
        account = self.get_account(productType)  
        for acc in account.get("data", []):
            if acc["marginCoin"] == marginCoin:
                available = float(acc["available"])
        return available
    
    def get_open_size(self, symbol="BTCUSDT", productType="USDT-FUTURES", marginCoin="USDT", openAmount=None, openPrice=None, leverage=None):
        # 计算合约可开张数
        size = self.api.get_open_size(symbol, productType, marginCoin, openAmount, openPrice, leverage)  # 返回所有账户记录
        return size["data"]["size"]