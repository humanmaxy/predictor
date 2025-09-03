#!/usr/bin/env python3
"""
基于Coinglass API的数字货币技术分析与预测系统
支持小时级和日级别的技术指标分析、趋势预测和交易信号生成
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import threading
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

# 导入自定义模块
from data_fetcher import CoinglassDataFetcher, CryptoDataFetcher
from technical_indicators import IndicatorAnalyzer, TechnicalIndicators
from chart_plotter import ChartPlotter
from ai_predictor import AIPredictor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class CoinglassAnalyzerGUI:
    """基于Coinglass API的数字货币分析工具"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Coinglass数字货币技术分析与AI预测系统")
        self.root.geometry("1600x1000")
        
        # 初始化数据获取器
        self.coinglass_fetcher = None
        self.backup_fetcher = CryptoDataFetcher()  # 备用数据源
        self.indicator_analyzer = IndicatorAnalyzer()
        self.chart_plotter = ChartPlotter()
        self.ai_predictor = None
        
        # 数据存储
        self.hourly_data = {}  # 小时级数据
        self.daily_data = {}   # 日级数据
        self.predictions = {}  # 预测结果
        
        # 状态变量
        self.is_loading = False
        self.current_symbol = "BTC"
        self.current_timeframe = "1h"
        
        # 创建界面
        self.create_widgets()
        self.setup_layout()
        
        logger.info("Coinglass分析器GUI初始化完成")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.main_frame = ttk.Frame(self.root)
        
        # 顶部工具栏
        self.toolbar = ttk.Frame(self.main_frame)
        
        # API配置区域
        api_frame = ttk.LabelFrame(self.toolbar, text="API配置", padding="5")
        
        # Coinglass API Key
        ttk.Label(api_frame, text="Coinglass API:").grid(row=0, column=0, sticky="w", padx=2)
        self.coinglass_key_var = tk.StringVar()
        self.coinglass_entry = ttk.Entry(api_frame, textvariable=self.coinglass_key_var, 
                                       show="*", width=25)
        self.coinglass_entry.grid(row=0, column=1, padx=2)
        
        # DeepSeek API Key
        ttk.Label(api_frame, text="DeepSeek API:").grid(row=1, column=0, sticky="w", padx=2)
        self.deepseek_key_var = tk.StringVar()
        self.deepseek_entry = ttk.Entry(api_frame, textvariable=self.deepseek_key_var, 
                                      show="*", width=25)
        self.deepseek_entry.grid(row=1, column=1, padx=2)
        
        ttk.Button(api_frame, text="保存配置", command=self.save_config).grid(row=0, column=2, rowspan=2, padx=5)
        
        # 交易参数区域
        trading_frame = ttk.LabelFrame(self.toolbar, text="交易参数", padding="5")
        
        ttk.Label(trading_frame, text="币种:").grid(row=0, column=0, sticky="w")
        self.symbol_var = tk.StringVar(value="BTC")
        symbols = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LINK", "LTC", "BCH", "UNI", "AVAX", "MATIC"]
        self.symbol_combo = ttk.Combobox(trading_frame, textvariable=self.symbol_var, 
                                       values=symbols, state="readonly", width=8)
        self.symbol_combo.grid(row=0, column=1, padx=2)
        
        ttk.Label(trading_frame, text="时间框架:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.timeframe_var = tk.StringVar(value="1h")
        timeframes = ["1h", "4h", "1d", "1w"]
        self.timeframe_combo = ttk.Combobox(trading_frame, textvariable=self.timeframe_var,
                                          values=timeframes, state="readonly", width=8)
        self.timeframe_combo.grid(row=0, column=3, padx=2)
        
        ttk.Label(trading_frame, text="数据量:").grid(row=0, column=4, sticky="w", padx=(10,0))
        self.limit_var = tk.StringVar(value="200")
        limits = ["100", "200", "500", "1000"]
        self.limit_combo = ttk.Combobox(trading_frame, textvariable=self.limit_var,
                                      values=limits, state="readonly", width=8)
        self.limit_combo.grid(row=0, column=5, padx=2)
        
        # 操作按钮区域
        action_frame = ttk.LabelFrame(self.toolbar, text="操作", padding="5")
        
        self.fetch_btn = ttk.Button(action_frame, text="获取数据", command=self.fetch_data)
        self.fetch_btn.grid(row=0, column=0, padx=2)
        
        self.analyze_btn = ttk.Button(action_frame, text="技术分析", 
                                    command=self.analyze_data, state="disabled")
        self.analyze_btn.grid(row=0, column=1, padx=2)
        
        self.predict_btn = ttk.Button(action_frame, text="AI预测", 
                                    command=self.predict_trend, state="disabled")
        self.predict_btn.grid(row=0, column=2, padx=2)
        
        self.compare_btn = ttk.Button(action_frame, text="多币种对比", 
                                    command=self.compare_multiple, state="disabled")
        self.compare_btn.grid(row=0, column=3, padx=2)
        
        # 主显示区域
        self.content_frame = ttk.Frame(self.main_frame)
        
        # 创建Notebook用于标签页
        self.notebook = ttk.Notebook(self.content_frame)
        
        # 小时级分析标签页
        self.hourly_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.hourly_frame, text="小时级分析")
        
        # 日级分析标签页
        self.daily_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.daily_frame, text="日级分析")
        
        # AI预测标签页
        self.prediction_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.prediction_frame, text="AI趋势预测")
        
        # 多币种对比标签页
        self.comparison_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.comparison_frame, text="多币种对比")
        
        # 初始化各标签页
        self.init_analysis_pages()
        self.init_prediction_page()
        self.init_comparison_page()
        
        # 状态栏
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_var = tk.StringVar(value="就绪 - 请配置API密钥并获取数据")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        
        # 加载已保存的配置
        self.load_config()
    
    def init_analysis_pages(self):
        """初始化分析页面"""
        # 小时级分析页面
        self.init_timeframe_page(self.hourly_frame, "小时级")
        
        # 日级分析页面  
        self.init_timeframe_page(self.daily_frame, "日级")
    
    def init_timeframe_page(self, parent_frame, timeframe_name):
        """初始化时间框架分析页面"""
        # 图表控制区域
        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(control_frame, text="图表类型:").pack(side="left")
        chart_type_var = tk.StringVar(value="综合分析")
        chart_types = ["价格+MA", "布林带", "RSI", "MACD", "KDJ", "成交量", "综合分析"]
        chart_combo = ttk.Combobox(control_frame, textvariable=chart_type_var,
                                 values=chart_types, state="readonly")
        chart_combo.pack(side="left", padx=5)
        
        # 保存图表类型变量的引用
        setattr(self, f"{timeframe_name.lower()}_chart_type_var", chart_type_var)
        
        update_btn = ttk.Button(control_frame, text="更新图表", 
                              command=lambda: self.update_chart(timeframe_name))
        update_btn.pack(side="left", padx=5)
        
        save_btn = ttk.Button(control_frame, text="保存图表", 
                            command=lambda: self.save_chart(timeframe_name))
        save_btn.pack(side="left", padx=5)
        
        # 创建分割窗口
        paned = ttk.PanedWindow(parent_frame, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 左侧图表区域
        chart_frame = ttk.Frame(paned)
        paned.add(chart_frame, weight=3)
        
        # 保存图表框架的引用
        setattr(self, f"{timeframe_name.lower()}_chart_frame", chart_frame)
        
        # 右侧信息区域
        info_frame = ttk.Frame(paned)
        paned.add(info_frame, weight=1)
        
        # 技术指标信息
        indicators_label = ttk.LabelFrame(info_frame, text="技术指标", padding="5")
        indicators_label.pack(fill="both", expand=True, pady=(0, 5))
        
        indicators_text = scrolledtext.ScrolledText(indicators_label, height=15, width=30)
        indicators_text.pack(fill="both", expand=True)
        
        # 保存文本框的引用
        setattr(self, f"{timeframe_name.lower()}_indicators_text", indicators_text)
        
        # 交易信号信息
        signals_label = ttk.LabelFrame(info_frame, text="交易信号", padding="5")
        signals_label.pack(fill="both", expand=True)
        
        signals_text = scrolledtext.ScrolledText(signals_label, height=10, width=30)
        signals_text.pack(fill="both", expand=True)
        
        # 保存信号文本框的引用
        setattr(self, f"{timeframe_name.lower()}_signals_text", signals_text)
    
    def init_prediction_page(self):
        """初始化预测页面"""
        # 预测控制区域
        pred_control = ttk.Frame(self.prediction_frame)
        pred_control.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(pred_control, text="预测类型:").pack(side="left")
        self.pred_type_var = tk.StringVar(value="短期")
        pred_types = ["短期(1-3天)", "中期(7天)", "长期(30天)"]
        pred_type_combo = ttk.Combobox(pred_control, textvariable=self.pred_type_var,
                                     values=pred_types, state="readonly")
        pred_type_combo.pack(side="left", padx=5)
        
        ttk.Button(pred_control, text="生成预测", command=self.generate_prediction).pack(side="left", padx=5)
        ttk.Button(pred_control, text="导出报告", command=self.export_report).pack(side="left", padx=5)
        
        # 预测结果显示
        self.prediction_text = scrolledtext.ScrolledText(self.prediction_frame, height=30)
        self.prediction_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def init_comparison_page(self):
        """初始化对比页面"""
        # 对比控制区域
        comp_control = ttk.Frame(self.comparison_frame)
        comp_control.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(comp_control, text="选择币种:").pack(side="left")
        
        # 多选币种
        self.selected_coins = []
        coin_frame = ttk.Frame(comp_control)
        coin_frame.pack(side="left", padx=5)
        
        coins = ["BTC", "ETH", "SOL", "XRP", "ADA"]
        self.coin_vars = {}
        for i, coin in enumerate(coins):
            var = tk.BooleanVar()
            self.coin_vars[coin] = var
            ttk.Checkbutton(coin_frame, text=coin, variable=var).grid(row=0, column=i, padx=2)
        
        ttk.Button(comp_control, text="开始对比", command=self.start_comparison).pack(side="left", padx=10)
        
        # 对比结果显示
        self.comparison_text = scrolledtext.ScrolledText(self.comparison_frame, height=30)
        self.comparison_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def setup_layout(self):
        """设置布局"""
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部工具栏
        self.toolbar.pack(fill="x", pady=(0, 10))
        api_frame = [child for child in self.toolbar.winfo_children() if isinstance(child, ttk.LabelFrame) and "API" in str(child['text'])][0]
        trading_frame = [child for child in self.toolbar.winfo_children() if isinstance(child, ttk.LabelFrame) and "交易" in str(child['text'])][0]
        action_frame = [child for child in self.toolbar.winfo_children() if isinstance(child, ttk.LabelFrame) and "操作" in str(child['text'])][0]
        
        api_frame.pack(side="left", padx=(0, 10))
        trading_frame.pack(side="left", padx=(0, 10))
        action_frame.pack(side="left", padx=(0, 10))
        
        # 主内容区域
        self.content_frame.pack(fill="both", expand=True)
        self.notebook.pack(fill="both", expand=True)
        
        # 状态栏
        self.status_frame.pack(fill="x", pady=(10, 0))
        self.status_label.pack(side="left")
        self.progress.pack(side="right", padx=(10, 0))
        
        # 获取toolbar中的框架
        toolbar_children = list(self.toolbar.winfo_children())
        if len(toolbar_children) >= 3:
            toolbar_children[0].pack(side="left", padx=(0, 10))  # API框架
            toolbar_children[1].pack(side="left", padx=(0, 10))  # 交易框架  
            toolbar_children[2].pack(side="left", padx=(0, 10))  # 操作框架
    
    def save_config(self):
        """保存API配置"""
        coinglass_key = self.coinglass_key_var.get().strip()
        deepseek_key = self.deepseek_key_var.get().strip()
        
        try:
            env_content = ""
            if coinglass_key:
                env_content += f"COINGLASS_API_KEY={coinglass_key}\n"
            if deepseek_key:
                env_content += f"DEEPSEEK_API_KEY={deepseek_key}\n"
                env_content += "DEEPSEEK_BASE_URL=https://api.deepseek.com/v1\n"
            
            with open('/workspace/.env', 'w') as f:
                f.write(env_content)
            
            messagebox.showinfo("成功", "API配置已保存")
            
            # 重新初始化API客户端
            if coinglass_key:
                self.coinglass_fetcher = CoinglassDataFetcher(coinglass_key)
            if deepseek_key:
                self.ai_predictor = None  # 重置以便重新初始化
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """加载已保存的配置"""
        try:
            if os.path.exists('/workspace/.env'):
                with open('/workspace/.env', 'r') as f:
                    for line in f:
                        if line.startswith('COINGLASS_API_KEY='):
                            key = line.split('=', 1)[1].strip()
                            self.coinglass_key_var.set(key)
                            self.coinglass_fetcher = CoinglassDataFetcher(key)
                        elif line.startswith('DEEPSEEK_API_KEY='):
                            key = line.split('=', 1)[1].strip()
                            self.deepseek_key_var.set(key)
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")
    
    def fetch_data(self):
        """获取数据"""
        if self.is_loading:
            return
        
        symbol = self.symbol_var.get()
        timeframe = self.timeframe_var.get()
        limit = int(self.limit_var.get())
        
        def fetch_thread():
            try:
                self.is_loading = True
                self.root.after(0, lambda: self.set_status("正在获取数据...", True))
                self.root.after(0, lambda: self.set_buttons_state(False))
                
                # 优先使用Coinglass API
                if self.coinglass_fetcher:
                    try:
                        data = self.coinglass_fetcher.get_kline_data(symbol, timeframe, limit)
                        data_source = "Coinglass"
                    except Exception as e:
                        logger.warning(f"Coinglass API失败，使用备用数据源: {e}")
                        # 转换时间框架映射
                        days_map = {'1h': 7, '4h': 30, '1d': 180, '1w': 365}
                        days = days_map.get(timeframe, 30)
                        data = self.backup_fetcher.get_price_data(symbol, days)
                        data_source = "CoinGecko"
                else:
                    # 使用备用数据源
                    days_map = {'1h': 7, '4h': 30, '1d': 180, '1w': 365}
                    days = days_map.get(timeframe, 30)
                    data = self.backup_fetcher.get_price_data(symbol, days)
                    data_source = "CoinGecko"
                
                # 存储数据
                if timeframe in ['1h', '4h']:
                    self.hourly_data[symbol] = data
                else:
                    self.daily_data[symbol] = data
                
                self.current_symbol = symbol
                self.current_timeframe = timeframe
                
                self.root.after(0, lambda: self.set_status(f"成功获取{symbol}数据 (来源: {data_source})", False))
                self.root.after(0, lambda: self.set_buttons_state(True, analyze=True))
                
            except Exception as e:
                error_msg = f"获取数据失败: {str(e)}"
                logger.error(error_msg)
                self.root.after(0, lambda: self.set_status(error_msg, False))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.is_loading = False
        
        thread = threading.Thread(target=fetch_thread)
        thread.daemon = True
        thread.start()
    
    def analyze_data(self):
        """分析数据"""
        if self.is_loading:
            return
        
        symbol = self.current_symbol
        timeframe = self.current_timeframe
        
        # 选择数据源
        if timeframe in ['1h', '4h']:
            data_dict = self.hourly_data
        else:
            data_dict = self.daily_data
        
        if symbol not in data_dict:
            messagebox.showwarning("警告", "请先获取数据")
            return
        
        def analyze_thread():
            try:
                self.is_loading = True
                self.root.after(0, lambda: self.set_status("正在进行技术分析...", True))
                
                # 计算技术指标
                raw_data = data_dict[symbol]
                analyzed_data = self.indicator_analyzer.analyze_price_data(raw_data)
                signals_data = self.indicator_analyzer.get_trading_signals(analyzed_data)
                
                # 更新存储的数据
                data_dict[symbol] = signals_data
                
                # 更新界面显示
                self.root.after(0, lambda: self.update_indicators_display(signals_data, timeframe))
                self.root.after(0, lambda: self.update_signals_display(signals_data, timeframe))
                self.root.after(0, lambda: self.update_chart(timeframe))
                
                self.root.after(0, lambda: self.set_status("技术分析完成", False))
                self.root.after(0, lambda: self.set_buttons_state(True, predict=True))
                
            except Exception as e:
                error_msg = f"技术分析失败: {str(e)}"
                logger.error(error_msg)
                self.root.after(0, lambda: self.set_status(error_msg, False))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.is_loading = False
        
        thread = threading.Thread(target=analyze_thread)
        thread.daemon = True
        thread.start()
    
    def predict_trend(self):
        """AI趋势预测"""
        if self.is_loading:
            return
        
        if not self.init_ai_predictor():
            return
        
        symbol = self.current_symbol
        timeframe = self.current_timeframe
        
        # 选择数据源
        data_dict = self.hourly_data if timeframe in ['1h', '4h'] else self.daily_data
        
        if symbol not in data_dict:
            messagebox.showwarning("警告", "请先获取并分析数据")
            return
        
        def predict_thread():
            try:
                self.is_loading = True
                self.root.after(0, lambda: self.set_status("正在进行AI预测...", True))
                
                # 获取预测天数
                pred_type = self.pred_type_var.get()
                if "短期" in pred_type:
                    prediction_days = 3
                elif "中期" in pred_type:
                    prediction_days = 7
                else:
                    prediction_days = 30
                
                # 执行预测
                prediction = self.ai_predictor.predict_trend(
                    data_dict[symbol], symbol, prediction_days
                )
                
                # 存储预测结果
                self.predictions[f"{symbol}_{timeframe}"] = prediction
                
                # 更新显示
                self.root.after(0, lambda: self.update_prediction_display(prediction))
                self.root.after(0, lambda: self.set_status("AI预测完成", False))
                
            except Exception as e:
                error_msg = f"AI预测失败: {str(e)}"
                logger.error(error_msg)
                self.root.after(0, lambda: self.set_status(error_msg, False))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.is_loading = False
        
        thread = threading.Thread(target=predict_thread)
        thread.daemon = True
        thread.start()
    
    def generate_prediction(self):
        """生成预测（别名）"""
        self.predict_trend()
    
    def compare_multiple(self):
        """多币种对比分析"""
        if self.is_loading:
            return
        
        selected_coins = [coin for coin, var in self.coin_vars.items() if var.get()]
        if not selected_coins:
            messagebox.showwarning("警告", "请至少选择一个币种进行对比")
            return
        
        if not self.init_ai_predictor():
            return
        
        def compare_thread():
            try:
                self.is_loading = True
                self.root.after(0, lambda: self.set_status("正在进行多币种分析...", True))
                
                batch_data = {}
                timeframe = self.timeframe_var.get()
                limit = int(self.limit_var.get())
                
                # 获取所有选中币种的数据
                for coin in selected_coins:
                    try:
                        if self.coinglass_fetcher:
                            data = self.coinglass_fetcher.get_kline_data(coin, timeframe, limit)
                        else:
                            days_map = {'1h': 7, '4h': 30, '1d': 180, '1w': 365}
                            days = days_map.get(timeframe, 30)
                            data = self.backup_fetcher.get_price_data(coin, days)
                        
                        # 计算技术指标
                        analyzed_data = self.indicator_analyzer.analyze_price_data(data)
                        batch_data[coin] = analyzed_data
                        
                        self.root.after(0, lambda c=coin: self.set_status(f"已分析 {c}", True))
                        
                    except Exception as e:
                        logger.warning(f"获取 {coin} 数据失败: {e}")
                
                # 批量预测
                if batch_data:
                    predictions = self.ai_predictor.analyze_multiple_coins(batch_data, 7)
                    report = self.ai_predictor.generate_market_report(predictions)
                    
                    self.root.after(0, lambda: self.comparison_text.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.comparison_text.insert(tk.END, report))
                    
                    # 更新预测存储
                    self.predictions.update(predictions)
                
                self.root.after(0, lambda: self.set_status("多币种对比完成", False))
                
            except Exception as e:
                error_msg = f"多币种对比失败: {str(e)}"
                logger.error(error_msg)
                self.root.after(0, lambda: self.set_status(error_msg, False))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.is_loading = False
        
        thread = threading.Thread(target=compare_thread)
        thread.daemon = True
        thread.start()
    
    def start_comparison(self):
        """开始对比（别名）"""
        self.compare_multiple()
    
    def update_chart(self, timeframe_name):
        """更新图表"""
        symbol = self.current_symbol
        
        # 选择数据
        if timeframe_name == "小时级":
            data_dict = self.hourly_data
            chart_frame = self.小时级_chart_frame
            chart_type_var = self.小时级_chart_type_var
        else:
            data_dict = self.daily_data
            chart_frame = self.日级_chart_frame
            chart_type_var = self.日级_chart_type_var
        
        if symbol not in data_dict:
            return
        
        try:
            # 清除旧图表
            for widget in chart_frame.winfo_children():
                widget.destroy()
            
            chart_type = chart_type_var.get()
            df = data_dict[symbol]
            
            # 根据图表类型生成图表
            if chart_type == "价格+MA":
                fig = self.chart_plotter.plot_price_with_ma(df, f"{symbol}({timeframe_name})")
            elif chart_type == "布林带":
                fig = self.chart_plotter.plot_bollinger_bands(df, f"{symbol}({timeframe_name})")
            elif chart_type == "RSI":
                fig = self.chart_plotter.plot_rsi(df, f"{symbol}({timeframe_name})")
            elif chart_type == "MACD":
                fig = self.chart_plotter.plot_macd(df, f"{symbol}({timeframe_name})")
            elif chart_type == "KDJ":
                fig = self.chart_plotter.plot_kdj(df, f"{symbol}({timeframe_name})")
            elif chart_type == "成交量":
                fig = self.plot_volume_analysis(df, f"{symbol}({timeframe_name})")
            else:  # 综合分析
                fig = self.chart_plotter.plot_enhanced_comprehensive_chart(df, f"{symbol}({timeframe_name})", self.current_timeframe)
            
            # 嵌入图表
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # 保存图表引用
            setattr(self, f"current_figure_{timeframe_name}", fig)
            
        except Exception as e:
            logger.error(f"更新图表失败: {e}")
            messagebox.showerror("错误", f"更新图表失败: {str(e)}")
    
    def plot_kdj(self, df: pd.DataFrame, title: str):
        """绘制KDJ指标图表"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if all(col in df.columns for col in ['KDJ_K', 'KDJ_D', 'KDJ_J']):
            ax.plot(df.index, df['KDJ_K'], label='K', linewidth=2, color='blue')
            ax.plot(df.index, df['KDJ_D'], label='D', linewidth=2, color='red')
            ax.plot(df.index, df['KDJ_J'], label='J', linewidth=2, color='green')
            
            # 添加参考线
            ax.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='超买线(80)')
            ax.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='超卖线(20)')
            ax.axhline(y=50, color='gray', linestyle='-', alpha=0.5, label='中线(50)')
            
            # 填充区域
            ax.fill_between(df.index, 80, 100, color='red', alpha=0.1)
            ax.fill_between(df.index, 0, 20, color='green', alpha=0.1)
        
        ax.set_title(f'{title} KDJ随机指标', fontsize=14, fontweight='bold')
        ax.set_ylabel('KDJ值')
        ax.set_ylim(0, 100)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    
    def plot_volume_analysis(self, df: pd.DataFrame, title: str):
        """绘制成交量分析图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
        
        # 价格图
        ax1.plot(df.index, df['price'], linewidth=2, color='blue', label='价格')
        if 'MA20' in df.columns:
            ax1.plot(df.index, df['MA20'], linewidth=1.5, color='orange', alpha=0.7, label='MA20')
        ax1.set_title(f'{title} 价格走势', fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格 (USD)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 成交量图
        if 'volume' in df.columns:
            colors = ['red' if df['price'].iloc[i] < df['price'].iloc[i-1] else 'green' 
                     for i in range(1, len(df))]
            colors.insert(0, 'gray')  # 第一个数据点
            
            ax2.bar(df.index, df['volume'], color=colors, alpha=0.7)
            
            if 'Volume_Ratio' in df.columns:
                ax2_twin = ax2.twinx()
                ax2_twin.plot(df.index, df['Volume_Ratio'], color='purple', 
                            linewidth=2, label='成交量比率')
                ax2_twin.axhline(y=1.5, color='red', linestyle='--', alpha=0.7)
                ax2_twin.axhline(y=0.5, color='green', linestyle='--', alpha=0.7)
                ax2_twin.set_ylabel('成交量比率')
                ax2_twin.legend(loc='upper right')
        
        ax2.set_title('成交量分析', fontsize=12)
        ax2.set_ylabel('成交量')
        ax2.set_xlabel('时间')
        ax2.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    
    def update_indicators_display(self, df: pd.DataFrame, timeframe: str):
        """更新技术指标显示"""
        timeframe_name = "小时级" if timeframe in ['1h', '4h'] else "日级"
        text_widget = getattr(self, f"{timeframe_name}_indicators_text")
        
        text_widget.delete(1.0, tk.END)
        
        latest = df.iloc[-1]
        
        display_text = f"""最新技术指标 ({latest.name.strftime('%Y-%m-%d %H:%M')})

价格信息:
• 当前价格: ${latest['price']:.4f}
• 开盘价: ${latest.get('open', 0):.4f}
• 最高价: ${latest.get('high', 0):.4f}
• 最低价: ${latest.get('low', 0):.4f}
• 成交量: {latest.get('volume', 0):,.0f}

移动平均线:
• MA5: ${latest.get('MA5', 0):.4f}
• MA20: ${latest.get('MA20', 0):.4f}
• MA50: ${latest.get('MA50', 0):.4f}

技术指标:
• RSI: {latest.get('RSI', 0):.2f}
• KDJ K: {latest.get('KDJ_K', 0):.2f}
• KDJ D: {latest.get('KDJ_D', 0):.2f}
• KDJ J: {latest.get('KDJ_J', 0):.2f}

MACD:
• MACD: {latest.get('MACD', 0):.6f}
• 信号线: {latest.get('MACD_Signal', 0):.6f}
• 柱状图: {latest.get('MACD_Histogram', 0):.6f}

布林带:
• 上轨: ${latest.get('BB_Upper', 0):.4f}
• 中轨: ${latest.get('BB_Middle', 0):.4f}
• 下轨: ${latest.get('BB_Lower', 0):.4f}

斐波那契位:
• 23.6%: ${latest.get('Fib_23.6', 0):.4f}
• 38.2%: ${latest.get('Fib_38.2', 0):.4f}
• 61.8%: ${latest.get('Fib_61.8', 0):.4f}"""
        
        text_widget.insert(tk.END, display_text)
    
    def update_signals_display(self, df: pd.DataFrame, timeframe: str):
        """更新交易信号显示"""
        timeframe_name = "小时级" if timeframe in ['1h', '4h'] else "日级"
        text_widget = getattr(self, f"{timeframe_name}_signals_text")
        
        text_widget.delete(1.0, tk.END)
        
        latest = df.iloc[-1]
        
        # 分析各种信号
        signals = []
        
        # MA信号
        ma_signal = latest.get('MA_Signal', 0)
        if ma_signal > 0:
            signals.append("✅ MA金叉买入")
        elif ma_signal < 0:
            signals.append("❌ MA死叉卖出")
        
        # RSI信号
        rsi_signal = latest.get('RSI_Signal', 0)
        rsi_value = latest.get('RSI', 50)
        if rsi_signal > 0:
            signals.append("✅ RSI超卖买入")
        elif rsi_signal < 0:
            signals.append("❌ RSI超买卖出")
        elif rsi_value > 70:
            signals.append("⚠️ RSI超买警告")
        elif rsi_value < 30:
            signals.append("⚠️ RSI超卖警告")
        
        # KDJ信号
        kdj_signal = latest.get('KDJ_Signal', 0)
        kdj_k = latest.get('KDJ_K', 50)
        kdj_d = latest.get('KDJ_D', 50)
        if kdj_signal > 0:
            signals.append("✅ KDJ买入信号")
        elif kdj_signal < 0:
            signals.append("❌ KDJ卖出信号")
        
        if kdj_k > kdj_d and kdj_k < 80:
            signals.append("📈 KDJ金叉向上")
        elif kdj_k < kdj_d and kdj_k > 20:
            signals.append("📉 KDJ死叉向下")
        
        # MACD信号
        macd_signal = latest.get('MACD_Signal_Trade', 0)
        if macd_signal > 0:
            signals.append("✅ MACD金叉买入")
        elif macd_signal < 0:
            signals.append("❌ MACD死叉卖出")
        
        # 布林带信号
        bb_signal = latest.get('BB_Signal', 0)
        if bb_signal > 0:
            signals.append("✅ 触及布林下轨")
        elif bb_signal < 0:
            signals.append("❌ 触及布林上轨")
        
        # 成交量信号
        volume_signal = latest.get('Volume_Signal', 0)
        if volume_signal > 0:
            signals.append("📊 放量突破")
        elif volume_signal < 0:
            signals.append("📊 缩量下跌")
        
        # 综合信号
        combined_signal = latest.get('Combined_Signal', 0)
        if combined_signal >= 3:
            signals.append("🚀 强烈买入信号")
        elif combined_signal >= 2:
            signals.append("📈 买入信号")
        elif combined_signal <= -3:
            signals.append("💥 强烈卖出信号")
        elif combined_signal <= -2:
            signals.append("📉 卖出信号")
        else:
            signals.append("⏸️ 观望信号")
        
        display_text = f"交易信号分析 ({timeframe})\n"
        display_text += "=" * 30 + "\n\n"
        
        if signals:
            for signal in signals:
                display_text += f"{signal}\n"
        else:
            display_text += "暂无明确信号\n"
        
        display_text += f"\n综合评分: {combined_signal}\n"
        display_text += f"信号强度: {'强' if abs(combined_signal) >= 3 else '中' if abs(combined_signal) >= 2 else '弱'}"
        
        text_widget.insert(tk.END, display_text)
    
    def update_prediction_display(self, prediction):
        """更新预测显示"""
        self.prediction_text.delete(1.0, tk.END)
        
        display_text = f"""🔮 AI趋势预测报告
{'='*50}

基本信息:
• 币种: {prediction.get('symbol', 'N/A')}
• 预测时间: {prediction.get('prediction_date', 'N/A')}
• 预测周期: {prediction.get('prediction_days', 'N/A')}天
• 数据来源: {prediction.get('data_points', 'N/A')}个数据点

预测结果:
• 趋势方向: {prediction.get('trend_direction', 'N/A')}
• 信心度: {prediction.get('confidence', 'N/A')}
• 风险等级: {prediction.get('risk_level', 'N/A')}
• 交易建议: {prediction.get('trading_suggestion', 'N/A')}
• 信号强度: {prediction.get('signal_strength', 'N/A')}/10

价格预测:
• 当前价格: ${prediction.get('current_price', 0):.4f}
• 目标价格: ${prediction.get('target_price', 0):.4f}
• 支撑位: ${prediction.get('support_level', 0):.4f}
• 阻力位: ${prediction.get('resistance_level', 0):.4f}

交易区间:
• 买入区间: ${prediction.get('buy_zone_low', 0):.4f} - ${prediction.get('buy_zone_high', 0):.4f}
• 卖出区间: ${prediction.get('sell_zone_low', 0):.4f} - ${prediction.get('sell_zone_high', 0):.4f}
• 止损位: ${prediction.get('stop_loss', 0):.4f}

专业分析:
{prediction.get('analysis_summary', 'N/A')}

斐波那契分析:
{prediction.get('fibonacci_levels', 'N/A')}

成交量分析:
{prediction.get('volume_analysis', 'N/A')}

关键因素:"""
        
        key_factors = prediction.get('key_factors', [])
        for i, factor in enumerate(key_factors, 1):
            display_text += f"\n{i}. {factor}"
        
        display_text += "\n\n⚠️ 免责声明: 本预测仅供参考，不构成投资建议。数字货币投资存在高风险，请谨慎决策。"
        
        self.prediction_text.insert(tk.END, display_text)
    
    def init_ai_predictor(self):
        """初始化AI预测器"""
        api_key = self.deepseek_key_var.get().strip()
        if not api_key:
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if api_key:
                self.deepseek_key_var.set(api_key)
        
        if not api_key:
            messagebox.showwarning("警告", "请先配置DeepSeek API密钥")
            return False
        
        try:
            if not self.ai_predictor:
                self.ai_predictor = AIPredictor(api_key=api_key)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"初始化AI预测器失败: {str(e)}")
            return False
    
    def save_chart(self, timeframe_name):
        """保存图表"""
        fig_attr = f"current_figure_{timeframe_name}"
        if hasattr(self, fig_attr):
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")],
                initialname=f"{self.current_symbol}_{timeframe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            if filename:
                try:
                    fig = getattr(self, fig_attr)
                    fig.savefig(filename, dpi=300, bbox_inches='tight')
                    messagebox.showinfo("成功", f"图表已保存: {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def export_report(self):
        """导出预测报告"""
        if not self.predictions:
            messagebox.showwarning("警告", "没有预测数据可导出")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")],
            initialname=f"prediction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.predictions, f, ensure_ascii=False, indent=2)
                else:
                    if self.ai_predictor:
                        report = self.ai_predictor.generate_market_report(self.predictions)
                    else:
                        report = str(self.predictions)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report)
                messagebox.showinfo("成功", f"报告已导出: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def set_status(self, message, loading=False):
        """设置状态"""
        self.status_var.set(message)
        if loading:
            self.progress.start()
        else:
            self.progress.stop()
    
    def set_buttons_state(self, enabled, analyze=False, predict=False):
        """设置按钮状态"""
        state = "normal" if enabled else "disabled"
        self.fetch_btn.config(state=state)
        
        if analyze:
            self.analyze_btn.config(state=state)
        if predict:
            self.predict_btn.config(state=state)
            self.compare_btn.config(state=state)


def main():
    """主函数"""
    # 检查依赖
    try:
        import matplotlib
        import pandas
        import numpy
        import requests
    except ImportError as e:
        print(f"缺少必要的依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 创建主窗口
    root = tk.Tk()
    app = CoinglassAnalyzerGUI(root)
    
    # 设置窗口属性
    try:
        root.state('zoomed')  # Linux下最大化
    except:
        pass
    
    # 启动GUI
    root.mainloop()


if __name__ == "__main__":
    main()