"""
图表绘制模块
使用matplotlib和plotly创建交互式价格图表和技术指标图表
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ChartPlotter:
    """图表绘制器"""
    
    def __init__(self):
        self.color_scheme = {
            'price': '#2E86C1',
            'ma5': '#E74C3C',
            'ma20': '#F39C12',
            'ma50': '#8E44AD',
            'bb_upper': '#27AE60',
            'bb_middle': '#3498DB',
            'bb_lower': '#27AE60',
            'volume': '#95A5A6',
            'rsi': '#E67E22',
            'macd': '#9B59B6',
            'signal': '#E74C3C'
        }
    
    def plot_price_with_ma(self, df: pd.DataFrame, symbol: str, 
                          ma_periods: List[int] = [5, 20, 50],
                          figsize: Tuple[int, int] = (12, 8)) -> Figure:
        """
        绘制价格图和移动平均线
        
        Args:
            df: 包含价格和MA数据的DataFrame
            symbol: 数字货币符号
            ma_periods: 移动平均线周期列表
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            # 绘制价格线
            ax.plot(df.index, df['price'], 
                   color=self.color_scheme['price'], 
                   linewidth=2, label=f'{symbol} Price', alpha=0.8)
            
            # 绘制移动平均线
            colors = [self.color_scheme['ma5'], self.color_scheme['ma20'], self.color_scheme['ma50']]
            for i, period in enumerate(ma_periods):
                ma_col = f'MA{period}'
                if ma_col in df.columns:
                    color = colors[i] if i < len(colors) else f'C{i}'
                    ax.plot(df.index, df[ma_col], 
                           color=color, linewidth=1.5, 
                           label=f'MA{period}', alpha=0.7)
            
            # 设置图表样式
            ax.set_title(f'{symbol} 价格走势图', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('价格 (USD)', fontsize=12)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴日期
            if len(df) > 30:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} 价格和MA图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制价格MA图表失败: {e}")
            raise
    
    def plot_bollinger_bands(self, df: pd.DataFrame, symbol: str,
                           figsize: Tuple[int, int] = (12, 8)) -> Figure:
        """
        绘制布林带图表
        
        Args:
            df: 包含价格和布林带数据的DataFrame
            symbol: 数字货币符号
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            # 绘制价格线
            ax.plot(df.index, df['price'], 
                   color=self.color_scheme['price'], 
                   linewidth=2, label=f'{symbol} Price')
            
            # 绘制布林带
            if all(col in df.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                # 中轨
                ax.plot(df.index, df['BB_Middle'], 
                       color=self.color_scheme['bb_middle'], 
                       linewidth=1.5, label='BB Middle (MA20)', linestyle='--')
                
                # 上轨和下轨
                ax.plot(df.index, df['BB_Upper'], 
                       color=self.color_scheme['bb_upper'], 
                       linewidth=1, label='BB Upper', alpha=0.7)
                ax.plot(df.index, df['BB_Lower'], 
                       color=self.color_scheme['bb_lower'], 
                       linewidth=1, label='BB Lower', alpha=0.7)
                
                # 填充布林带区域
                ax.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], 
                              color=self.color_scheme['bb_upper'], alpha=0.1)
            
            # 设置图表样式
            ax.set_title(f'{symbol} 布林带图', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('价格 (USD)', fontsize=12)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴
            if len(df) > 30:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} 布林带图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制布林带图表失败: {e}")
            raise
    
    def plot_rsi(self, df: pd.DataFrame, symbol: str,
                figsize: Tuple[int, int] = (12, 6)) -> Figure:
        """
        绘制RSI指标图表
        
        Args:
            df: 包含RSI数据的DataFrame
            symbol: 数字货币符号
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            if 'RSI' in df.columns:
                # 绘制RSI线
                ax.plot(df.index, df['RSI'], 
                       color=self.color_scheme['rsi'], 
                       linewidth=2, label='RSI')
                
                # 添加超买超卖线
                ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='超买线 (70)')
                ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='超卖线 (30)')
                ax.axhline(y=50, color='gray', linestyle='-', alpha=0.5, label='中线 (50)')
                
                # 填充超买超卖区域
                ax.fill_between(df.index, 70, 100, color='red', alpha=0.1)
                ax.fill_between(df.index, 0, 30, color='green', alpha=0.1)
            
            # 设置图表样式
            ax.set_title(f'{symbol} RSI 相对强弱指标', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('RSI', fontsize=12)
            ax.set_ylim(0, 100)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴
            if len(df) > 30:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} RSI图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制RSI图表失败: {e}")
            raise
    
    def plot_macd(self, df: pd.DataFrame, symbol: str,
                 figsize: Tuple[int, int] = (12, 6)) -> Figure:
        """
        绘制MACD指标图表
        
        Args:
            df: 包含MACD数据的DataFrame
            symbol: 数字货币符号
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            if all(col in df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
                # 绘制MACD线和信号线
                ax.plot(df.index, df['MACD'], 
                       color=self.color_scheme['macd'], 
                       linewidth=2, label='MACD')
                ax.plot(df.index, df['MACD_Signal'], 
                       color=self.color_scheme['signal'], 
                       linewidth=1.5, label='Signal', linestyle='--')
                
                # 绘制MACD柱状图
                colors = ['red' if x < 0 else 'green' for x in df['MACD_Histogram']]
                ax.bar(df.index, df['MACD_Histogram'], 
                      color=colors, alpha=0.6, width=1, label='Histogram')
                
                # 添加零线
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            # 设置图表样式
            ax.set_title(f'{symbol} MACD 指标', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('MACD', fontsize=12)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴
            if len(df) > 30:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} MACD图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制MACD图表失败: {e}")
            raise
    
    def plot_comprehensive_chart(self, df: pd.DataFrame, symbol: str,
                               figsize: Tuple[int, int] = (15, 12)) -> Figure:
        """
        绘制综合技术分析图表
        
        Args:
            df: 包含所有技术指标的DataFrame
            symbol: 数字货币符号
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, axes = plt.subplots(4, 1, figsize=figsize, 
                                   gridspec_kw={'height_ratios': [3, 1, 1, 1]})
            
            # 第一个子图：价格和移动平均线
            ax1 = axes[0]
            ax1.plot(df.index, df['price'], color=self.color_scheme['price'], 
                    linewidth=2, label=f'{symbol} Price')
            
            # 移动平均线
            for ma in ['MA5', 'MA20', 'MA50']:
                if ma in df.columns:
                    ax1.plot(df.index, df[ma], linewidth=1.5, 
                            label=ma, alpha=0.7)
            
            # 布林带
            if all(col in df.columns for col in ['BB_Upper', 'BB_Lower']):
                ax1.plot(df.index, df['BB_Upper'], color='green', 
                        linewidth=1, alpha=0.5, label='BB Upper')
                ax1.plot(df.index, df['BB_Lower'], color='green', 
                        linewidth=1, alpha=0.5, label='BB Lower')
                ax1.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], 
                               color='green', alpha=0.05)
            
            ax1.set_title(f'{symbol} 综合技术分析', fontsize=16, fontweight='bold')
            ax1.set_ylabel('价格 (USD)', fontsize=12)
            ax1.legend(loc='upper left', fontsize=9)
            ax1.grid(True, alpha=0.3)
            
            # 第二个子图：成交量
            ax2 = axes[1]
            if 'volume' in df.columns:
                ax2.bar(df.index, df['volume'], color=self.color_scheme['volume'], 
                       alpha=0.6, width=1)
            ax2.set_ylabel('成交量', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # 第三个子图：RSI
            ax3 = axes[2]
            if 'RSI' in df.columns:
                ax3.plot(df.index, df['RSI'], color=self.color_scheme['rsi'], 
                        linewidth=2)
                ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                ax3.fill_between(df.index, 70, 100, color='red', alpha=0.1)
                ax3.fill_between(df.index, 0, 30, color='green', alpha=0.1)
            ax3.set_ylabel('RSI', fontsize=12)
            ax3.set_ylim(0, 100)
            ax3.grid(True, alpha=0.3)
            
            # 第四个子图：MACD
            ax4 = axes[3]
            if all(col in df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
                ax4.plot(df.index, df['MACD'], color=self.color_scheme['macd'], 
                        linewidth=2, label='MACD')
                ax4.plot(df.index, df['MACD_Signal'], color=self.color_scheme['signal'], 
                        linewidth=1.5, label='Signal', linestyle='--')
                
                colors = ['red' if x < 0 else 'green' for x in df['MACD_Histogram']]
                ax4.bar(df.index, df['MACD_Histogram'], color=colors, alpha=0.6, width=1)
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            ax4.set_ylabel('MACD', fontsize=12)
            ax4.set_xlabel('时间', fontsize=12)
            ax4.grid(True, alpha=0.3)
            
            # 格式化所有子图的x轴
            for ax in axes:
                if len(df) > 30:
                    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                else:
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} 综合技术分析图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制综合图表失败: {e}")
            raise
    
    def create_interactive_chart(self, df: pd.DataFrame, symbol: str) -> go.Figure:
        """
        创建交互式图表 (使用Plotly)
        
        Args:
            df: 包含技术指标的DataFrame
            symbol: 数字货币符号
            
        Returns:
            Plotly图表对象
        """
        try:
            # 创建子图
            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=(f'{symbol} 价格走势', '成交量', 'RSI', 'MACD'),
                row_heights=[0.5, 0.2, 0.15, 0.15]
            )
            
            # 主图：价格和技术指标
            fig.add_trace(
                go.Scatter(x=df.index, y=df['price'], 
                          name=f'{symbol} Price', line=dict(color='blue', width=2)),
                row=1, col=1
            )
            
            # 移动平均线
            for ma in ['MA5', 'MA20', 'MA50']:
                if ma in df.columns:
                    fig.add_trace(
                        go.Scatter(x=df.index, y=df[ma], name=ma, 
                                 line=dict(width=1.5), opacity=0.7),
                        row=1, col=1
                    )
            
            # 布林带
            if all(col in df.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper',
                             line=dict(color='green', width=1), opacity=0.5),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower',
                             line=dict(color='green', width=1), opacity=0.5,
                             fill='tonexty', fillcolor='rgba(0,255,0,0.1)'),
                    row=1, col=1
                )
            
            # 成交量
            if 'volume' in df.columns:
                fig.add_trace(
                    go.Bar(x=df.index, y=df['volume'], name='Volume',
                          marker_color='lightblue', opacity=0.6),
                    row=2, col=1
                )
            
            # RSI
            if 'RSI' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['RSI'], name='RSI',
                             line=dict(color='orange', width=2)),
                    row=3, col=1
                )
                
                # RSI参考线
                fig.add_hline(y=70, line_dash="dash", line_color="red", 
                            opacity=0.7, row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", 
                            opacity=0.7, row=3, col=1)
            
            # MACD
            if all(col in df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['MACD'], name='MACD',
                             line=dict(color='purple', width=2)),
                    row=4, col=1
                )
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal',
                             line=dict(color='red', width=1.5, dash='dash')),
                    row=4, col=1
                )
                
                # MACD柱状图
                colors = ['red' if x < 0 else 'green' for x in df['MACD_Histogram']]
                fig.add_trace(
                    go.Bar(x=df.index, y=df['MACD_Histogram'], name='Histogram',
                          marker_color=colors, opacity=0.6),
                    row=4, col=1
                )
            
            # 更新布局
            fig.update_layout(
                title=f'{symbol} 交互式技术分析图表',
                xaxis_title='时间',
                height=800,
                showlegend=True,
                hovermode='x unified'
            )
            
            # 更新y轴标签
            fig.update_yaxes(title_text="价格 (USD)", row=1, col=1)
            fig.update_yaxes(title_text="成交量", row=2, col=1)
            fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
            fig.update_yaxes(title_text="MACD", row=4, col=1)
            
            logger.info(f"成功创建 {symbol} 交互式图表")
            return fig
            
        except Exception as e:
            logger.error(f"创建交互式图表失败: {e}")
            raise
    
    def plot_kdj(self, df: pd.DataFrame, symbol: str,
                figsize: Tuple[int, int] = (12, 6)) -> Figure:
        """
        绘制KDJ指标图表
        
        Args:
            df: 包含KDJ数据的DataFrame
            symbol: 数字货币符号
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            if all(col in df.columns for col in ['KDJ_K', 'KDJ_D', 'KDJ_J']):
                # 绘制KDJ三线
                ax.plot(df.index, df['KDJ_K'], color='blue', linewidth=2, label='K线')
                ax.plot(df.index, df['KDJ_D'], color='red', linewidth=2, label='D线')
                ax.plot(df.index, df['KDJ_J'], color='green', linewidth=2, label='J线')
                
                # 添加参考线
                ax.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='超买线(80)')
                ax.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='超卖线(20)')
                ax.axhline(y=50, color='gray', linestyle='-', alpha=0.5, label='中线(50)')
                
                # 填充超买超卖区域
                ax.fill_between(df.index, 80, 100, color='red', alpha=0.1, label='超买区域')
                ax.fill_between(df.index, 0, 20, color='green', alpha=0.1, label='超卖区域')
                
                # 标记金叉死叉点
                k_above_d = df['KDJ_K'] > df['KDJ_D']
                k_above_d_prev = k_above_d.shift(1)
                golden_cross = (~k_above_d_prev) & k_above_d
                death_cross = k_above_d_prev & (~k_above_d)
                
                if golden_cross.any():
                    ax.scatter(df.index[golden_cross], df['KDJ_K'][golden_cross], 
                             color='gold', s=100, marker='^', label='金叉', zorder=5)
                if death_cross.any():
                    ax.scatter(df.index[death_cross], df['KDJ_K'][death_cross], 
                             color='black', s=100, marker='v', label='死叉', zorder=5)
            
            # 设置图表样式
            ax.set_title(f'{symbol} KDJ随机指标', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('KDJ值', fontsize=12)
            ax.set_ylim(0, 100)
            ax.legend(loc='upper left', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴
            if len(df) > 30:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} KDJ图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制KDJ图表失败: {e}")
            raise
    
    def plot_fibonacci_levels(self, df: pd.DataFrame, symbol: str,
                            figsize: Tuple[int, int] = (12, 8)) -> Figure:
        """
        绘制斐波那契水平图表
        
        Args:
            df: 包含价格和斐波那契数据的DataFrame
            symbol: 数字货币符号
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(figsize=figsize)
            
            # 绘制价格线
            ax.plot(df.index, df['price'], color='blue', linewidth=2, label=f'{symbol} Price')
            
            # 绘制斐波那契水平
            fib_colors = ['red', 'orange', 'yellow', 'green']
            fib_levels = ['Fib_23.6', 'Fib_38.2', 'Fib_50.0', 'Fib_61.8']
            fib_labels = ['23.6%', '38.2%', '50%', '61.8%']
            
            for i, (level, label) in enumerate(zip(fib_levels, fib_labels)):
                if level in df.columns:
                    color = fib_colors[i % len(fib_colors)]
                    ax.plot(df.index, df[level], color=color, linestyle='--', 
                           alpha=0.7, linewidth=1.5, label=f'Fib {label}')
            
            # 绘制高低点
            if 'Fib_High' in df.columns and 'Fib_Low' in df.columns:
                ax.plot(df.index, df['Fib_High'], color='red', linestyle=':', 
                       alpha=0.5, linewidth=1, label='区间高点')
                ax.plot(df.index, df['Fib_Low'], color='green', linestyle=':', 
                       alpha=0.5, linewidth=1, label='区间低点')
            
            # 设置图表样式
            ax.set_title(f'{symbol} 斐波那契回调位分析', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('价格 (USD)', fontsize=12)
            ax.legend(loc='upper left', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴
            if len(df) > 30:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            else:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} 斐波那契图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制斐波那契图表失败: {e}")
            raise
    
    def plot_enhanced_comprehensive_chart(self, df: pd.DataFrame, symbol: str,
                                        timeframe: str = "1h",
                                        figsize: Tuple[int, int] = (16, 14)) -> Figure:
        """
        绘制增强版综合技术分析图表，包含所有指标
        
        Args:
            df: 包含所有技术指标的DataFrame
            symbol: 数字货币符号
            timeframe: 时间框架
            figsize: 图表尺寸
            
        Returns:
            matplotlib Figure对象
        """
        try:
            fig, axes = plt.subplots(5, 1, figsize=figsize, 
                                   gridspec_kw={'height_ratios': [3, 1, 1, 1, 1]})
            
            # 第一个子图：价格、移动平均线、布林带、斐波那契
            ax1 = axes[0]
            ax1.plot(df.index, df['price'], color='black', linewidth=2, label=f'{symbol} Price')
            
            # 移动平均线
            ma_colors = {'MA5': 'red', 'MA20': 'orange', 'MA50': 'purple'}
            for ma, color in ma_colors.items():
                if ma in df.columns:
                    ax1.plot(df.index, df[ma], color=color, linewidth=1.5, 
                            label=ma, alpha=0.8)
            
            # 布林带
            if all(col in df.columns for col in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
                ax1.plot(df.index, df['BB_Upper'], color='green', linewidth=1, alpha=0.6, label='BB Upper')
                ax1.plot(df.index, df['BB_Lower'], color='green', linewidth=1, alpha=0.6, label='BB Lower')
                ax1.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], 
                               color='green', alpha=0.05)
            
            # 斐波那契关键位
            fib_levels = ['Fib_38.2', 'Fib_61.8']
            fib_colors = ['orange', 'red']
            for level, color in zip(fib_levels, fib_colors):
                if level in df.columns:
                    ax1.plot(df.index, df[level], color=color, linestyle='--', 
                           alpha=0.5, linewidth=1, label=f'{level.split("_")[1]}')
            
            ax1.set_title(f'{symbol} 综合技术分析 ({timeframe})', fontsize=16, fontweight='bold')
            ax1.set_ylabel('价格 (USD)', fontsize=12)
            ax1.legend(loc='upper left', fontsize=9, ncol=2)
            ax1.grid(True, alpha=0.3)
            
            # 第二个子图：成交量
            ax2 = axes[1]
            if 'volume' in df.columns:
                # 根据价格涨跌着色
                colors = []
                for i in range(len(df)):
                    if i == 0:
                        colors.append('gray')
                    else:
                        colors.append('red' if df['close'].iloc[i] >= df['close'].iloc[i-1] else 'green')
                
                ax2.bar(df.index, df['volume'], color=colors, alpha=0.7, width=1)
                
                # 成交量移动平均
                if 'Volume_Ratio' in df.columns:
                    ax2_twin = ax2.twinx()
                    ax2_twin.plot(df.index, df['Volume_Ratio'], color='purple', 
                                linewidth=1.5, label='成交量比率')
                    ax2_twin.axhline(y=1.5, color='red', linestyle='--', alpha=0.5)
                    ax2_twin.set_ylabel('成交量比率', fontsize=10)
                    ax2_twin.legend(loc='upper right', fontsize=8)
            
            ax2.set_ylabel('成交量', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # 第三个子图：RSI
            ax3 = axes[2]
            if 'RSI' in df.columns:
                ax3.plot(df.index, df['RSI'], color='orange', linewidth=2, label='RSI')
                ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='超买(70)')
                ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='超卖(30)')
                ax3.fill_between(df.index, 70, 100, color='red', alpha=0.1)
                ax3.fill_between(df.index, 0, 30, color='green', alpha=0.1)
            ax3.set_ylabel('RSI', fontsize=12)
            ax3.set_ylim(0, 100)
            ax3.legend(loc='upper left', fontsize=8)
            ax3.grid(True, alpha=0.3)
            
            # 第四个子图：KDJ
            ax4 = axes[3]
            if all(col in df.columns for col in ['KDJ_K', 'KDJ_D', 'KDJ_J']):
                ax4.plot(df.index, df['KDJ_K'], color='blue', linewidth=2, label='K')
                ax4.plot(df.index, df['KDJ_D'], color='red', linewidth=2, label='D')
                ax4.plot(df.index, df['KDJ_J'], color='green', linewidth=1.5, label='J', alpha=0.8)
                
                ax4.axhline(y=80, color='red', linestyle='--', alpha=0.7)
                ax4.axhline(y=20, color='green', linestyle='--', alpha=0.7)
                ax4.fill_between(df.index, 80, 100, color='red', alpha=0.1)
                ax4.fill_between(df.index, 0, 20, color='green', alpha=0.1)
            ax4.set_ylabel('KDJ', fontsize=12)
            ax4.set_ylim(0, 100)
            ax4.legend(loc='upper left', fontsize=8)
            ax4.grid(True, alpha=0.3)
            
            # 第五个子图：MACD
            ax5 = axes[4]
            if all(col in df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
                ax5.plot(df.index, df['MACD'], color='blue', linewidth=2, label='MACD')
                ax5.plot(df.index, df['MACD_Signal'], color='red', linewidth=1.5, 
                        label='Signal', linestyle='--')
                
                colors = ['red' if x < 0 else 'green' for x in df['MACD_Histogram']]
                ax5.bar(df.index, df['MACD_Histogram'], color=colors, alpha=0.6, 
                       width=1, label='Histogram')
                ax5.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            ax5.set_ylabel('MACD', fontsize=12)
            ax5.set_xlabel('时间', fontsize=12)
            ax5.legend(loc='upper left', fontsize=8)
            ax5.grid(True, alpha=0.3)
            
            # 格式化所有子图的x轴
            for ax in axes:
                if len(df) > 50:
                    ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                elif len(df) > 20:
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                else:
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            logger.info(f"成功绘制 {symbol} 增强综合分析图表")
            return fig
            
        except Exception as e:
            logger.error(f"绘制增强综合图表失败: {e}")
            raise


if __name__ == "__main__":
    # 测试图表绘制功能
    import sys
    sys.path.append('.')
    from data_fetcher import CryptoDataFetcher
    from technical_indicators import IndicatorAnalyzer
    
    try:
        # 获取测试数据
        fetcher = CryptoDataFetcher()
        btc_data = fetcher.get_price_data('BTC', days=30)
        
        # 计算技术指标
        analyzer = IndicatorAnalyzer()
        indicators_data = analyzer.analyze_price_data(btc_data)
        
        # 创建图表绘制器
        plotter = ChartPlotter()
        
        # 测试绘制价格MA图表
        fig1 = plotter.plot_price_with_ma(indicators_data, 'BTC')
        plt.savefig('/workspace/test_price_ma.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 测试绘制布林带图表
        fig2 = plotter.plot_bollinger_bands(indicators_data, 'BTC')
        plt.savefig('/workspace/test_bollinger.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("图表绘制测试完成，已保存测试图片")
        
    except Exception as e:
        print(f"测试失败: {e}")
