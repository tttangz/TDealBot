import pandas as pd

class Indicators:
    """通用指标计算类"""
    
    @staticmethod
    def macd(df: pd.DataFrame, short=12, long=26, signal=9):
        """
        计算 MACD 指标

        参数:
            df: DataFrame，必须包含 'close' 列
            short: 短期 EMA 周期
            long:  长期 EMA 周期
            signal: DEA 平滑周期

        返回:
            DataFrame，包含 'DIF', 'DEA', 'MACD'
        """

        # 计算 EMA
        ema_short = df["close"].ewm(span=short, adjust=False).mean()
        ema_long = df["close"].ewm(span=long, adjust=False).mean()

        # DIF = 快线
        dif = ema_short - ema_long
        # DEA = 慢线（DIF 的 EMA）
        dea = dif.ewm(span=signal, adjust=False).mean()
        # MACD = (DIF - DEA) * 2  （乘2是常见标准）
        macd = (dif - dea) * 2

        # 合并为 DataFrame
        result = pd.DataFrame({
            "DIF": dif,
            "DEA": dea,
            "MACD": macd
        })

        return result

    @staticmethod
    def ma(df: pd.DataFrame, period=20):
        """简单移动平均线"""
        return df["close"].rolling(window=period).mean()

    @staticmethod
    def rsi(df: pd.DataFrame, period=14):
        """计算 RSI 指标"""
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi