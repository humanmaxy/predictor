#!/usr/bin/env python3
"""
数字货币分析工具演示脚本
展示核心功能的使用方法
"""

import os
import sys
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_data_fetching():
    """演示数据获取功能"""
    print("=" * 50)
    print("1. 数据获取功能演示")
    print("=" * 50)
    
    try:
        from data_fetcher import CryptoDataFetcher
        
        fetcher = CryptoDataFetcher()
        print(f"支持的数字货币: {fetcher.get_supported_coins()}")
        
        # 获取BTC数据
        print("\n获取BTC 7天价格数据...")
        btc_data = fetcher.get_price_data('BTC', days=7)
        print(f"获取到 {len(btc_data)} 条记录")
        print("\n最新5条记录:")
        print(btc_data[['price', 'volume']].tail())
        
        # 获取当前价格
        print("\n获取当前价格...")
        current_prices = fetcher.get_current_price(['BTC', 'ETH', 'SOL'])
        for symbol, data in current_prices.items():
            price = data.get('usd', 'N/A')
            change_24h = data.get('usd_24h_change', 'N/A')
            print(f"{symbol}: ${price} (24h变化: {change_24h}%)")
        
        return btc_data
        
    except Exception as e:
        print(f"数据获取演示失败: {e}")
        return None

def demo_technical_analysis(data):
    """演示技术分析功能"""
    print("\n" + "=" * 50)
    print("2. 技术分析功能演示")
    print("=" * 50)
    
    if data is None:
        print("跳过技术分析演示（数据获取失败）")
        return None
    
    try:
        from technical_indicators import IndicatorAnalyzer
        
        analyzer = IndicatorAnalyzer()
        
        # 计算技术指标
        print("计算技术指标...")
        analyzed_data = analyzer.analyze_price_data(data)
        
        print(f"技术指标计算完成，数据形状: {analyzed_data.shape}")
        print("\n技术指标列:")
        indicator_columns = [col for col in analyzed_data.columns if col not in ['price', 'volume', 'symbol']]
        for col in indicator_columns:
            print(f"  - {col}")
        
        # 显示最新的技术指标值
        latest = analyzed_data.iloc[-1]
        print(f"\n最新技术指标值 ({latest.name.strftime('%Y-%m-%d %H:%M')}):")
        print(f"  价格: ${latest['price']:.2f}")
        if 'MA5' in latest:
            print(f"  MA5: ${latest['MA5']:.2f}")
        if 'MA20' in latest:
            print(f"  MA20: ${latest['MA20']:.2f}")
        if 'RSI' in latest:
            print(f"  RSI: {latest['RSI']:.2f}")
        if 'BB_Upper' in latest:
            print(f"  布林带上轨: ${latest['BB_Upper']:.2f}")
        if 'BB_Lower' in latest:
            print(f"  布林带下轨: ${latest['BB_Lower']:.2f}")
        
        # 生成交易信号
        print("\n生成交易信号...")
        signals_data = analyzer.get_trading_signals(analyzed_data)
        
        # 显示最新信号
        latest_signals = signals_data.iloc[-1]
        print("最新交易信号:")
        signal_columns = [col for col in signals_data.columns if 'Signal' in col]
        for col in signal_columns:
            if col in latest_signals:
                value = latest_signals[col]
                signal_text = "买入" if value > 0 else "卖出" if value < 0 else "中性"
                print(f"  {col}: {signal_text} ({value})")
        
        return signals_data
        
    except Exception as e:
        print(f"技术分析演示失败: {e}")
        return None

def demo_chart_plotting(data):
    """演示图表绘制功能"""
    print("\n" + "=" * 50)
    print("3. 图表绘制功能演示")
    print("=" * 50)
    
    if data is None:
        print("跳过图表绘制演示（数据获取失败）")
        return
    
    try:
        from chart_plotter import ChartPlotter
        import matplotlib.pyplot as plt
        
        plotter = ChartPlotter()
        
        # 绘制价格和移动平均线图表
        print("绘制价格和移动平均线图表...")
        fig1 = plotter.plot_price_with_ma(data, 'BTC')
        plt.savefig('/workspace/demo_price_ma.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("已保存: demo_price_ma.png")
        
        # 绘制布林带图表
        if all(col in data.columns for col in ['BB_Upper', 'BB_Lower']):
            print("绘制布林带图表...")
            fig2 = plotter.plot_bollinger_bands(data, 'BTC')
            plt.savefig('/workspace/demo_bollinger.png', dpi=150, bbox_inches='tight')
            plt.close()
            print("已保存: demo_bollinger.png")
        
        # 绘制RSI图表
        if 'RSI' in data.columns:
            print("绘制RSI图表...")
            fig3 = plotter.plot_rsi(data, 'BTC')
            plt.savefig('/workspace/demo_rsi.png', dpi=150, bbox_inches='tight')
            plt.close()
            print("已保存: demo_rsi.png")
        
        # 绘制综合分析图表
        print("绘制综合分析图表...")
        fig4 = plotter.plot_comprehensive_chart(data, 'BTC')
        plt.savefig('/workspace/demo_comprehensive.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("已保存: demo_comprehensive.png")
        
        print("图表绘制演示完成！")
        
    except Exception as e:
        print(f"图表绘制演示失败: {e}")

def demo_ai_prediction(data):
    """演示AI预测功能"""
    print("\n" + "=" * 50)
    print("4. AI预测功能演示")
    print("=" * 50)
    
    if data is None:
        print("跳过AI预测演示（数据获取失败）")
        return
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("未找到DEEPSEEK_API_KEY环境变量")
        print("请在.env文件中设置API密钥或跳过AI预测演示")
        return
    
    try:
        from ai_predictor import AIPredictor
        
        predictor = AIPredictor(api_key=api_key)
        
        print("正在进行AI趋势预测...")
        print("（这可能需要几秒钟时间）")
        
        prediction = predictor.predict_trend(data, 'BTC', prediction_days=7)
        
        print("\nAI预测结果:")
        print(f"  趋势方向: {prediction.get('trend_direction', 'N/A')}")
        print(f"  信心度: {prediction.get('confidence', 'N/A')}")
        print(f"  风险等级: {prediction.get('risk_level', 'N/A')}")
        print(f"  交易建议: {prediction.get('trading_suggestion', 'N/A')}")
        print(f"  目标价格: ${prediction.get('target_price', 0):.2f}")
        print(f"  支撑位: ${prediction.get('support_level', 0):.2f}")
        print(f"  阻力位: ${prediction.get('resistance_level', 0):.2f}")
        
        print(f"\n分析摘要:")
        summary = prediction.get('analysis_summary', '')
        if len(summary) > 200:
            print(summary[:200] + "...")
        else:
            print(summary)
        
        # 保存预测结果
        import json
        with open('/workspace/demo_prediction.json', 'w', encoding='utf-8') as f:
            json.dump(prediction, f, ensure_ascii=False, indent=2)
        print("\n预测结果已保存到: demo_prediction.json")
        
    except Exception as e:
        print(f"AI预测演示失败: {e}")
        if "api" in str(e).lower():
            print("可能是API密钥问题，请检查DEEPSEEK_API_KEY设置")

def main():
    """主演示函数"""
    print("数字货币技术分析与AI预测工具 - 功能演示")
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 数据获取演示
    data = demo_data_fetching()
    
    # 2. 技术分析演示
    analyzed_data = demo_technical_analysis(data)
    
    # 3. 图表绘制演示
    demo_chart_plotting(analyzed_data if analyzed_data is not None else data)
    
    # 4. AI预测演示
    demo_ai_prediction(analyzed_data if analyzed_data is not None else data)
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)
    print("生成的文件:")
    print("  - demo_price_ma.png (价格和移动平均线图表)")
    print("  - demo_bollinger.png (布林带图表)")
    print("  - demo_rsi.png (RSI指标图表)")
    print("  - demo_comprehensive.png (综合分析图表)")
    print("  - demo_prediction.json (AI预测结果)")
    print("\n要启动完整的GUI程序，请运行:")
    print("  python3 main_gui.py")
    print("\n注意: GUI程序需要配置DeepSeek API密钥才能使用AI预测功能")

if __name__ == "__main__":
    main()
