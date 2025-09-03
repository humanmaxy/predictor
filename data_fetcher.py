"""
数据获取模块
支持CoinGlass API和CoinGecko API获取数字货币行情数据
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import os
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoinglassDataFetcher:
    """Coinglass数据获取器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('COINGLASS_API_KEY')
        self.base_url = "https://open-api-v4.coinglass.com/api"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'CG-API-KEY': self.api_key,
                'accept': 'application/json'
            })
        
        # 支持的交易对映射
        self.symbol_map = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT', 
            'SOL': 'SOLUSDT',
            'XRP': 'XRPUSDT',
            'ADA': 'ADAUSDT',
            'DOT': 'DOTUSDT',
            'LINK': 'LINKUSDT',
            'LTC': 'LTCUSDT',
            'BCH': 'BCHUSDT',
            'UNI': 'UNIUSDT',
            'AVAX': 'AVAXUSDT',
            'MATIC': 'MATICUSDT'
        }
    
    def get_kline_data(self, symbol: str, interval: str = '1h', limit: int = 200) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号 (如 'BTC', 'ETH')
            interval: 时间间隔 ('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w')
            limit: 数据条数限制
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        try:
            # 转换符号
            trading_pair = self.symbol_map.get(symbol.upper(), f"{symbol.upper()}USDT")
            
            url = f"{self.base_url}/spot/kline"
            params = {
                'symbol': trading_pair,
                'interval': interval,
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == '0' and data.get('data'):
                klines = data['data']
                
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                    'taker_buy_quote_volume', 'ignore'
                ])
                
                # 数据类型转换
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 设置索引
                df.set_index('timestamp', inplace=True)
                
                # 重命名列以保持兼容性
                df['price'] = df['close']
                df['symbol'] = symbol.upper()
                
                logger.info(f"成功获取 {symbol} {interval} K线数据，共{len(df)}条记录")
                return df[['open', 'high', 'low', 'close', 'price', 'volume', 'symbol']]
            else:
                error_msg = data.get('msg', '未知错误')
                raise Exception(f"API返回错误: {error_msg}")
                
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise
    
    def get_ticker_data(self, symbol: str) -> Dict:
        """
        获取ticker数据
        
        Args:
            symbol: 交易对符号
            
        Returns:
            ticker数据字典
        """
        try:
            trading_pair = self.symbol_map.get(symbol.upper(), f"{symbol.upper()}USDT")
            
            url = f"{self.base_url}/spot/ticker"
            params = {'symbol': trading_pair}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == '0' and data.get('data'):
                ticker = data['data']
                return {
                    'symbol': symbol.upper(),
                    'price': float(ticker.get('lastPrice', 0)),
                    'change_24h': float(ticker.get('priceChangePercent', 0)),
                    'volume_24h': float(ticker.get('volume', 0)),
                    'high_24h': float(ticker.get('highPrice', 0)),
                    'low_24h': float(ticker.get('lowPrice', 0)),
                    'open_price': float(ticker.get('openPrice', 0))
                }
            else:
                raise Exception(f"API返回错误: {data.get('msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"获取ticker数据失败: {e}")
            raise
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的交易对列表"""
        return list(self.symbol_map.keys())


class CryptoDataFetcher:
    """数字货币数据获取器"""
    
    def __init__(self):
        # use_http = os.getenv('USE_HTTP', 'false').lower() == 'true'
        # protocol = 'http' if use_http else 'https'
        # self.base_url = f"{protocol}://api.coingecko.com/api/v3"
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoAnalyzer/1.0'
        })
        
        # 支持的数字货币映射
        self.crypto_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'UNI': 'uniswap'
        }
    
    def get_price_data(self, symbol: str, days: int = 30, vs_currency: str = 'usd') -> pd.DataFrame:
        """
        获取历史价格数据
        
        Args:
            symbol: 数字货币符号 (如 'BTC', 'ETH')
            days: 历史数据天数
            vs_currency: 对比货币，默认USD
            
        Returns:
            包含价格数据的DataFrame
        """
        try:
            # 转换符号到CoinGecko ID
            coin_id = self.crypto_map.get(symbol.upper())
            if not coin_id:
                raise ValueError(f"不支持的数字货币符号: {symbol}")
            
            # 构建API请求
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': vs_currency,
                'days': days,
                'interval': 'hourly' if days <= 1 else 'daily'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析数据
            prices = data['prices']
            volumes = data['total_volumes']
            market_caps = data['market_caps']
            
            # 创建DataFrame
            df = pd.DataFrame({
                'timestamp': [item[0] for item in prices],
                'price': [item[1] for item in prices],
                'volume': [item[1] for item in volumes],
                'market_cap': [item[1] for item in market_caps]
            })
            
            # 转换时间戳
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            df.drop('timestamp', axis=1, inplace=True)
            
            # 添加币种信息
            df['symbol'] = symbol.upper()
            
            logger.info(f"成功获取 {symbol} {days}天的价格数据，共{len(df)}条记录")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求错误: {e}")
            raise
        except Exception as e:
            logger.error(f"获取价格数据失败: {e}")
            raise
    
    def get_current_price(self, symbols: List[str], vs_currency: str = 'usd') -> Dict:
        """
        获取当前价格
        
        Args:
            symbols: 数字货币符号列表
            vs_currency: 对比货币
            
        Returns:
            包含当前价格信息的字典
        """
        try:
            # 转换符号到CoinGecko ID
            coin_ids = []
            for symbol in symbols:
                coin_id = self.crypto_map.get(symbol.upper())
                if coin_id:
                    coin_ids.append(coin_id)
            
            if not coin_ids:
                raise ValueError("没有有效的数字货币符号")
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': vs_currency,
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 转换结果格式
            result = {}
            for symbol in symbols:
                coin_id = self.crypto_map.get(symbol.upper())
                if coin_id and coin_id in data:
                    result[symbol.upper()] = data[coin_id]
            
            logger.info(f"成功获取 {len(result)} 个币种的当前价格")
            return result
            
        except Exception as e:
            logger.error(f"获取当前价格失败: {e}")
            raise
    
    def get_market_data(self, symbol: str) -> Dict:
        """
        获取市场数据
        
        Args:
            symbol: 数字货币符号
            
        Returns:
            市场数据字典
        """
        try:
            coin_id = self.crypto_map.get(symbol.upper())
            if not coin_id:
                raise ValueError(f"不支持的数字货币符号: {symbol}")
            
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            market_data = data.get('market_data', {})
            
            # 提取关键市场数据
            result = {
                'name': data.get('name'),
                'symbol': data.get('symbol', '').upper(),
                'current_price': market_data.get('current_price', {}).get('usd'),
                'market_cap': market_data.get('market_cap', {}).get('usd'),
                'total_volume': market_data.get('total_volume', {}).get('usd'),
                'price_change_24h': market_data.get('price_change_24h'),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
                'price_change_percentage_7d': market_data.get('price_change_percentage_7d'),
                'price_change_percentage_30d': market_data.get('price_change_percentage_30d'),
                'market_cap_rank': market_data.get('market_cap_rank'),
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply'),
                'ath': market_data.get('ath', {}).get('usd'),
                'atl': market_data.get('atl', {}).get('usd'),
                'last_updated': market_data.get('last_updated')
            }
            
            logger.info(f"成功获取 {symbol} 的市场数据")
            return result
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            raise
    
    def get_supported_coins(self) -> List[str]:
        """获取支持的数字货币列表"""
        return list(self.crypto_map.keys())
    
    def rate_limit_delay(self):
        """API请求限流延迟"""
        time.sleep(1.1)  # CoinGecko免费API限制每秒1次请求


if __name__ == "__main__":
    # 测试数据获取功能
    fetcher = CryptoDataFetcher()
    
    # 测试获取BTC价格数据
    try:
        btc_data = fetcher.get_price_data('BTC', days=7)
        print("BTC 7天价格数据:")
        print(btc_data.head())
        print(f"数据形状: {btc_data.shape}")
        
        # 测试获取当前价格
        current_prices = fetcher.get_current_price(['BTC', 'ETH', 'SOL'])
        print("\n当前价格:")
        for symbol, data in current_prices.items():
            print(f"{symbol}: ${data.get('usd', 'N/A')}")
            
    except Exception as e:
        print(f"测试失败: {e}")
