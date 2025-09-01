"""
数据获取模块
使用CoinGecko API获取数字货币行情数据
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
