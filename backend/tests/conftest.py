"""
pytest 共享 fixtures
"""
import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_ohlcv():
    """生成 100 天的模拟 OHLCV 数据，用于策略和回测测试"""
    np.random.seed(42)
    n = 100
    dates = pd.date_range(start="2024-01-01", periods=n, freq="B")
    # 模拟一个带趋势的价格序列：基础趋势 + 随机波动
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, n)
    close_prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": close_prices * (1 + np.random.uniform(-0.005, 0.005, n)),
        "High": close_prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
        "Low": close_prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
        "Close": close_prices,
        "Volume": np.random.randint(100000, 1000000, n).astype(float),
    })
    return df


@pytest.fixture
def small_ohlcv():
    """30 天的短数据集，用于快速单元测试"""
    np.random.seed(123)
    n = 30
    dates = pd.date_range(start="2024-01-01", periods=n, freq="B")
    close_prices = 50.0 * np.cumprod(1 + np.random.normal(0.0005, 0.015, n))

    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Open": close_prices * 0.999,
        "High": close_prices * 1.01,
        "Low": close_prices * 0.99,
        "Close": close_prices,
        "Volume": np.random.randint(50000, 500000, n).astype(float),
    })
