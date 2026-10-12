"""
策略引擎测试 — 覆盖策略创建、信号生成的核心路径
"""
import pytest
import pandas as pd
import numpy as np

from app.strategies.engine import (
    BaseStrategy,
    MACrossStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    RSIStrategy,
    BollingerBandsStrategy,
    MultiFactorStrategy,
    TransformerPredictStrategy,
    get_available_strategies,
    create_strategy,
)


# ────────────────────────────────────────────
# 策略注册表 & 工厂函数
# ────────────────────────────────────────────

class TestStrategyRegistry:
    """测试策略注册表和工厂函数"""

    def test_get_available_strategies_returns_list(self):
        strategies = get_available_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) >= 7  # 至少 7 个策略

    def test_each_strategy_has_required_fields(self):
        required_keys = {"id", "name", "description", "parameters"}
        for s in get_available_strategies():
            assert required_keys.issubset(s.keys()), f"策略 {s.get('id')} 缺少必要字段"

    @pytest.mark.parametrize("strategy_id", [
        "ma_cross", "momentum", "mean_reversion", "rsi",
        "bollinger_bands", "multi_factor", "transformer_predict",
    ])
    def test_create_strategy_known_ids(self, strategy_id):
        strategy = create_strategy(strategy_id)
        assert isinstance(strategy, BaseStrategy)
        assert strategy.name  # 名称非空

    def test_create_strategy_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            create_strategy("nonexistent_strategy")


# ────────────────────────────────────────────
# 信号生成通用断言
# ────────────────────────────────────────────

def _assert_signal_schema(df: pd.DataFrame):
    """断言信号 DataFrame 包含必需列且值合法"""
    assert "signal" in df.columns
    assert "position" in df.columns
    # signal 只允许 1, -1, 0
    unique_signals = set(df["signal"].unique())
    assert unique_signals.issubset({-1, 0, 1}), f"非法信号值: {unique_signals - {-1, 0, 1}}"


# ────────────────────────────────────────────
# 各策略信号生成测试
# ────────────────────────────────────────────

class TestMACrossStrategy:
    def test_signal_schema(self, sample_ohlcv):
        strategy = MACrossStrategy(short_window=5, long_window=20)
        result = strategy.generate_signals(sample_ohlcv)
        _assert_signal_schema(result)

    def test_default_parameters(self):
        strategy = MACrossStrategy()
        assert strategy.short_window == 5
        assert strategy.long_window == 20

    def test_signal_has_intermediate_columns(self, sample_ohlcv):
        result = MACrossStrategy().generate_signals(sample_ohlcv)
        assert "ma_short" in result.columns
        assert "ma_long" in result.columns


class TestMomentumStrategy:
    def test_signal_schema(self, sample_ohlcv):
        strategy = MomentumStrategy(lookback_period=10, threshold=0.03)
        result = strategy.generate_signals(sample_ohlcv)
        _assert_signal_schema(result)

    def test_momentum_column_exists(self, sample_ohlcv):
        result = MomentumStrategy().generate_signals(sample_ohlcv)
        assert "momentum" in result.columns


class TestMeanReversionStrategy:
    def test_signal_schema(self, sample_ohlcv):
        strategy = MeanReversionStrategy(window=15, num_std=2.0)
        result = strategy.generate_signals(sample_ohlcv)
        _assert_signal_schema(result)

    def test_band_columns(self, sample_ohlcv):
        result = MeanReversionStrategy().generate_signals(sample_ohlcv)
        assert "upper_band" in result.columns
        assert "lower_band" in result.columns


class TestRSIStrategy:
    def test_signal_schema(self, sample_ohlcv):
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        result = strategy.generate_signals(sample_ohlcv)
        _assert_signal_schema(result)

    def test_rsi_range(self, sample_ohlcv):
        """RSI 值应在 0-100 之间"""
        result = RSIStrategy().generate_signals(sample_ohlcv)
        valid_rsi = result["rsi"].dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


class TestBollingerBandsStrategy:
    def test_signal_schema(self, sample_ohlcv):
        strategy = BollingerBandsStrategy()
        result = strategy.generate_signals(sample_ohlcv)
        _assert_signal_schema(result)

    def test_percent_b_column(self, sample_ohlcv):
        result = BollingerBandsStrategy().generate_signals(sample_ohlcv)
        assert "percent_b" in result.columns


class TestMultiFactorStrategy:
    def test_signal_schema(self, sample_ohlcv):
        strategy = MultiFactorStrategy()
        result = strategy.generate_signals(sample_ohlcv)
        _assert_signal_schema(result)

    def test_composite_score_column(self, sample_ohlcv):
        result = MultiFactorStrategy().generate_signals(sample_ohlcv)
        assert "composite_score" in result.columns


class TestTransformerPredictStrategy:
    def test_signal_schema(self, sample_ohlcv):
        """Transformer 预测策略需要较长数据，使用 100 天数据"""
        strategy = TransformerPredictStrategy(
            seq_length=10, pred_horizon=3, lookback_train=30
        )
        result = strategy.generate_signals(sample_ohlcv)
        _assert_signal_schema(result)

    def test_pred_score_column(self, sample_ohlcv):
        strategy = TransformerPredictStrategy(
            seq_length=10, pred_horizon=3, lookback_train=30
        )
        result = strategy.generate_signals(sample_ohlcv)
        assert "pred_score" in result.columns


# ────────────────────────────────────────────
# 边界条件
# ────────────────────────────────────────────

class TestEdgeCases:
    def test_strategy_with_minimal_data(self, small_ohlcv):
        """短数据不应导致崩溃"""
        strategy = MACrossStrategy(short_window=3, long_window=10)
        result = strategy.generate_signals(small_ohlcv)
        _assert_signal_schema(result)
        assert len(result) == len(small_ohlcv)

    def test_position_is_signal_diff(self, sample_ohlcv):
        """position 列应为 signal 的一阶差分"""
        result = MACrossStrategy().generate_signals(sample_ohlcv)
        expected_pos = result["signal"].diff()
        pd.testing.assert_series_equal(
            result["position"], expected_pos, check_names=False
        )

    def test_does_not_mutate_input(self, sample_ohlcv):
        """策略不应修改原始输入 DataFrame"""
        original_cols = set(sample_ohlcv.columns)
        _ = MACrossStrategy().generate_signals(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols
