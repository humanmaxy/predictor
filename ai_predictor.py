"""
AI趋势预测模块
使用DeepSeek API进行数字货币趋势预测和分析
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dotenv import load_dotenv
import openai

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class AIPredictor:
    """AI趋势预测器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化AI预测器
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = base_url or os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
        
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未设置，请在.env文件中设置DEEPSEEK_API_KEY")
        
        # 配置OpenAI客户端用于DeepSeek API
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info("AI预测器初始化完成")
    
    def prepare_market_data(self, df: pd.DataFrame, symbol: str) -> str:
        """
        准备市场数据用于AI分析
        
        Args:
            df: 包含技术指标的DataFrame
            symbol: 数字货币符号
            
        Returns:
            格式化的市场数据字符串
        """
        try:
            # 获取最新数据
            latest_data = df.tail(10)
            current_price = df['price'].iloc[-1]
            
            # 计算价格变化
            price_change_1d = ((df['price'].iloc[-1] - df['price'].iloc[-2]) / df['price'].iloc[-2] * 100) if len(df) > 1 else 0
            price_change_7d = ((df['price'].iloc[-1] - df['price'].iloc[-8]) / df['price'].iloc[-8] * 100) if len(df) > 7 else 0
            
            # 技术指标状态
            rsi_current = df['RSI'].iloc[-1] if 'RSI' in df.columns else None
            ma5_current = df['MA5'].iloc[-1] if 'MA5' in df.columns else None
            ma20_current = df['MA20'].iloc[-1] if 'MA20' in df.columns else None
            
            # 布林带位置
            bb_position = None
            if all(col in df.columns for col in ['BB_Upper', 'BB_Lower', 'price']):
                bb_upper = df['BB_Upper'].iloc[-1]
                bb_lower = df['BB_Lower'].iloc[-1]
                bb_range = bb_upper - bb_lower
                price_position = (current_price - bb_lower) / bb_range
                
                if price_position > 0.8:
                    bb_position = "接近上轨"
                elif price_position < 0.2:
                    bb_position = "接近下轨"
                else:
                    bb_position = "在中间区域"
            
            # MACD信号
            macd_signal = None
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
                macd_current = df['MACD'].iloc[-1]
                macd_signal_current = df['MACD_Signal'].iloc[-1]
                macd_signal = "金叉" if macd_current > macd_signal_current else "死叉"
            
            # 成交量趋势
            volume_trend = None
            if 'volume' in df.columns and len(df) > 5:
                recent_volume = df['volume'].tail(5).mean()
                previous_volume = df['volume'].iloc[-10:-5].mean() if len(df) > 10 else recent_volume
                volume_change = (recent_volume - previous_volume) / previous_volume * 100
                volume_trend = "放量" if volume_change > 20 else "缩量" if volume_change < -20 else "平稳"
            
            # 格式化数据
            market_summary = f"""
数字货币: {symbol}
当前价格: ${current_price:.4f}
1日涨跌幅: {price_change_1d:.2f}%
7日涨跌幅: {price_change_7d:.2f}%

技术指标分析:
- RSI: {rsi_current:.2f if rsi_current else 'N/A'} ({'超买' if rsi_current and rsi_current > 70 else '超卖' if rsi_current and rsi_current < 30 else '正常' if rsi_current else 'N/A'})
- MA5: ${ma5_current:.4f if ma5_current else 'N/A'}
- MA20: ${ma20_current:.4f if ma20_current else 'N/A'}
- MA趋势: {'多头排列' if ma5_current and ma20_current and ma5_current > ma20_current else '空头排列' if ma5_current and ma20_current else 'N/A'}
- 布林带位置: {bb_position or 'N/A'}
- MACD信号: {macd_signal or 'N/A'}
- 成交量: {volume_trend or 'N/A'}

最近10个交易周期价格走势:
{latest_data[['price']].to_string()}
            """
            
            return market_summary.strip()
            
        except Exception as e:
            logger.error(f"准备市场数据失败: {e}")
            raise
    
    def predict_trend(self, df: pd.DataFrame, symbol: str, 
                     prediction_days: int = 7) -> Dict:
        """
        预测价格趋势
        
        Args:
            df: 包含技术指标的DataFrame
            symbol: 数字货币符号
            prediction_days: 预测天数
            
        Returns:
            预测结果字典
        """
        try:
            # 准备市场数据
            market_data = self.prepare_market_data(df, symbol)
            
            # 构建预测提示
            prompt = f"""
你是一位专业的数字货币技术分析师。请基于以下市场数据对{symbol}进行{prediction_days}天的趋势预测和分析。

{market_data}

请从以下几个方面进行分析：
1. 技术面分析：基于技术指标（MA、RSI、MACD、布林带等）判断当前趋势
2. 短期预测：未来{prediction_days}天的价格走势预测
3. 关键支撑阻力位：重要的价格支撑和阻力位
4. 风险提示：潜在的风险因素
5. 交易建议：基于技术分析的交易策略建议

请用JSON格式返回分析结果，包含以下字段：
{{
    "trend_direction": "上涨/下跌/震荡",
    "confidence": "高/中/低",
    "target_price": 目标价格数值,
    "support_level": 支撑位价格,
    "resistance_level": 阻力位价格,
    "risk_level": "高/中/低",
    "trading_suggestion": "买入/卖出/观望",
    "analysis_summary": "详细分析总结",
    "key_factors": ["关键因素1", "关键因素2", "关键因素3"]
}}

请确保分析客观、专业，并基于技术指标数据进行判断。
"""
            
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一位专业的数字货币技术分析师，擅长基于技术指标进行趋势预测和风险分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # 解析响应
            ai_response = response.choices[0].message.content
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = ai_response[json_start:json_end]
                    prediction_result = json.loads(json_str)
                else:
                    raise ValueError("响应中未找到JSON格式")
                    
            except (json.JSONDecodeError, ValueError):
                # 如果JSON解析失败，创建默认结构
                logger.warning("AI响应JSON解析失败，使用文本解析")
                prediction_result = {
                    "trend_direction": "震荡",
                    "confidence": "中",
                    "target_price": df['price'].iloc[-1],
                    "support_level": df['price'].min() if len(df) > 0 else 0,
                    "resistance_level": df['price'].max() if len(df) > 0 else 0,
                    "risk_level": "中",
                    "trading_suggestion": "观望",
                    "analysis_summary": ai_response,
                    "key_factors": ["技术指标分析", "市场趋势", "风险控制"]
                }
            
            # 添加元数据
            prediction_result.update({
                "symbol": symbol,
                "prediction_date": datetime.now().isoformat(),
                "prediction_days": prediction_days,
                "current_price": float(df['price'].iloc[-1]),
                "data_points": len(df),
                "ai_model": "deepseek-chat"
            })
            
            logger.info(f"成功完成 {symbol} 的AI趋势预测")
            return prediction_result
            
        except Exception as e:
            logger.error(f"AI趋势预测失败: {e}")
            # 返回默认预测结果
            return {
                "symbol": symbol,
                "trend_direction": "数据不足",
                "confidence": "低",
                "target_price": float(df['price'].iloc[-1]) if len(df) > 0 else 0,
                "support_level": 0,
                "resistance_level": 0,
                "risk_level": "高",
                "trading_suggestion": "观望",
                "analysis_summary": f"预测失败: {str(e)}",
                "key_factors": ["数据获取错误"],
                "prediction_date": datetime.now().isoformat(),
                "prediction_days": prediction_days,
                "current_price": float(df['price'].iloc[-1]) if len(df) > 0 else 0,
                "data_points": len(df),
                "ai_model": "deepseek-chat",
                "error": str(e)
            }
    
    def analyze_multiple_coins(self, data_dict: Dict[str, pd.DataFrame], 
                             prediction_days: int = 7) -> Dict[str, Dict]:
        """
        分析多个数字货币
        
        Args:
            data_dict: 包含多个币种数据的字典
            prediction_days: 预测天数
            
        Returns:
            包含所有币种预测结果的字典
        """
        results = {}
        
        for symbol, df in data_dict.items():
            try:
                logger.info(f"开始分析 {symbol}")
                prediction = self.predict_trend(df, symbol, prediction_days)
                results[symbol] = prediction
                
                # API调用间隔，避免频率限制
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"分析 {symbol} 失败: {e}")
                results[symbol] = {
                    "symbol": symbol,
                    "error": str(e),
                    "trend_direction": "分析失败",
                    "confidence": "无",
                    "analysis_summary": f"分析失败: {str(e)}"
                }
        
        logger.info(f"完成 {len(results)} 个币种的分析")
        return results
    
    def generate_market_report(self, predictions: Dict[str, Dict]) -> str:
        """
        生成市场分析报告
        
        Args:
            predictions: 预测结果字典
            
        Returns:
            格式化的市场报告
        """
        try:
            report_lines = [
                f"数字货币市场分析报告",
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 50,
                ""
            ]
            
            # 统计概况
            total_coins = len(predictions)
            bullish_count = sum(1 for p in predictions.values() 
                              if p.get('trend_direction', '').lower() in ['上涨', 'bullish'])
            bearish_count = sum(1 for p in predictions.values() 
                              if p.get('trend_direction', '').lower() in ['下跌', 'bearish'])
            
            report_lines.extend([
                "市场概况:",
                f"- 分析币种数量: {total_coins}",
                f"- 看涨币种: {bullish_count}",
                f"- 看跌币种: {bearish_count}",
                f"- 震荡/其他: {total_coins - bullish_count - bearish_count}",
                ""
            ])
            
            # 各币种详细分析
            report_lines.append("详细分析:")
            for symbol, prediction in predictions.items():
                if 'error' in prediction:
                    report_lines.extend([
                        f"\n{symbol}:",
                        f"  分析状态: 失败 ({prediction.get('error', '未知错误')})"
                    ])
                    continue
                
                report_lines.extend([
                    f"\n{symbol}:",
                    f"  当前价格: ${prediction.get('current_price', 0):.4f}",
                    f"  趋势方向: {prediction.get('trend_direction', 'N/A')}",
                    f"  信心度: {prediction.get('confidence', 'N/A')}",
                    f"  目标价格: ${prediction.get('target_price', 0):.4f}",
                    f"  支撑位: ${prediction.get('support_level', 0):.4f}",
                    f"  阻力位: ${prediction.get('resistance_level', 0):.4f}",
                    f"  风险等级: {prediction.get('risk_level', 'N/A')}",
                    f"  交易建议: {prediction.get('trading_suggestion', 'N/A')}",
                ])
                
                # 关键因素
                key_factors = prediction.get('key_factors', [])
                if key_factors:
                    report_lines.append("  关键因素:")
                    for factor in key_factors:
                        report_lines.append(f"    - {factor}")
            
            report_lines.extend([
                "",
                "=" * 50,
                "免责声明: 本报告仅供参考，不构成投资建议。数字货币投资存在高风险，请谨慎决策。"
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"生成市场报告失败: {e}")
            return f"报告生成失败: {str(e)}"


if __name__ == "__main__":
    # 测试AI预测功能
    import sys
    sys.path.append('.')
    from data_fetcher import CryptoDataFetcher
    from technical_indicators import IndicatorAnalyzer
    
    try:
        # 检查环境变量
        if not os.getenv('DEEPSEEK_API_KEY'):
            print("请在.env文件中设置DEEPSEEK_API_KEY")
            print("示例: DEEPSEEK_API_KEY=your_api_key_here")
            exit(1)
        
        # 获取测试数据
        fetcher = CryptoDataFetcher()
        btc_data = fetcher.get_price_data('BTC', days=30)
        
        # 计算技术指标
        analyzer = IndicatorAnalyzer()
        indicators_data = analyzer.analyze_price_data(btc_data)
        
        # 创建AI预测器
        predictor = AIPredictor()
        
        # 测试单币种预测
        print("测试BTC趋势预测...")
        prediction = predictor.predict_trend(indicators_data, 'BTC', prediction_days=7)
        
        print(f"预测结果:")
        print(f"趋势方向: {prediction.get('trend_direction')}")
        print(f"信心度: {prediction.get('confidence')}")
        print(f"目标价格: ${prediction.get('target_price')}")
        print(f"交易建议: {prediction.get('trading_suggestion')}")
        
        print("\n分析摘要:")
        print(prediction.get('analysis_summary', ''))
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("请确保已正确配置DeepSeek API密钥")
