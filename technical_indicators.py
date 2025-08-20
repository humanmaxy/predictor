"""
技术指标计算模块
包含移动平均线、布林带等常用技术指标
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def simple_moving_average(data: pd.Series, window: int) -> pd.Series:
        """
        简单移动平均线 (SMA)
        
        Args:
            data: 价格数据序列
            window: 移动窗口大小
            
        Returns:
            移动平均线序列
        """
        return data.rolling(window=window).mean()
    
    @staticmethod
    def exponential_moving_average(data: pd.Series, window: int) -> pd.Series:
        """
        指数移动平均线 (EMA)
        
        Args:
            data: 价格数据序列
            window: 移动窗口大小
            
        Returns:
            指数移动平均线序列
        """
        return data.ewm(span=window).mean()
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        布林带指标
        
        Args:
            data: 价格数据序列
            window: 移动窗口大小，默认20
            num_std: 标准差倍数，默认2.0
            
        Returns:
            (上轨, 中轨, 下轨) 三个序列的元组
        """
        # 中轨：简单移动平均线
        middle_band = data.rolling(window=window).mean()
        
        # 标准差
        std = data.rolling(window=window).std()
        
        # 上轨和下轨
        upper_band = middle_band + (std * num_std)
        lower_band = middle_band - (std * num_std)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """
        相对强弱指标 (RSI)
        
        Args:
            data: 价格数据序列
            window: 计算窗口，默认14
            
        Returns:
            RSI指标序列
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD指标
        
        Args:
            data: 价格数据序列
            fast: 快速EMA周期，默认12
            slow: 慢速EMA周期，默认26
            signal: 信号线EMA周期，默认9
            
        Returns:
            (MACD线, 信号线, 柱状图) 三个序列的元组
        """
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def stochastic_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_window: int = 14, d_window: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        随机振荡器 (KD指标)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            k_window: K值计算窗口，默认14
            d_window: D值计算窗口，默认3
            
        Returns:
            (K值, D值) 两个序列的元组
        """
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """
        威廉指标 (%R)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 计算窗口，默认14
            
        Returns:
            威廉指标序列
        """
        highest_high = high.rolling(window=window).max()
        lowest_low = low.rolling(window=window).min()
        
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        
        return williams_r
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """
        平均真实波动范围 (ATR)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 计算窗口，默认14
            
        Returns:
            ATR指标序列
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=window).mean()
        
        return atr


class IndicatorAnalyzer:
    """技术指标分析器"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        对价格数据进行完整的技术指标分析
        
        Args:
            df: 包含价格数据的DataFrame，需要包含'price'列
            
        Returns:
            添加了技术指标的DataFrame
        """
        try:
            result_df = df.copy()
            
            # 基础数据准备
            price = df['price']
            
            # 如果数据不足，创建模拟的高低价
            if 'high' not in df.columns:
                # 简单估算：假设高价比收盘价高1%，低价比收盘价低1%
                result_df['high'] = price * 1.01
                result_df['low'] = price * 0.99
                result_df['close'] = price
            else:
                result_df['close'] = price
            
            # 移动平均线
            result_df['MA5'] = self.indicators.simple_moving_average(price, 5)
            result_df['MA10'] = self.indicators.simple_moving_average(price, 10)
            result_df['MA20'] = self.indicators.simple_moving_average(price, 20)
            result_df['MA50'] = self.indicators.simple_moving_average(price, 50)
            
            # 指数移动平均线
            result_df['EMA12'] = self.indicators.exponential_moving_average(price, 12)
            result_df['EMA26'] = self.indicators.exponential_moving_average(price, 26)
            
            # 布林带
            bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(price)
            result_df['BB_Upper'] = bb_upper
            result_df['BB_Middle'] = bb_middle
            result_df['BB_Lower'] = bb_lower
            
            # RSI
            result_df['RSI'] = self.indicators.rsi(price)
            
            # MACD
            macd, signal, histogram = self.indicators.macd(price)
            result_df['MACD'] = macd
            result_df['MACD_Signal'] = signal
            result_df['MACD_Histogram'] = histogram
            
            # 随机振荡器
            k_percent, d_percent = self.indicators.stochastic_oscillator(
                result_df['high'], result_df['low'], result_df['close']
            )
            result_df['Stoch_K'] = k_percent
            result_df['Stoch_D'] = d_percent
            
            # 威廉指标
            result_df['Williams_R'] = self.indicators.williams_r(
                result_df['high'], result_df['low'], result_df['close']
            )
            
            # ATR
            result_df['ATR'] = self.indicators.atr(
                result_df['high'], result_df['low'], result_df['close']
            )
            
            logger.info(f"成功计算技术指标，数据形状: {result_df.shape}")
            return result_df
            
        except Exception as e:
            logger.error(f"技术指标计算失败: {e}")
            raise
    
    def get_trading_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于技术指标生成交易信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            添加交易信号的DataFrame
        """
        try:
            signals_df = df.copy()
            
            # 初始化信号列
            signals_df['MA_Signal'] = 0  # MA交叉信号
            signals_df['BB_Signal'] = 0  # 布林带信号
            signals_df['RSI_Signal'] = 0  # RSI信号
            signals_df['MACD_Signal_Trade'] = 0  # MACD信号
            
            # MA交叉信号 (金叉死叉)
            if 'MA5' in signals_df.columns and 'MA20' in signals_df.columns:
                # 过滤掉NaN值
                ma5_valid = signals_df['MA5'].notna()
                ma20_valid = signals_df['MA20'].notna()
                both_valid = ma5_valid & ma20_valid
                
                if both_valid.any():
                    ma5_above_ma20 = (signals_df['MA5'] > signals_df['MA20']) & both_valid
                    ma5_above_ma20_prev = ma5_above_ma20.shift(1)
                    
                    # 金叉：MA5从下方穿越MA20
                    golden_cross = (~ma5_above_ma20_prev) & ma5_above_ma20 & both_valid
                    # 死叉：MA5从上方跌破MA20
                    death_cross = ma5_above_ma20_prev & (~ma5_above_ma20) & both_valid
                    
                    signals_df.loc[golden_cross, 'MA_Signal'] = 1  # 买入信号
                    signals_df.loc[death_cross, 'MA_Signal'] = -1  # 卖出信号
            
            # 布林带信号
            if all(col in signals_df.columns for col in ['price', 'BB_Upper', 'BB_Lower']):
                # 价格触及下轨：买入信号
                touch_lower = signals_df['price'] <= signals_df['BB_Lower']
                # 价格触及上轨：卖出信号
                touch_upper = signals_df['price'] >= signals_df['BB_Upper']
                
                signals_df.loc[touch_lower, 'BB_Signal'] = 1
                signals_df.loc[touch_upper, 'BB_Signal'] = -1
            
            # RSI信号
            if 'RSI' in signals_df.columns:
                # RSI超卖：买入信号
                oversold = signals_df['RSI'] < 30
                # RSI超买：卖出信号
                overbought = signals_df['RSI'] > 70
                
                signals_df.loc[oversold, 'RSI_Signal'] = 1
                signals_df.loc[overbought, 'RSI_Signal'] = -1
            
            # MACD信号
            if 'MACD' in signals_df.columns and 'MACD_Signal' in signals_df.columns:
                # 过滤掉NaN值
                macd_valid = signals_df['MACD'].notna()
                signal_valid = signals_df['MACD_Signal'].notna()
                both_valid = macd_valid & signal_valid
                
                if both_valid.any():
                    macd_above_signal = (signals_df['MACD'] > signals_df['MACD_Signal']) & both_valid
                    macd_above_signal_prev = macd_above_signal.shift(1)
                    
                    # MACD上穿信号线：买入
                    macd_golden_cross = (~macd_above_signal_prev) & macd_above_signal & both_valid
                    # MACD下穿信号线：卖出
                    macd_death_cross = macd_above_signal_prev & (~macd_above_signal) & both_valid
                    
                    signals_df.loc[macd_golden_cross, 'MACD_Signal_Trade'] = 1
                    signals_df.loc[macd_death_cross, 'MACD_Signal_Trade'] = -1
            
            # 综合信号
            signal_columns = ['MA_Signal', 'BB_Signal', 'RSI_Signal', 'MACD_Signal_Trade']
            existing_signals = [col for col in signal_columns if col in signals_df.columns]
            
            if existing_signals:
                signals_df['Combined_Signal'] = signals_df[existing_signals].sum(axis=1)
                
                # 强买入信号 (>=2)
                signals_df['Strong_Buy'] = signals_df['Combined_Signal'] >= 2
                # 强卖出信号 (<=2)
                signals_df['Strong_Sell'] = signals_df['Combined_Signal'] <= -2
            
            logger.info("成功生成交易信号")
            return signals_df
            
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            raise


if __name__ == "__main__":
    # 测试技术指标计算
    import sys
    sys.path.append('.')
    from data_fetcher import CryptoDataFetcher
    
    try:
        # 获取测试数据
        fetcher = CryptoDataFetcher()
        btc_data = fetcher.get_price_data('BTC', days=30)
        
        # 计算技术指标
        analyzer = IndicatorAnalyzer()
        indicators_data = analyzer.analyze_price_data(btc_data)
        
        print("技术指标计算结果:")
        print(indicators_data[['price', 'MA5', 'MA20', 'BB_Upper', 'BB_Lower', 'RSI']].tail())
        
        # 生成交易信号
        signals_data = analyzer.get_trading_signals(indicators_data)
        print("\n交易信号:")
        print(signals_data[['price', 'MA_Signal', 'RSI_Signal', 'Combined_Signal']].tail())
        
    except Exception as e:
        print(f"测试失败: {e}")
