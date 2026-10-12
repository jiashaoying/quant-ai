"""
多数据源管理器
支持：tencent(腾讯财经), yfinance, akshare, baostock, 模拟数据
"""
import pandas as pd
import numpy as np
import requests
from typing import Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class DataSourceManager:
    """数据源管理器"""
    
    @staticmethod
    def get_stock_data(
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y",
        source: str = "auto"
    ) -> tuple:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: 数据周期
            source: 数据源 (auto, tencent, yfinance, akshare, baostock, mock)
            
        Returns:
            tuple: (DataFrame with OHLCV data, actual_source: str)
        """
        # 自动选择数据源
        if source == "auto":
            return DataSourceManager._auto_fetch(symbol, start_date, end_date, period)
        
        # 指定数据源
        if source == "tencent":
            return DataSourceManager._fetch_tencent(symbol, start_date, end_date, period), "tencent"
        elif source == "yfinance":
            return DataSourceManager._fetch_yfinance(symbol, start_date, end_date, period), "yfinance"
        elif source == "akshare":
            return DataSourceManager._fetch_akshare(symbol, start_date, end_date, period), "akshare"
        elif source == "baostock":
            return DataSourceManager._fetch_baostock(symbol, start_date, end_date, period), "baostock"
        elif source == "mock":
            return DataSourceManager._generate_mock_data(symbol, period), "mock"
        else:
            raise ValueError(f"Unknown data source: {source}")
    
    @staticmethod
    def _auto_fetch(
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        period: str
    ) -> tuple:
        """自动选择最佳数据源，返回 (DataFrame, actual_source)"""
        # 判断股票市场
        is_cn_stock = '.SS' in symbol or '.SZ' in symbol or '.BJ' in symbol
        is_hk_stock = '.HK' in symbol
        
        # A股/港股优先使用腾讯财经（内置，无需额外安装）
        if is_cn_stock or is_hk_stock:
            market_name = "A股" if is_cn_stock else "港股"
            print(f"✅ 检测到{market_name}代码: {symbol}，优先使用腾讯财经")
            try:
                data = DataSourceManager._fetch_tencent(symbol, start_date, end_date, period)
                if not data.empty:
                    print(f"✓ 腾讯财经数据获取成功 ({len(data)} 条)")
                    return data, "tencent"
            except Exception as e:
                print(f"腾讯财经获取失败: {e}")
        
        # 尝试 yfinance (美股/港股)
        print(f"尝试使用 YFinance...")
        try:
            data = DataSourceManager._fetch_yfinance(symbol, start_date, end_date, period)
            if not data.empty:
                return data, "yfinance"
        except Exception as e:
            print(f"YFinance 获取失败: {e}")
        
        # 尝试 AKShare (仅A股)
        if is_cn_stock:
            try:
                data = DataSourceManager._fetch_akshare(symbol, start_date, end_date, period)
                if not data.empty:
                    return data, "akshare"
            except Exception as e:
                print(f"AKShare 获取失败: {e}")
        
        # 尝试 BaoStock (仅A股)
        if is_cn_stock:
            try:
                data = DataSourceManager._fetch_baostock(symbol, start_date, end_date, period)
                if not data.empty:
                    return data, "baostock"
            except Exception as e:
                print(f"BaoStock 获取失败: {e}")
        
        # 最后使用模拟数据
        print(f"⚠️  所有数据源失败，使用模拟数据: {symbol}")
        return DataSourceManager._generate_mock_data(symbol, period), "mock"
    
    @staticmethod
    def _fetch_tencent(
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        period: str
    ) -> pd.DataFrame:
        """
        使用腾讯财经API获取股票数据
        
        接口地址: https://web.ifzq.gtimg.cn/appstock/app/fqkline/get
        支持: A股(上证/深证)、港股
        数据格式: [日期, 开盘, 收盘, 最高, 最低, 成交量]
        """
        # 转换股票代码格式
        # 600519.SS -> sh600519, 000858.SZ -> sz000858, 00700.HK -> hk00700
        tencent_symbol = DataSourceManager._convert_to_tencent_symbol(symbol)
        if not tencent_symbol:
            raise ValueError(f"无法转换股票代码: {symbol}")
        
        # 计算日期范围
        if start_date and end_date:
            start = start_date
            end = end_date
        else:
            period_days = {
                "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365,
                "2y": 730, "5y": 1825,
            }
            days = period_days.get(period, 365)
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 计算获取条数（确保足够覆盖日期范围）
        count = max(365, (datetime.strptime(end, '%Y-%m-%d') - datetime.strptime(start, '%Y-%m-%d')).days + 10)
        
        # 构建API URL
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = f"param={tencent_symbol},day,{start},{end},{count},qfq"
        full_url = f"{url}?{params}"
        
        # 发送请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://web.sqt.gtimg.cn/'
        }
        
        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('code') != 0:
            raise Exception(f"腾讯财经API返回错误: {data.get('msg', 'unknown')}")
        
        # 解析数据
        stock_data = data.get('data', {})
        if not stock_data:
            return pd.DataFrame()
        
        # 获取K线数据（尝试不同的key）
        kline_data = None
        for key in ['qfqday', 'day', 'qfqweek', 'qfqmonth']:
            if tencent_symbol in stock_data and key in stock_data[tencent_symbol]:
                kline_data = stock_data[tencent_symbol][key]
                break
        
        if not kline_data:
            return pd.DataFrame()
        
        # 转换为DataFrame
        # 数据格式: [日期, 开盘, 收盘, 最高, 最低, 成交量]
        records = []
        for item in kline_data:
            if len(item) >= 6:
                records.append({
                    'Date': pd.to_datetime(item[0]),
                    'Open': float(item[1]),
                    'Close': float(item[2]),
                    'High': float(item[3]),
                    'Low': float(item[4]),
                    'Volume': float(item[5])
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # 过滤日期范围
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        df = df.reset_index(drop=True)
        
        return df
    
    @staticmethod
    def _convert_to_tencent_symbol(symbol: str) -> Optional[str]:
        """
        转换股票代码为腾讯财经格式
        
        600519.SS -> sh600519  (上证)
        000858.SZ -> sz000858  (深证)
        00700.HK  -> hk00700   (港股)
        """
        symbol = symbol.strip().upper()
        
        if '.SS' in symbol:
            # 上证
            code = symbol.replace('.SS', '')
            return f"sh{code}"
        elif '.SZ' in symbol:
            # 深证
            code = symbol.replace('.SZ', '')
            return f"sz{code}"
        elif '.BJ' in symbol:
            # 北交所
            code = symbol.replace('.BJ', '')
            return f"bj{code}"
        elif '.HK' in symbol:
            # 港股
            code = symbol.replace('.HK', '')
            return f"hk{code}"
        else:
            # 尝试自动判断（纯数字代码可能是A股）
            if symbol.isdigit() and len(symbol) == 6:
                code = symbol
                if code.startswith(('6', '9')):
                    return f"sh{code}"  # 上证
                elif code.startswith(('0', '2', '3')):
                    return f"sz{code}"  # 深证
                elif code.startswith(('4', '8')):
                    return f"bj{code}"  # 北证
        
        return None
    
    @staticmethod
    def _fetch_yfinance(
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        period: str
    ) -> pd.DataFrame:
        """使用 yfinance 获取数据"""
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        
        if start_date and end_date:
            data = ticker.history(start=start_date, end=end_date)
        else:
            data = ticker.history(period=period)
        
        if data.empty:
            return pd.DataFrame()
        
        data = data.reset_index()
        data = data.rename(columns={'Date': 'Date'})
        data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        return data
    
    @staticmethod
    def _fetch_akshare(
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        period: str
    ) -> pd.DataFrame:
        """使用 AKShare 获取A股数据"""
        import akshare as ak
        
        # 转换股票代码格式：600519.SS -> 600519
        pure_symbol = symbol.split('.')[0]
        
        # 计算日期范围
        if start_date and end_date:
            start = start_date.replace('-', '')
            end = end_date.replace('-', '')
        else:
            end = datetime.now().strftime('%Y%m%d')
            period_days = {
                "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365,
                "2y": 730, "5y": 1825,
            }
            days = period_days.get(period, 365)
            start = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        # 获取A股日K线数据
        try:
            df = ak.stock_zh_a_hist(
                symbol=pure_symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'Date',
                '开盘': 'Open',
                '最高': 'High',
                '最低': 'Low',
                '收盘': 'Close',
                '成交量': 'Volume'
            })
            
            # 只保留需要的列
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            # 转换日期格式
            df['Date'] = pd.to_datetime(df['Date'])
            
            return df
            
        except Exception as e:
            print(f"AKShare error: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def _fetch_baostock(
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        period: str
    ) -> pd.DataFrame:
        """使用 BaoStock 获取A股数据"""
        import baostock as bs
        
        # 登录 BaoStock
        lg = bs.login()
        if lg.error_code != '0':
            raise Exception(f"BaoStock login failed: {lg.error_msg}")
        
        try:
            # 转换股票代码格式：600519.SS -> sh.600519, 000858.SZ -> sz.000858
            if '.SS' in symbol:
                bs_symbol = f"sh.{symbol.split('.')[0]}"
            elif '.SZ' in symbol:
                bs_symbol = f"sz.{symbol.split('.')[0]}"
            else:
                bs_symbol = symbol
            
            # 计算日期范围
            if start_date and end_date:
                start = start_date
                end = end_date
            else:
                end = datetime.now().strftime('%Y-%m-%d')
                period_days = {
                    "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365,
                    "2y": 730, "5y": 1825,
                }
                days = period_days.get(period, 365)
                start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # 获取日K线数据
            rs = bs.query_history_k_data_plus(
                bs_symbol,
                "date,open,high,low,close,volume",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="2"  # 前复权
            )
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 转换数据类型
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # 重命名列
            df = df.rename(columns={
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            
            df['Date'] = pd.to_datetime(df['Date'])
            
            return df
            
        finally:
            # 登出 BaoStock
            bs.logout()
    
    @staticmethod
    def _generate_mock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
        """生成模拟股票数据"""
        period_days = {
            "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365,
            "2y": 730, "5y": 1825,
        }
        days = period_days.get(period, 365)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        base_prices = {
            "AAPL": 150, "GOOGL": 2800, "MSFT": 300, "AMZN": 3300, "TSLA": 700,
            "600519": 1800, "000858": 150, "601318": 60, "000001": 3200,
        }
        
        pure_symbol = symbol.split('.')[0]
        base_price = base_prices.get(pure_symbol, 100)
        
        np.random.seed(hash(symbol) % 2**32)
        
        mu = 0.0005
        sigma = 0.02
        returns = np.random.normal(mu, sigma, len(dates))
        
        prices = [base_price]
        for r in returns[1:]:
            new_price = prices[-1] * (1 + r)
            prices.append(new_price)
        
        data = []
        for i, date in enumerate(dates):
            close = prices[i]
            open_price = close * (1 + np.random.uniform(-0.01, 0.01))
            high_price = max(open_price, close) * (1 + np.random.uniform(0, 0.02))
            low_price = min(open_price, close) * (1 - np.random.uniform(0, 0.02))
            volume = np.random.randint(1000000, 10000000)
            
            data.append({
                'Date': date,
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close, 2),
                'Volume': volume
            })
        
        df = pd.DataFrame(data)
        return df
