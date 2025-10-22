import pandas as pd
from indicators.macd import Indicators
from api.adapter.adapter_api import APIAdapter
from core.event_bus import event_bus

class Strategy:
    """策略类，支持滑动窗口和MACD信号交易"""
    def __init__(self, adapter_api: APIAdapter, symbol, productType, marginCoin, window_size=100):
        self.adapter_api = adapter_api
        self.symbol = symbol
        self.productType = productType
        self.marginCoin = marginCoin
        self.event_bus = event_bus
        self.window_size = window_size
        self.candles_df = pd.DataFrame()  # 滑动窗口K线数据

        position = adapter_api.get_single_position(symbol, productType, marginCoin)
        if len(position["data"]) == 0:
            self.state = "toOrder"  # 初始等待下单状态
        else:
            if position["data"][0]["holdSide"] == "long":
                self.state = "ordered_long"  # 有一个多单
            if position["data"][0]["holdSide"] == "short":
                self.state = "ordered_short"  # 有一个空单
        print("当前开单状态:" + self.state)

        event_bus.on("candle_update", self.on_candle_update)

    def on_candle_update(self, candles):
        """
        WebSocket回调，每次推送新的K线数据
        candles: list[list] 格式的K线数据
        """
        df_new = pd.DataFrame(candles, columns=[
            "startTime","open","high","low","close","vol1","vol2","vol3"
        ])
        df_new[["open","high","low","close","vol1","vol2","vol3"]] = df_new[["open","high","low","close","vol1","vol2","vol3"]].astype(float)
        # float_cols = ["open","high","low","close","vol1","vol2","vol3"]
        # df_new.loc[:, float_cols] = df_new.loc[:, float_cols].astype(float)

        # columns=["startTime","open","high","low","close","vol1","vol2","vol3"]
        # df_new = pd.DataFrame(candles, columns)
        # df_new.loc[:, columns] = df_new.loc[:, columns].astype(float)

        # 初始化或累积滑动窗口
        if self.candles_df.empty:
            self.candles_df = df_new
        else:
            self.candles_df = pd.concat([self.candles_df, df_new], ignore_index=True)
        
        # 只保留最近 window_size 根K线
        self.candles_df = self.candles_df.iloc[-self.window_size:]

        # 计算MACD信号
        signal = self.macd_signal()

        # 执行交易逻辑
        if self.state == "toOrder":
            if signal == "long":
                print("📈 开多")
                self.order("buy", "open")
                self.state = "ordered_long"
            elif signal == "short":
                print("📉 开空")
                self.order("sell", "open")
                self.state = "ordered_short"
        elif self.state == "ordered_long":
            if signal == "short":
                print("平多")
                #一键平多
                self.close("long")
                #self.order("buy", "close")
                self.state = "toOrder"
        elif self.state == "ordered_short":
            if signal == "long":
                print("平空")
                #一键平空
                self.close("short")
                #self.order("sell", "close")
                self.state = "toOrder"
                


    def macd_signal(self):
        """计算MACD并判断买卖信号"""
        macd_df = Indicators.macd(self.candles_df)
        if macd_df.empty or len(macd_df) < 2:
            return "hold"
        # 取最近两根K线
        last, prev = macd_df.iloc[-1], macd_df.iloc[-2]
        # 金叉开多：DIF由下向上穿越DEA
        if prev["DIF"] < prev["DEA"] and last["DIF"] > last["DEA"]:
            return "long"
        # 死叉开空：DIF由上向下穿越DEA
        elif prev["DIF"] > prev["DEA"] and last["DIF"] < last["DEA"]:
            return "short"
        return "hold"

    def order(self, side, tradeSide):
        """开仓，side=buy开多, side=sell开空"""
        available = self.adapter_api.get_available(self.productType, self.marginCoin)
        if available < 10:
            print("⚠️ 余额不足，无法下单")
            return
        price = self.adapter_api.get_last_price(self.symbol, self.productType)
        size = self.adapter_api.get_open_size(self.symbol, self.productType, self.marginCoin, available/4, price, 20)
        result = self.adapter_api.place_order(self.symbol, self.productType, "crossed", self.marginCoin, price, size, side, "market", "GTC", None, None, tradeSide)


        
        print(result)

    #无关价格一键平仓
    def close(self, side):
        """平仓，side=long平多, side=short平空"""
        result = self.adapter_api.close_position(self.symbol, self.productType, side)
        print(result)
