# bitget_api.py
import time
import hmac
import hashlib
import base64
import requests
import json
from urllib.parse import urlencode

class BitgetApi:
    def __init__(self, test_flag, api_key, api_secret, passphrase, base_url="https://api.bitget.com"):
        """
        Bitget V2 API 封装
        :param api_key: API Key
        :param api_secret: API Secret
        :param passphrase: API Passphrase
        :param base_url: API 基础 URL, 默认实盘
        :param paptrading: 是否模拟盘, True 时自动加 header 'papertrading: 1'
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.base_url = base_url
        if test_flag:
            self.paptrading = "1"
        else:
            self.paptrading = "0"

    # -----------------------
    # 请求封装
    # -----------------------
    def _request(self, method, path, params=None, auth=False):
        """
        通用请求方法
        :param method: "GET" 或 "POST"
        :param path: 接口路径，例如 "/api/v2/mix/market/ticker"
        :param params: dict 格式的参数，GET 会拼到 URL，POST 会转 JSON
        :param auth: 是否需要签名
        """
        url = self.base_url + path
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["paptrading"] = self.paptrading
        query_string = ""
        body_str = ""

        if params:
            # GET 请求拼接 URL
            if method.upper() == "GET":
                query_string = urlencode(params)
                url += "?" + query_string
            else:
                # POST 请求转 JSON
                body_str = json.dumps(params)

        # 签名处理
        if auth:
            timestamp, sign = self._sign(method, path, query_string, body_str)
            headers.update({
                "ACCESS-KEY": self.api_key,
                "ACCESS-SIGN": sign,
                "ACCESS-TIMESTAMP": timestamp,
                "ACCESS-PASSPHRASE": self.passphrase,
            })

        # 发起请求
        resp = requests.request(
            method,
            url,
            json=params if method.upper() != "GET" else None,
            headers=headers,
            timeout=10
        )
        return resp.json()

    # -----------------------
    # 签名
    # -----------------------
    def _sign(self, method, request_path, query_string="", body_str=""):
        """
        按官方文档 v2 签名规则
        message = timestamp + method + requestPath + ("?" + queryString if queryString else "") + body
        Signature = base64( HMAC_SHA256(secret, message) )
        """
        timestamp = str(int(time.time() * 1000))
        msg = timestamp + method.upper() + request_path
        if query_string:
            msg += "?" + query_string
        if body_str:
            msg += body_str
        mac = hmac.new(self.api_secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
        sign = base64.b64encode(mac.digest()).decode()
        return timestamp, sign

    # -----------------------
    # 公共行情接口
    # -----------------------
    def get_ticker(self, symbol="BTCUSDT", productType="USDT-FUTURES"):
        path = "/api/v2/mix/market/ticker"
        params = {
            "symbol": symbol ,
            "productType": productType,
            }
        return self._request("GET", path, params=params, auth=False)

    def get_candles(self,
                    symbol: str,
                    productType: str,
                    granularity: str,
                    startTime: int = None,
                    endTime: int = None,
                    kLineType: str = None,
                    limit: int = None):
        """
        获取合约 K 线数据（Get Candlestick Data）

        :param symbol: 交易对符号，例如 "BTCUSDT"
        :param productType: 合约类型，如 "USDT-FUTURES"、"COIN-FUTURES"
        :param granularity: 周期，如 "1m", "5m", "15m", "1H", "4H" 等
        :param startTime: 查询起始时间，Unix 毫秒时间戳（可选）
        :param endTime: 查询结束时间，Unix 毫秒时间戳（可选）
        :param kLineType: K 线类型，可选，比如 "MARKET"、"MARK"、"INDEX"
        :param limit: 返回条数（可选，最大 1000）
        :return: 返回 JSON 格式接口响应
        """
        path = "/api/v2/mix/market/candles"
        params = {
            "symbol": symbol,
            "productType": productType,
            "granularity": granularity
        }
        if startTime is not None:
            params["startTime"] = str(startTime)
        if endTime is not None:
            params["endTime"] = str(endTime)
        if kLineType is not None:
            params["kLineType"] = kLineType
        if limit is not None:
            params["limit"] = str(limit)
        return self._request("GET", path, params=params, auth=False)

    # -----------------------
    # 账户接口
    # -----------------------
    def get_account(self, productType="USDT-FUTURES"):
        """
        查询合约账户信息
        :param productType: 例如 "USDT-FUTURES" 永续合约
        """
        path = "/api/v2/mix/account/accounts"
        params = {"productType": productType}
        return self._request("GET", path, params=params, auth=True)
    
    def get_open_size(self, symbol, productType, marginCoin, openAmount, openPrice, leverage = None):
        """
        获取预估可开数量接口（Est-Open-Count / open-count）
        :param symbol: 合约名称，例如 "BTCUSDT_UMCBL" 或 "ETHUSDT"
        :param productType: 合约类型，如 "USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES"
        :param marginCoin: 保证金币种，例如 "USDT"
        :param openAmount: 计划投入保证金数量（字符串格式）
        :param openPrice: 计划开仓价格（字符串格式）
        :param leverage: 杠杆倍数（字符串），可选，不填取默认值
        :return: 返回 JSON，内部 `data["size"]` 即预估张数（字符串）
        """
        path = "/api/v2/mix/account/open-count"
        params = {
            "symbol": symbol,
            "productType": productType,
            "marginCoin": marginCoin,
            "openAmount": openAmount,
            "openPrice": openPrice
        }
        if leverage is not None:
            params["leverage"] = leverage
        return self._request("GET", path, params=params, auth=True)
    
   
    # -----------------------
    # 单个合约持仓接口
    # -----------------------
    def get_single_position(self, symbol, productType, marginCoin):
        path = "/api/v2/mix/position/single-position"
        params = {
            "productType": productType,
            "symbol": symbol,
            "marginCoin": marginCoin,
            }
        return self._request("GET", path, params=params, auth=True)

    # ------------------------------
    # 下单接口
    # ------------------------------
    def place_order(self, symbol, productType, marginMode, marginCoin, price, size, side, order_type,  time_in_force="GTC", reduce_only=None, client_oid=None, tradeSide=None):
        """
        下单接口
        :param symbol: 合约名称，例如 BTCUSDT_UMCBL
        :param price: 价格
        :param size: 数量
        :param side: BUY 或 SELL
        :param order_type: LIMIT 或 MARKET
        :param margin_coin: 保证金币种，例如 USDT
        :param time_in_force: GTC/IOC/FOK
        :param reduce_only: 是否仅平仓
        :param client_oid: 客户端自定义订单 ID，可选
        """
        path = "/api/v2/mix/order/place-order"
        params_dict = {
            "symbol": symbol,
            "price": price,
            "productType":productType,
            "marginMode":marginMode,
            "marginCoin": marginCoin,
            "size": size,
            "side": side,
            "orderType": order_type,
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "clientOid": client_oid,
            "tradeSide": tradeSide,
        }
        return self._request("POST", path, params=params_dict, auth=True)

    # ------------------------------
    # 快速平仓接口
    # ------------------------------
    def close_position(self, symbol, productType, holdSide):
        """
        快速平仓接口
        :param symbol: 合约名称，例如 BTCUSDT_UMCBL
        :param margin_coin: 保证金币种，例如 USDT
        :param side: BUY 或 SELL
        :param size: 平仓数量
        :param client_oid: 客户端自定义订单 ID，可选
        """
        path = "/api/v2/mix/order/close-positions"
        params_dict = {
            "symbol": symbol,
            "productType": productType,
            "holdSide": holdSide,
        }
        return self._request("POST", path, params=params_dict, auth=True)