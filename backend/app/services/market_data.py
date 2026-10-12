"""
市场数据服务 - 获取股票数据
支持多数据源：yfinance, akshare, baostock, 模拟数据
"""
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
from app.services.data_source_manager import DataSourceManager


class MarketDataService:
    """市场数据服务"""
    
    @staticmethod
    def get_stock_data(
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y",
        source: str = "auto"
    ) -> tuple:
        """
        获取股票数据（自动选择最佳数据源）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期
            source: 数据源 (auto, yfinance, akshare, baostock, mock)
            
        Returns:
            tuple: (DataFrame, actual_source)
        """
        return DataSourceManager.get_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            source=source
        )
    
    @staticmethod
    def get_stock_info(symbol: str) -> dict:
        """获取股票基本信息"""
        # 尝试获取真实信息
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if info and 'currentPrice' in info:
                return {
                    "symbol": symbol,
                    "name": info.get("longName", "N/A"),
                    "sector": info.get("sector", "N/A"),
                    "industry": info.get("industry", "N/A"),
                    "market_cap": info.get("marketCap", "N/A"),
                    "current_price": info.get("currentPrice", "N/A"),
                    "currency": info.get("currency", "USD")
                }
        except:
            pass
        
        # 返回模拟信息
        mock_names = {
            "AAPL": "苹果公司 (模拟数据)",
            "GOOGL": "谷歌 (模拟数据)",
            "MSFT": "微软 (模拟数据)",
            "TSLA": "特斯拉 (模拟数据)",
            "600519.SS": "贵州茅台 (模拟数据)",
            "000858.SZ": "五粮液 (模拟数据)",
        }
        
        return {
            "symbol": symbol,
            "name": mock_names.get(symbol, f"{symbol} (模拟数据)"),
            "sector": "N/A",
            "industry": "N/A",
            "market_cap": "N/A",
            "current_price": "N/A",
            "currency": "CNY" if ".SS" in symbol or ".SZ" in symbol else "USD"
        }
    
    @staticmethod
    def search_symbol(keyword: str) -> list:
        """搜索股票代码（简化版本）"""
        common_stocks = {
            "AAPL": "苹果",
            "GOOGL": "谷歌",
            "MSFT": "微软",
            "AMZN": "亚马逊",
            "TSLA": "特斯拉",
            "000001.SS": "上证指数",
            "399001.SZ": "深证成指",
            "600519.SS": "贵州茅台",
            "000858.SZ": "五粮液",
            "601318.SS": "中国平安"
        }
        
        results = []
        for symbol, name in common_stocks.items():
            if keyword.upper() in symbol or keyword in name:
                results.append({"symbol": symbol, "name": name})
        
        return results
