"""
Market data fetching from Alpha Vantage and Binance.
"""

import requests
import time
import json
import os
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """
    Fetches real market data from APIs to parameterize trading jobs.
    """
    
    def __init__(self, alpha_vantage_key=None, cache_dir='data/'):
        """
        Initialize market data fetcher.
        
        Args:
            alpha_vantage_key: API key for Alpha Vantage
            cache_dir: Directory to cache market data
        """
        self.alpha_vantage_key = alpha_vantage_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def fetch_intraday_data(self, symbol='SPY', interval='1min', use_cache=True):
        """
        Fetch intraday stock data from Alpha Vantage.
        
        Args:
            symbol: Stock ticker symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            use_cache: Use cached data if available
            
        Returns:
            dict: Time series data
        """
        cache_file = f"{self.cache_dir}{symbol}_{interval}.json"
        
        # Check cache first
        if use_cache and os.path.exists(cache_file):
            logger.info(f"Loading cached data for {symbol}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        if not self.alpha_vantage_key:
            logger.warning("No Alpha Vantage API key configured. Using mock data.")
            return self._generate_mock_data(symbol)
        
        # Fetch from API
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': 'full',
            'apikey': self.alpha_vantage_key
        }
        
        try:
            logger.info(f"Fetching {symbol} data from Alpha Vantage...")
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'Time Series (1min)' in data or 'Time Series (5min)' in data:
                # Cache the data
                with open(cache_file, 'w') as f:
                    json.dump(data, f)
                logger.info(f"Cached data for {symbol}")
                return data
            else:
                logger.error(f"API Error: {data.get('Note', data.get('Error Message', 'Unknown'))}")
                return self._generate_mock_data(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return self._generate_mock_data(symbol)
    
    def _generate_mock_data(self, symbol):
        """
        Generate mock market data for testing without API.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            dict: Mock time series data
        """
        import random
        from datetime import datetime, timedelta
        
        logger.info(f"Generating mock data for {symbol}")
        
        data = {}
        base_price = 100.0
        current_time = datetime.now()
        
        # Generate 100 time periods
        for i in range(100):
            timestamp = (current_time - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S')
            price_change = random.uniform(-2, 2)
            price = max(base_price + price_change, 1.0)
            
            data[timestamp] = {
                'open': f"{price:.2f}",
                'high': f"{price + random.uniform(0, 1):.2f}",
                'low': f"{price - random.uniform(0, 1):.2f}",
                'close': f"{price + random.uniform(-0.5, 0.5):.2f}",
                'volume': str(random.randint(1000000, 10000000))
            }
        
        return {'Time Series (1min)': data}
    
    def calculate_volatility(self, symbol='SPY'):
        """
        Calculate recent volatility for a symbol.
        Higher volatility = higher priority for processing.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            float: Volatility measure
        """
        data = self.fetch_intraday_data(symbol)
        
        if not data:
            return 0.01  # Default low volatility
        
        # Get time series key
        ts_key = [k for k in data.keys() if 'Time Series' in k]
        if not ts_key:
            return 0.01
        
        time_series = data[ts_key[0]]
        prices = [float(v['close']) for v in list(time_series.values())[:50]]
        
        if len(prices) < 2:
            return 0.01
        
        # Calculate simple volatility (std dev of returns)
        returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
        volatility = sum([r**2 for r in returns]) / len(returns)
        
        return volatility ** 0.5
    
    def get_tick_count(self, symbol='SPY'):
        """
        Estimate tick count (proxy for market activity).
        
        Args:
            symbol: Stock ticker
            
        Returns:
            int: Estimated tick count
        """
        data = self.fetch_intraday_data(symbol)
        
        if not data:
            return 10000  # Default
        
        ts_key = [k for k in data.keys() if 'Time Series' in k]
        if not ts_key:
            return 10000
        
        time_series = data[ts_key[0]]
        
        # Use volume as proxy for tick count
        volumes = [int(v['volume']) for v in list(time_series.values())[:10]]
        avg_volume = sum(volumes) / len(volumes) if volumes else 10000
        
        # Rough estimate: 1 tick per 100 shares
        return int(avg_volume / 100)
