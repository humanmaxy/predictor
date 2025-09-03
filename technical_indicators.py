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
    def kdj_indicator(high: pd.Series, low: pd.Series, close: pd.Series, 
                     k_window: int = 14, d_window: int = 3, j_window: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        KDJ指标 (随机指标)
        
        Args:
            high: 最高价序列
            low: 最低价序列  
            close: 收盘价序列
            k_window: K值计算窗口，默认14
            d_window: D值计算窗口，默认3
            j_window: J值计算窗口，默认3
            
        Returns:
            (K值, D值, J值) 三个序列的元组
        """
        # 计算RSV (Raw Stochastic Value)
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        rsv = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # 计算K值 (使用指数移动平均)
        k_value = rsv.ewm(alpha=1/d_window).mean()
        
        # 计算D值 (K值的指数移动平均)
        d_value = k_value.ewm(alpha=1/j_window).mean()
        
        # 计算J值
        j_value = 3 * k_value - 2 * d_value
        
        return k_value, d_value, j_value
    
    @staticmethod
    def fibonacci_retracement(high_price: float, low_price: float) -> Dict[str, float]:
        """
        斐波那契回调位计算
        
        Args:
            high_price: 最高价
            low_price: 最低价
            
        Returns:
            斐波那契回调位字典
        """
        diff = high_price - low_price
        
        levels = {
            '0%': high_price,
            '23.6%': high_price - diff * 0.236,
            '38.2%': high_price - diff * 0.382,
            '50%': high_price - diff * 0.5,
            '61.8%': high_price - diff * 0.618,
            '78.6%': high_price - diff * 0.786,
            '100%': low_price
        }
        
        return levels
    
    @staticmethod
    def fibonacci_extension(high_price: float, low_price: float, retracement_price: float) -> Dict[str, float]:
        """
        斐波那契扩展位计算
        
        Args:
            high_price: 最高价
            low_price: 最低价
            retracement_price: 回调价格
            
        Returns:
            斐波那契扩展位字典
        """
        diff = high_price - low_price
        
        levels = {
            '127.2%': retracement_price + diff * 1.272,
            '161.8%': retracement_price + diff * 1.618,
            '200%': retracement_price + diff * 2.0,
            '261.8%': retracement_price + diff * 2.618
        }
        
        return levels
    
    @staticmethod
    def volume_analysis(volume: pd.Series, price: pd.Series, window: int = 20) -> pd.Series:
        """
        成交量分析
        
        Args:
            volume: 成交量序列
            price: 价格序列
            window: 计算窗口
            
        Returns:
            成交量相对强度序列
        """
        # 计算成交量移动平均
        volume_ma = volume.rolling(window=window).mean()
        
        # 成交量相对强度
        volume_ratio = volume / volume_ma
        
        return volume_ratio
    
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
            
            # 随机振荡器 (KD)
            k_percent, d_percent = self.indicators.stochastic_oscillator(
                result_df['high'], result_df['low'], result_df['close']
            )
            result_df['Stoch_K'] = k_percent
            result_df['Stoch_D'] = d_percent
            
            # KDJ指标
            kdj_k, kdj_d, kdj_j = self.indicators.kdj_indicator(
                result_df['high'], result_df['low'], result_df['close']
            )
            result_df['KDJ_K'] = kdj_k
            result_df['KDJ_D'] = kdj_d
            result_df['KDJ_J'] = kdj_j
            
            # 成交量分析
            if 'volume' in result_df.columns:
                result_df['Volume_Ratio'] = self.indicators.volume_analysis(
                    result_df['volume'], result_df['price']
                )
            
            # 威廉指标
            result_df['Williams_R'] = self.indicators.williams_r(
                result_df['high'], result_df['low'], result_df['close']
            )
            
            # ATR
            result_df['ATR'] = self.indicators.atr(
                result_df['high'], result_df['low'], result_df['close']
            )
            
            # 添加斐波那契分析
            result_df = self.add_fibonacci_analysis(result_df)
            
            logger.info(f"成功计算技术指标，数据形状: {result_df.shape}")
            return result_df
            
        except Exception as e:
            logger.error(f"技术指标计算失败: {e}")
            raise
    
    def add_fibonacci_analysis(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        添加斐波那契分析
        
        Args:
            df: 包含价格数据的DataFrame
            period: 分析周期
            
        Returns:
            添加斐波那契水平的DataFrame
        """
        try:
            result_df = df.copy()
            
            # 计算滚动的高低点
            rolling_high = df['high'].rolling(window=period).max()
            rolling_low = df['low'].rolling(window=period).min()
            
            # 计算斐波那契回调位
            fib_23_6 = rolling_high - (rolling_high - rolling_low) * 0.236
            fib_38_2 = rolling_high - (rolling_high - rolling_low) * 0.382
            fib_50_0 = rolling_high - (rolling_high - rolling_low) * 0.5
            fib_61_8 = rolling_high - (rolling_high - rolling_low) * 0.618
            
            result_df['Fib_23.6'] = fib_23_6
            result_df['Fib_38.2'] = fib_38_2
            result_df['Fib_50.0'] = fib_50_0
            result_df['Fib_61.8'] = fib_61_8
            result_df['Fib_High'] = rolling_high
            result_df['Fib_Low'] = rolling_low
            
            return result_df
            
        except Exception as e:
            logger.error(f"斐波那契分析失败: {e}")
            return df
    
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
            signals_df['KDJ_Signal'] = 0  # KDJ信号
            signals_df['Volume_Signal'] = 0  # 成交量信号
            signals_df['Fibonacci_Signal'] = 0  # 斐波那契信号
            
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
            
            # KDJ信号
            if all(col in signals_df.columns for col in ['KDJ_K', 'KDJ_D', 'KDJ_J']):
                # KDJ超买超卖信号
                kdj_oversold = (signals_df['KDJ_K'] < 20) & (signals_df['KDJ_D'] < 20)
                kdj_overbought = (signals_df['KDJ_K'] > 80) & (signals_df['KDJ_D'] > 80)
                
                # KDJ金叉死叉
                k_above_d = signals_df['KDJ_K'] > signals_df['KDJ_D']
                k_above_d_prev = k_above_d.shift(1)
                kdj_golden_cross = (~k_above_d_prev) & k_above_d & (signals_df['KDJ_K'] < 50)
                kdj_death_cross = k_above_d_prev & (~k_above_d) & (signals_df['KDJ_K'] > 50)
                
                signals_df.loc[kdj_oversold | kdj_golden_cross, 'KDJ_Signal'] = 1
                signals_df.loc[kdj_overbought | kdj_death_cross, 'KDJ_Signal'] = -1
            
            # 成交量信号
            if 'Volume_Ratio' in signals_df.columns:
                # 放量突破信号
                volume_breakout = signals_df['Volume_Ratio'] > 1.5
                volume_weak = signals_df['Volume_Ratio'] < 0.5
                
                signals_df.loc[volume_breakout, 'Volume_Signal'] = 1
                signals_df.loc[volume_weak, 'Volume_Signal'] = -1
            
            # 斐波那契信号
            if all(col in signals_df.columns for col in ['Fib_38.2', 'Fib_61.8', 'price']):
                # 价格在关键斐波那契位附近
                near_fib_382 = np.abs(signals_df['price'] - signals_df['Fib_38.2']) / signals_df['price'] < 0.01
                near_fib_618 = np.abs(signals_df['price'] - signals_df['Fib_61.8']) / signals_df['price'] < 0.01
                
                # 在斐波那契支撑位附近：买入信号
                at_support = near_fib_382 | near_fib_618
                signals_df.loc[at_support, 'Fibonacci_Signal'] = 1
            
            # 综合信号
            signal_columns = ['MA_Signal', 'BB_Signal', 'RSI_Signal', 'MACD_Signal_Trade', 
                            'KDJ_Signal', 'Volume_Signal', 'Fibonacci_Signal']
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
