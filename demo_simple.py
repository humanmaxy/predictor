#!/usr/bin/env python3
"""
简化版演示脚本
展示系统核心逻辑，不依赖外部包
"""

import json
import os
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_technical_analysis_logic():
    """演示技术分析逻辑"""
    print("=" * 60)
    print("📈 技术分析逻辑演示")
    print("=" * 60)
    
    # 模拟价格数据
    prices = [
        45000, 45200, 44800, 45500, 46000, 45800, 46200, 46500,
        46800, 46300, 46700, 47000, 46500, 46800, 47200, 47500,
        47800, 47300, 47600, 48000, 47700, 48200, 48500, 48800
    ]
    
    print(f"📊 模拟BTC价格数据 (最近24小时):")
    print(f"价格范围: ${min(prices):.0f} - ${max(prices):.0f}")
    print(f"当前价格: ${prices[-1]:.0f}")
    print(f"24小时涨跌: {((prices[-1] - prices[0]) / prices[0] * 100):.2f}%")
    
    # 简单移动平均线计算
    def calculate_ma(data, period):
        if len(data) < period:
            return None
        return sum(data[-period:]) / period
    
    ma5 = calculate_ma(prices, 5)
    ma20 = calculate_ma(prices, 20)
    
    print(f"\n📊 移动平均线:")
    print(f"MA5: ${ma5:.2f}")
    print(f"MA20: ${ma20:.2f}")
    print(f"趋势: {'多头排列' if ma5 > ma20 else '空头排列'}")
    
    # 简单RSI计算
    def calculate_simple_rsi(prices, period=14):
        if len(prices) < period + 1:
            return 50  # 默认值
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    rsi = calculate_simple_rsi(prices)
    print(f"\n📊 RSI指标:")
    print(f"RSI: {rsi:.2f}")
    
    if rsi > 70:
        rsi_signal = "超买，考虑卖出"
    elif rsi < 30:
        rsi_signal = "超卖，考虑买入"
    else:
        rsi_signal = "正常区间"
    print(f"RSI信号: {rsi_signal}")
    
    # 布林带计算
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        if len(prices) < period:
            return None, None, None
        
        recent_prices = prices[-period:]
        ma = sum(recent_prices) / period
        
        variance = sum((p - ma) ** 2 for p in recent_prices) / period
        std = variance ** 0.5
        
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        
        return upper, ma, lower
    
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)
    current_price = prices[-1]
    
    print(f"\n📊 布林带:")
    print(f"上轨: ${bb_upper:.2f}")
    print(f"中轨: ${bb_middle:.2f}")
    print(f"下轨: ${bb_lower:.2f}")
    
    # 布林带位置
    if bb_upper and bb_lower:
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
        if bb_position > 0.8:
            bb_signal = "接近上轨，考虑卖出"
        elif bb_position < 0.2:
            bb_signal = "接近下轨，考虑买入"
        else:
            bb_signal = "在正常区间"
        print(f"位置: {bb_position:.1%} ({bb_signal})")
    
    # 综合信号分析
    signals = []
    if ma5 > ma20:
        signals.append("MA多头")
    else:
        signals.append("MA空头")
    
    if rsi > 70:
        signals.append("RSI超买")
    elif rsi < 30:
        signals.append("RSI超卖")
    
    if bb_position > 0.8:
        signals.append("布林上轨")
    elif bb_position < 0.2:
        signals.append("布林下轨")
    
    print(f"\n🚨 综合信号: {', '.join(signals)}")
    
    return {
        'price': current_price,
        'ma5': ma5,
        'ma20': ma20,
        'rsi': rsi,
        'bb_upper': bb_upper,
        'bb_lower': bb_lower,
        'signals': signals
    }

def demo_ai_analysis_logic(market_data):
    """演示AI分析逻辑"""
    print("\n" + "=" * 60)
    print("🤖 AI分析逻辑演示")
    print("=" * 60)
    
    # 模拟AI分析过程
    price = market_data['price']
    ma5 = market_data['ma5']
    ma20 = market_data['ma20']
    rsi = market_data['rsi']
    signals = market_data['signals']
    
    # 趋势判断逻辑
    trend_score = 0
    
    # MA趋势
    if ma5 > ma20:
        trend_score += 1
        trend_factors = ["MA5上穿MA20，短期趋势向好"]
    else:
        trend_score -= 1
        trend_factors = ["MA5下穿MA20，短期趋势转弱"]
    
    # RSI判断
    if 30 < rsi < 70:
        trend_score += 0.5
        trend_factors.append("RSI在正常区间，无极端情况")
    elif rsi < 30:
        trend_score += 1
        trend_factors.append("RSI超卖，反弹概率较高")
    else:
        trend_score -= 1
        trend_factors.append("RSI超买，回调风险较高")
    
    # 价格位置判断
    if price > ma20:
        trend_score += 0.5
        trend_factors.append("价格位于MA20上方，多头格局")
    else:
        trend_score -= 0.5
        trend_factors.append("价格位于MA20下方，空头格局")
    
    # 综合判断
    if trend_score >= 1.5:
        trend_direction = "上涨"
        confidence = "高" if trend_score >= 2 else "中"
        trading_suggestion = "买入"
        target_price = price * 1.05  # 5%涨幅目标
        support_level = ma20
        resistance_level = price * 1.03
    elif trend_score <= -1.5:
        trend_direction = "下跌"
        confidence = "高" if trend_score <= -2 else "中"
        trading_suggestion = "卖出"
        target_price = price * 0.95  # 5%跌幅目标
        support_level = price * 0.97
        resistance_level = ma20
    else:
        trend_direction = "震荡"
        confidence = "中"
        trading_suggestion = "观望"
        target_price = price
        support_level = min(price * 0.98, ma20 * 0.99)
        resistance_level = max(price * 1.02, ma20 * 1.01)
    
    # 风险评估
    volatility = (max(market_data.get('recent_prices', [price])) - min(market_data.get('recent_prices', [price]))) / price
    if volatility > 0.1:
        risk_level = "高"
    elif volatility > 0.05:
        risk_level = "中"
    else:
        risk_level = "低"
    
    # 构建预测结果
    prediction = {
        "symbol": "BTC",
        "trend_direction": trend_direction,
        "confidence": confidence,
        "target_price": target_price,
        "support_level": support_level,
        "resistance_level": resistance_level,
        "buy_zone_low": support_level * 0.998,
        "buy_zone_high": support_level * 1.002,
        "sell_zone_low": resistance_level * 0.998,
        "sell_zone_high": resistance_level * 1.002,
        "stop_loss": support_level * 0.97,
        "risk_level": risk_level,
        "trading_suggestion": trading_suggestion,
        "analysis_summary": f"基于技术指标分析，{trend_direction}趋势概率较高。主要支撑位在${support_level:.0f}，阻力位在${resistance_level:.0f}。",
        "key_factors": trend_factors[:3],
        "signal_strength": min(10, max(1, int(abs(trend_score) * 3))),
        "prediction_date": datetime.now().isoformat(),
        "prediction_days": 7
    }
    
    print("🔮 AI分析结果:")
    print(f"📈 趋势方向: {prediction['trend_direction']}")
    print(f"🎯 信心度: {prediction['confidence']}")
    print(f"⚡ 信号强度: {prediction['signal_strength']}/10")
    print(f"💰 目标价格: ${prediction['target_price']:.0f}")
    print(f"🛡️  支撑位: ${prediction['support_level']:.0f}")
    print(f"🚧 阻力位: ${prediction['resistance_level']:.0f}")
    print(f"📊 交易建议: {prediction['trading_suggestion']}")
    print(f"⚠️  风险等级: {prediction['risk_level']}")
    
    print(f"\n🔍 关键因素:")
    for i, factor in enumerate(prediction['key_factors'], 1):
        print(f"  {i}. {factor}")
    
    # 保存预测结果
    with open('/workspace/demo_prediction_simple.json', 'w', encoding='utf-8') as f:
        json.dump(prediction, f, ensure_ascii=False, indent=2)
    print(f"\n📄 预测结果已保存到: demo_prediction_simple.json")
    
    return prediction

def demo_fibonacci_logic():
    """演示斐波那契分析逻辑"""
    print("\n" + "=" * 60)
    print("📐 斐波那契分析逻辑演示")
    print("=" * 60)
    
    # 模拟最近的高低点
    recent_high = 48000
    recent_low = 44000
    current_price = 46500
    
    print(f"📊 分析区间:")
    print(f"最高点: ${recent_high:.0f}")
    print(f"最低点: ${recent_low:.0f}")
    print(f"当前价格: ${current_price:.0f}")
    
    # 计算斐波那契回调位
    diff = recent_high - recent_low
    fib_levels = {
        '0%': recent_high,
        '23.6%': recent_high - diff * 0.236,
        '38.2%': recent_high - diff * 0.382,
        '50%': recent_high - diff * 0.5,
        '61.8%': recent_high - diff * 0.618,
        '78.6%': recent_high - diff * 0.786,
        '100%': recent_low
    }
    
    print(f"\n📐 斐波那契回调位:")
    for level, price in fib_levels.items():
        distance = abs(current_price - price) / current_price * 100
        status = "🎯 当前位置" if distance < 1 else "📍 关键位" if distance < 3 else ""
        print(f"  {level:>6}: ${price:>7.0f} {status}")
    
    # 找到最接近的斐波那契位
    closest_level = min(fib_levels.items(), key=lambda x: abs(x[1] - current_price))
    print(f"\n🎯 最接近的斐波那契位: {closest_level[0]} (${closest_level[1]:.0f})")
    
    # 分析当前位置
    if current_price > fib_levels['38.2%']:
        position_analysis = "价格在38.2%回调位上方，回调幅度较小，趋势仍然较强"
    elif current_price > fib_levels['50%']:
        position_analysis = "价格在50%回调位上方，属于健康回调"
    elif current_price > fib_levels['61.8%']:
        position_analysis = "价格在61.8%黄金回调位上方，关键支撑位"
    else:
        position_analysis = "价格跌破61.8%回调位，趋势可能转弱"
    
    print(f"\n📋 位置分析: {position_analysis}")
    
    return fib_levels

def demo_trading_signals():
    """演示交易信号生成逻辑"""
    print("\n" + "=" * 60)
    print("🚨 交易信号生成逻辑演示")
    print("=" * 60)
    
    # 模拟技术指标状态
    indicators = {
        'RSI': 45,  # 正常区间
        'MA5': 46800,
        'MA20': 46500,
        'KDJ_K': 55,
        'KDJ_D': 50,
        'MACD': 0.002,
        'MACD_Signal': -0.001,
        'BB_position': 0.6,  # 布林带位置 (0-1)
        'Volume_ratio': 1.2   # 成交量比率
    }
    
    print("📊 当前技术指标状态:")
    for indicator, value in indicators.items():
        print(f"  {indicator}: {value}")
    
    # 信号评分系统
    signals = {}
    total_score = 0
    
    # MA信号
    if indicators['MA5'] > indicators['MA20']:
        signals['MA'] = {'signal': '买入', 'score': 1, 'reason': 'MA5上穿MA20，短期趋势向好'}
        total_score += 1
    else:
        signals['MA'] = {'signal': '卖出', 'score': -1, 'reason': 'MA5下穿MA20，短期趋势转弱'}
        total_score -= 1
    
    # RSI信号
    if indicators['RSI'] < 30:
        signals['RSI'] = {'signal': '买入', 'score': 2, 'reason': 'RSI超卖，反弹概率高'}
        total_score += 2
    elif indicators['RSI'] > 70:
        signals['RSI'] = {'signal': '卖出', 'score': -2, 'reason': 'RSI超买，回调风险高'}
        total_score -= 2
    else:
        signals['RSI'] = {'signal': '中性', 'score': 0, 'reason': 'RSI在正常区间'}
    
    # KDJ信号
    if indicators['KDJ_K'] > indicators['KDJ_D'] and indicators['KDJ_K'] < 80:
        signals['KDJ'] = {'signal': '买入', 'score': 1, 'reason': 'KDJ金叉且未超买'}
        total_score += 1
    elif indicators['KDJ_K'] < indicators['KDJ_D'] and indicators['KDJ_K'] > 20:
        signals['KDJ'] = {'signal': '卖出', 'score': -1, 'reason': 'KDJ死叉且未超卖'}
        total_score -= 1
    else:
        signals['KDJ'] = {'signal': '中性', 'score': 0, 'reason': 'KDJ无明确信号'}
    
    # MACD信号
    if indicators['MACD'] > indicators['MACD_Signal']:
        signals['MACD'] = {'signal': '买入', 'score': 1, 'reason': 'MACD上穿信号线'}
        total_score += 1
    else:
        signals['MACD'] = {'signal': '卖出', 'score': -1, 'reason': 'MACD下穿信号线'}
        total_score -= 1
    
    # 布林带信号
    if indicators['BB_position'] < 0.2:
        signals['布林带'] = {'signal': '买入', 'score': 1, 'reason': '价格触及布林带下轨'}
        total_score += 1
    elif indicators['BB_position'] > 0.8:
        signals['布林带'] = {'signal': '卖出', 'score': -1, 'reason': '价格触及布林带上轨'}
        total_score -= 1
    else:
        signals['布林带'] = {'signal': '中性', 'score': 0, 'reason': '价格在布林带中间区域'}
    
    # 成交量信号
    if indicators['Volume_ratio'] > 1.5:
        signals['成交量'] = {'signal': '确认', 'score': 1, 'reason': '放量确认趋势'}
        total_score += 1
    elif indicators['Volume_ratio'] < 0.5:
        signals['成交量'] = {'signal': '警告', 'score': -1, 'reason': '缩量需要谨慎'}
        total_score -= 1
    else:
        signals['成交量'] = {'signal': '正常', 'score': 0, 'reason': '成交量正常'}
    
    print(f"\n🚨 各指标信号:")
    for indicator, signal_data in signals.items():
        emoji = "✅" if signal_data['score'] > 0 else "❌" if signal_data['score'] < 0 else "⏸️"
        print(f"  {emoji} {indicator}: {signal_data['signal']} ({signal_data['score']:+d}) - {signal_data['reason']}")
    
    # 综合评分
    print(f"\n⚖️  综合评分: {total_score}")
    
    if total_score >= 3:
        overall_signal = "强烈买入"
        confidence = "高"
    elif total_score >= 1:
        overall_signal = "买入"
        confidence = "中"
    elif total_score <= -3:
        overall_signal = "强烈卖出"
        confidence = "高"
    elif total_score <= -1:
        overall_signal = "卖出"
        confidence = "中"
    else:
        overall_signal = "观望"
        confidence = "低"
    
    print(f"🎯 综合建议: {overall_signal} (信心度: {confidence})")
    
    return {
        'overall_signal': overall_signal,
        'confidence': confidence,
        'total_score': total_score,
        'individual_signals': signals
    }

def main():
    """主演示函数"""
    print("🚀 Coinglass数字货币分析系统 - 核心逻辑演示")
    print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 技术分析逻辑演示
    market_data = demo_technical_analysis_logic()
    
    # 2. 斐波那契分析演示
    fib_levels = demo_fibonacci_logic()
    
    # 3. AI分析逻辑演示
    trading_analysis = demo_trading_signals()
    
    # 4. 生成完整报告
    print("\n" + "=" * 60)
    print("📋 完整分析报告")
    print("=" * 60)
    
    report = {
        "分析时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "币种": "BTC (演示数据)",
        "当前价格": f"${market_data['price']:.0f}",
        "技术指标": {
            "MA5": f"${market_data['ma5']:.0f}",
            "MA20": f"${market_data['ma20']:.0f}",
            "RSI": f"{market_data['rsi']:.1f}",
            "布林带上轨": f"${market_data['bb_upper']:.0f}",
            "布林带下轨": f"${market_data['bb_lower']:.0f}"
        },
        "斐波那契关键位": {
            "38.2%回调": f"${fib_levels['38.2%']:.0f}",
            "50%回调": f"${fib_levels['50%']:.0f}",
            "61.8%回调": f"${fib_levels['61.8%']:.0f}"
        },
        "交易信号": {
            "综合建议": trading_analysis['overall_signal'],
            "信心度": trading_analysis['confidence'],
            "评分": trading_analysis['total_score']
        }
    }
    
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 保存完整报告
    with open('/workspace/demo_complete_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 完整报告已保存到: demo_complete_report.json")
    
    print("\n" + "=" * 60)
    print("🎊 演示完成")
    print("=" * 60)
    print("📁 生成的文件:")
    print("  • demo_prediction_simple.json - AI预测结果")
    print("  • demo_complete_report.json - 完整分析报告")
    
    print("\n🚀 要运行完整系统，请:")
    print("  1. 安装依赖: pip install -r requirements.txt")
    print("  2. 配置API密钥: 复制.env.example到.env并填入密钥")
    print("  3. 启动程序: python3 coinglass_analyzer.py")
    
    print("\n💡 提示:")
    print("  • 本演示使用模拟数据展示核心逻辑")
    print("  • 实际使用需要配置真实的API密钥")
    print("  • 投资有风险，决策需谨慎！")

if __name__ == "__main__":
    main()