#!/usr/bin/env python3
"""
Coinglass API功能测试脚本
验证数据获取、技术指标计算和AI预测功能
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_coinglass_api():
    """测试Coinglass API数据获取"""
    print("=" * 60)
    print("🔍 测试Coinglass API数据获取")
    print("=" * 60)
    
    try:
        from data_fetcher import CoinglassDataFetcher
        
        # 检查API密钥
        api_key = os.getenv('COINGLASS_API_KEY')
        if not api_key:
            print("⚠️  未找到COINGLASS_API_KEY环境变量")
            print("请在.env文件中配置API密钥，或者测试将使用备用数据源")
            return None
        
        fetcher = CoinglassDataFetcher(api_key)
        print(f"✅ 支持的币种: {fetcher.get_supported_symbols()}")
        
        # 测试获取BTC小时数据
        print("\n📊 获取BTC 1小时K线数据...")
        btc_hourly = fetcher.get_kline_data('BTC', '1h', 100)
        print(f"✅ 获取到 {len(btc_hourly)} 条小时数据")
        print("最新5条记录:")
        print(btc_hourly[['open', 'high', 'low', 'close', 'volume']].tail())
        
        # 测试获取BTC日数据
        print("\n📊 获取BTC 1日K线数据...")
        btc_daily = fetcher.get_kline_data('BTC', '1d', 30)
        print(f"✅ 获取到 {len(btc_daily)} 条日数据")
        
        # 测试ticker数据
        print("\n💰 获取BTC当前价格信息...")
        ticker_data = fetcher.get_ticker_data('BTC')
        print(f"当前价格: ${ticker_data['price']:.2f}")
        print(f"24小时涨跌: {ticker_data['change_24h']:.2f}%")
        print(f"24小时成交量: {ticker_data['volume_24h']:,.0f}")
        
        return {'hourly': btc_hourly, 'daily': btc_daily}
        
    except Exception as e:
        print(f"❌ Coinglass API测试失败: {e}")
        return None

def test_technical_indicators(data_dict):
    """测试技术指标计算"""
    print("\n" + "=" * 60)
    print("📈 测试技术指标计算")
    print("=" * 60)
    
    if not data_dict:
        print("⚠️  跳过技术指标测试（数据获取失败）")
        return None
    
    try:
        from technical_indicators import IndicatorAnalyzer
        
        analyzer = IndicatorAnalyzer()
        results = {}
        
        for timeframe, data in data_dict.items():
            print(f"\n📊 分析{timeframe}数据...")
            
            # 计算技术指标
            analyzed_data = analyzer.analyze_price_data(data)
            print(f"✅ 技术指标计算完成，数据形状: {analyzed_data.shape}")
            
            # 生成交易信号
            signals_data = analyzer.get_trading_signals(analyzed_data)
            print(f"✅ 交易信号生成完成")
            
            # 显示最新指标值
            latest = signals_data.iloc[-1]
            print(f"\n最新技术指标 ({latest.name.strftime('%Y-%m-%d %H:%M')}):")
            print(f"  💰 价格: ${latest['price']:.4f}")
            print(f"  📊 RSI: {latest.get('RSI', 0):.2f}")
            print(f"  📈 KDJ: K={latest.get('KDJ_K', 0):.1f}, D={latest.get('KDJ_D', 0):.1f}, J={latest.get('KDJ_J', 0):.1f}")
            print(f"  📉 MACD: {latest.get('MACD', 0):.6f}")
            print(f"  🎯 布林带位置: {((latest['price'] - latest.get('BB_Lower', 0)) / (latest.get('BB_Upper', 0) - latest.get('BB_Lower', 0)) * 100):.1f}%" if latest.get('BB_Upper') and latest.get('BB_Lower') else 'N/A')
            
            # 交易信号分析
            signals = []
            signal_cols = ['MA_Signal', 'RSI_Signal', 'KDJ_Signal', 'MACD_Signal_Trade', 'BB_Signal']
            for col in signal_cols:
                if col in latest and latest[col] != 0:
                    signal_type = "买入" if latest[col] > 0 else "卖出"
                    signals.append(f"{col.replace('_Signal', '').replace('_Trade', '')}: {signal_type}")
            
            if signals:
                print(f"  🚨 当前信号: {', '.join(signals)}")
                combined = latest.get('Combined_Signal', 0)
                print(f"  ⚖️  综合评分: {combined} ({'强烈' if abs(combined) >= 3 else '一般' if abs(combined) >= 2 else '弱'}{'买入' if combined > 0 else '卖出' if combined < 0 else '观望'})")
            else:
                print(f"  ⏸️  当前信号: 观望")
            
            results[timeframe] = signals_data
        
        return results
        
    except Exception as e:
        print(f"❌ 技术指标测试失败: {e}")
        return None

def test_chart_plotting(analyzed_data):
    """测试图表绘制功能"""
    print("\n" + "=" * 60)
    print("📊 测试图表绘制功能")
    print("=" * 60)
    
    if not analyzed_data:
        print("⚠️  跳过图表绘制测试（数据分析失败）")
        return
    
    try:
        from chart_plotter import ChartPlotter
        
        plotter = ChartPlotter()
        
        for timeframe, data in analyzed_data.items():
            print(f"\n🎨 绘制{timeframe}图表...")
            
            # 综合分析图表
            fig = plotter.plot_enhanced_comprehensive_chart(data, 'BTC', timeframe)
            filename = f'/workspace/test_comprehensive_{timeframe}.png'
            fig.savefig(filename, dpi=200, bbox_inches='tight')
            plt.close()
            print(f"✅ 综合分析图表已保存: {filename}")
            
            # KDJ专项图表
            if all(col in data.columns for col in ['KDJ_K', 'KDJ_D', 'KDJ_J']):
                fig_kdj = plotter.plot_kdj(data, f'BTC({timeframe})')
                filename_kdj = f'/workspace/test_kdj_{timeframe}.png'
                fig_kdj.savefig(filename_kdj, dpi=200, bbox_inches='tight')
                plt.close()
                print(f"✅ KDJ指标图表已保存: {filename_kdj}")
            
            # 斐波那契图表
            if 'Fib_38.2' in data.columns:
                fig_fib = plotter.plot_fibonacci_levels(data, f'BTC({timeframe})')
                filename_fib = f'/workspace/test_fibonacci_{timeframe}.png'
                fig_fib.savefig(filename_fib, dpi=200, bbox_inches='tight')
                plt.close()
                print(f"✅ 斐波那契图表已保存: {filename_fib}")
        
        print("🎉 图表绘制测试完成！")
        
    except Exception as e:
        print(f"❌ 图表绘制测试失败: {e}")

def test_ai_prediction(analyzed_data):
    """测试AI预测功能"""
    print("\n" + "=" * 60)
    print("🤖 测试AI预测功能")
    print("=" * 60)
    
    if not analyzed_data:
        print("⚠️  跳过AI预测测试（数据分析失败）")
        return
    
    # 检查DeepSeek API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("⚠️  未找到DEEPSEEK_API_KEY环境变量，跳过AI预测测试")
        print("请在.env文件中配置DeepSeek API密钥以启用AI预测功能")
        return
    
    try:
        from ai_predictor import AIPredictor
        
        predictor = AIPredictor(api_key=api_key)
        
        # 测试小时级预测
        if 'hourly' in analyzed_data:
            print("\n🔮 进行小时级AI预测...")
            hourly_prediction = predictor.predict_trend(analyzed_data['hourly'], 'BTC', 3)
            
            print("✅ 小时级预测完成:")
            print(f"  📈 趋势方向: {hourly_prediction.get('trend_direction', 'N/A')}")
            print(f"  🎯 信心度: {hourly_prediction.get('confidence', 'N/A')}")
            print(f"  ⚡ 信号强度: {hourly_prediction.get('signal_strength', 'N/A')}/10")
            print(f"  💰 目标价格: ${hourly_prediction.get('target_price', 0):.2f}")
            print(f"  🛡️  支撑位: ${hourly_prediction.get('support_level', 0):.2f}")
            print(f"  🚧 阻力位: ${hourly_prediction.get('resistance_level', 0):.2f}")
            print(f"  📊 交易建议: {hourly_prediction.get('trading_suggestion', 'N/A')}")
            
            # 保存预测结果
            import json
            with open('/workspace/test_hourly_prediction.json', 'w', encoding='utf-8') as f:
                json.dump(hourly_prediction, f, ensure_ascii=False, indent=2)
            print("📄 小时级预测结果已保存到: test_hourly_prediction.json")
        
        # 测试日级预测
        if 'daily' in analyzed_data:
            print("\n🔮 进行日级AI预测...")
            daily_prediction = predictor.predict_trend(analyzed_data['daily'], 'BTC', 7)
            
            print("✅ 日级预测完成:")
            print(f"  📈 趋势方向: {daily_prediction.get('trend_direction', 'N/A')}")
            print(f"  🎯 信心度: {daily_prediction.get('confidence', 'N/A')}")
            print(f"  ⚡ 信号强度: {daily_prediction.get('signal_strength', 'N/A')}/10")
            print(f"  💰 目标价格: ${daily_prediction.get('target_price', 0):.2f}")
            print(f"  📊 交易建议: {daily_prediction.get('trading_suggestion', 'N/A')}")
            
            # 保存预测结果
            with open('/workspace/test_daily_prediction.json', 'w', encoding='utf-8') as f:
                json.dump(daily_prediction, f, ensure_ascii=False, indent=2)
            print("📄 日级预测结果已保存到: test_daily_prediction.json")
        
        print("🎉 AI预测测试完成！")
        
    except Exception as e:
        print(f"❌ AI预测测试失败: {e}")
        if "api" in str(e).lower():
            print("💡 可能是API密钥问题，请检查DEEPSEEK_API_KEY配置")

def test_backup_data_source():
    """测试备用数据源"""
    print("\n" + "=" * 60)
    print("🔄 测试备用数据源 (CoinGecko)")
    print("=" * 60)
    
    try:
        from data_fetcher import CryptoDataFetcher
        
        fetcher = CryptoDataFetcher()
        
        print("📊 获取BTC数据...")
        btc_data = fetcher.get_price_data('BTC', days=7)
        print(f"✅ 获取到 {len(btc_data)} 条记录")
        
        print("💰 获取当前价格...")
        current_prices = fetcher.get_current_price(['BTC', 'ETH'])
        for symbol, data in current_prices.items():
            price = data.get('usd', 'N/A')
            change = data.get('usd_24h_change', 'N/A')
            print(f"  {symbol}: ${price} (24h: {change}%)")
        
        return btc_data
        
    except Exception as e:
        print(f"❌ 备用数据源测试失败: {e}")
        return None

def main():
    """主测试函数"""
    print("🚀 Coinglass数字货币分析系统 - 功能测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试Coinglass API
    coinglass_data = test_coinglass_api()
    
    # 2. 测试备用数据源
    backup_data = test_backup_data_source()
    
    # 选择可用的数据进行后续测试
    test_data = coinglass_data if coinglass_data else {'hourly': backup_data} if backup_data else None
    
    # 3. 测试技术指标计算
    analyzed_data = test_technical_indicators(test_data)
    
    # 4. 测试图表绘制
    test_chart_plotting(analyzed_data)
    
    # 5. 测试AI预测
    test_ai_prediction(analyzed_data)
    
    # 总结
    print("\n" + "=" * 60)
    print("🎊 测试完成总结")
    print("=" * 60)
    print("生成的测试文件:")
    
    test_files = [
        "test_comprehensive_hourly.png",
        "test_comprehensive_daily.png", 
        "test_kdj_hourly.png",
        "test_kdj_daily.png",
        "test_fibonacci_hourly.png",
        "test_fibonacci_daily.png",
        "test_hourly_prediction.json",
        "test_daily_prediction.json"
    ]
    
    for file in test_files:
        full_path = f"/workspace/{file}"
        if os.path.exists(full_path):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (未生成)")
    
    print("\n🚀 启动完整程序:")
    print("  python coinglass_analyzer.py")
    
    print("\n💡 配置说明:")
    print("  1. 复制 .env.example 到 .env")
    print("  2. 在 .env 中配置您的API密钥")
    print("  3. 运行程序并在GUI中输入API密钥")
    
    print("\n⚠️  风险提示:")
    print("  本工具仅供学习研究使用，投资有风险，决策需谨慎！")

if __name__ == "__main__":
    main()