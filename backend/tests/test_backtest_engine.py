"""
回测引擎测试 — 覆盖回测运行、交易提取、绩效指标的核心路径
"""
import pytest
import pandas as pd
import numpy as np

from app.backtest.engine import BacktestEngine
from app.strategies.engine import MACrossStrategy, RSIStrategy


# ────────────────────────────────────────────
# 回测运行 — 基本结构
# ────────────────────────────────────────────

class TestBacktestRun:
    """测试 BacktestEngine.run() 返回结构"""

    def _run_backtest(self, data, initial_capital=100000.0):
        strategy = MACrossStrategy(short_window=5, long_window=20)
        signals = strategy.generate_signals(data)
        engine = BacktestEngine(initial_capital=initial_capital)
        return engine.run(data, signals)

    def test_result_has_required_keys(self, sample_ohlcv):
        result = self._run_backtest(sample_ohlcv)
        assert "metrics" in result
        assert "trades" in result
        assert "equity_curve" in result
        assert "signals_data" in result

    def test_equity_curve_is_list_of_dicts(self, sample_ohlcv):
        result = self._run_backtest(sample_ohlcv)
        assert isinstance(result["equity_curve"], list)
        assert len(result["equity_curve"]) > 0
        first = result["equity_curve"][0]
        assert "Date" in first
        assert "equity" in first
        assert "Close" in first
        assert "signal" in first

    def test_signals_data_is_list_of_dicts(self, sample_ohlcv):
        result = self._run_backtest(sample_ohlcv)
        assert isinstance(result["signals_data"], list)
        first = result["signals_data"][0]
        assert "Date" in first
        assert "signal" in first
        assert "position_change" in first


# ────────────────────────────────────────────
# 绩效指标
# ────────────────────────────────────────────

class TestMetrics:
    """测试回测绩效指标计算"""

    def _get_metrics(self, data, initial_capital=100000.0):
        strategy = MACrossStrategy(short_window=5, long_window=20)
        signals = strategy.generate_signals(data)
        engine = BacktestEngine(initial_capital=initial_capital)
        result = engine.run(data, signals)
        return result["metrics"]

    def test_metrics_has_required_fields(self, sample_ohlcv):
        required = {
            "initial_capital", "final_value", "total_return",
            "annual_return", "max_drawdown", "sharpe_ratio",
            "win_rate", "total_trades", "winning_trades",
            "losing_trades", "profit_loss_ratio",
        }
        metrics = self._get_metrics(sample_ohlcv)
        assert required.issubset(metrics.keys())

    def test_initial_capital_matches(self, sample_ohlcv):
        metrics = self._get_metrics(sample_ohlcv, initial_capital=200000.0)
        assert metrics["initial_capital"] == 200000.0

    def test_no_nan_or_inf_in_metrics(self, sample_ohlcv):
        """所有指标应为有限浮点数，不含 NaN / Inf"""
        metrics = self._get_metrics(sample_ohlcv)
        for key, value in metrics.items():
            if isinstance(value, float):
                assert not np.isnan(value), f"{key} is NaN"
                assert not np.isinf(value), f"{key} is Inf"

    def test_max_drawdown_non_positive(self, sample_ohlcv):
        """最大回撤应为非正数（0 或负值）"""
        metrics = self._get_metrics(sample_ohlcv)
        assert metrics["max_drawdown"] <= 0

    def test_win_rate_in_range(self, sample_ohlcv):
        metrics = self._get_metrics(sample_ohlcv)
        assert 0 <= metrics["win_rate"] <= 100

    def test_trade_counts_consistent(self, sample_ohlcv):
        metrics = self._get_metrics(sample_ohlcv)
        assert metrics["total_trades"] == metrics["winning_trades"] + metrics["losing_trades"]


# ────────────────────────────────────────────
# 交易记录
# ────────────────────────────────────────────

class TestTrades:
    """测试交易记录提取"""

    def _get_trades(self, data):
        strategy = MACrossStrategy(short_window=5, long_window=20)
        signals = strategy.generate_signals(data)
        engine = BacktestEngine()
        result = engine.run(data, signals)
        return result["trades"]

    def test_trades_are_list(self, sample_ohlcv):
        trades = self._get_trades(sample_ohlcv)
        assert isinstance(trades, list)

    def test_trade_structure(self, sample_ohlcv):
        trades = self._get_trades(sample_ohlcv)
        if len(trades) == 0:
            pytest.skip("该数据集未产生交易")
        required_keys = {"entry_date", "exit_date", "entry_price", "exit_price", "pnl", "pnl_pct", "direction"}
        for trade in trades:
            assert required_keys.issubset(trade.keys())

    def test_trade_dates_are_strings(self, sample_ohlcv):
        trades = self._get_trades(sample_ohlcv)
        for trade in trades:
            assert isinstance(trade["entry_date"], str)
            assert isinstance(trade["exit_date"], str)


# ────────────────────────────────────────────
# 不同策略集成
# ────────────────────────────────────────────

class TestMultiStrategyIntegration:
    """确保不同策略都能跑通回测引擎"""

    @pytest.mark.parametrize("StrategyClass,kwargs", [
        (MACrossStrategy, {"short_window": 5, "long_window": 20}),
        (RSIStrategy, {"period": 14, "oversold": 30, "overbought": 70}),
    ])
    def test_strategy_backtest_runs(self, sample_ohlcv, StrategyClass, kwargs):
        strategy = StrategyClass(**kwargs)
        signals = strategy.generate_signals(sample_ohlcv)
        engine = BacktestEngine()
        result = engine.run(sample_ohlcv, signals)
        assert "metrics" in result
        assert "equity_curve" in result


# ────────────────────────────────────────────
# JSON 序列化安全
# ────────────────────────────────────────────

class TestJSONSafety:
    """确保回测结果可被 JSON 序列化"""

    def test_equity_curve_dates_are_strings(self, sample_ohlcv):
        strategy = MACrossStrategy()
        signals = strategy.generate_signals(sample_ohlcv)
        engine = BacktestEngine()
        result = engine.run(sample_ohlcv, signals)
        for point in result["equity_curve"]:
            assert isinstance(point["Date"], str)

    def test_equity_curve_values_finite(self, sample_ohlcv):
        strategy = MACrossStrategy()
        signals = strategy.generate_signals(sample_ohlcv)
        engine = BacktestEngine()
        result = engine.run(sample_ohlcv, signals)
        for point in result["equity_curve"]:
            for key in ("equity", "Close", "signal"):
                val = point[key]
                assert not np.isnan(val), f"equity_curve {key} is NaN"
                assert not np.isinf(val), f"equity_curve {key} is Inf"
