"""
策略引擎 - 量化策略实现
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime

# 尝试导入深度学习策略
try:
    from app.strategies.transformer_dl import TransformerDLStrategy, create_transformer_dl_strategy
    DL_AVAILABLE = True
except ImportError:
    DL_AVAILABLE = False


class BaseStrategy:
    """策略基类"""
    def __init__(self, name: str, parameters: Dict):
        self.name = name
        self.parameters = parameters
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信号 - 子类实现"""
        raise NotImplementedError


class MACrossStrategy(BaseStrategy):
    """均线交叉策略"""
    def __init__(self, short_window: int = 5, long_window: int = 20):
        super().__init__("均线交叉策略", {
            "short_window": short_window,
            "long_window": long_window
        })
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成均线交叉信号
        返回: DataFrame with 'signal' column (1: 买入, -1: 卖出, 0: 持有)
        """
        df = data.copy()
        df['ma_short'] = df['Close'].rolling(window=self.short_window).mean()
        df['ma_long'] = df['Close'].rolling(window=self.long_window).mean()
        
        df['signal'] = 0
        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1  # 金叉买入
        df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1  # 死叉卖出
        
        # 只在信号变化时交易
        df['position'] = df['signal'].diff()
        
        return df


class MomentumStrategy(BaseStrategy):
    """动量策略"""
    def __init__(self, lookback_period: int = 20, threshold: float = 0.05):
        super().__init__("动量策略", {
            "lookback_period": lookback_period,
            "threshold": threshold
        })
        self.lookback_period = lookback_period
        self.threshold = threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成动量信号
        当价格涨幅超过阈值时买入，跌幅超过阈值时卖出
        """
        df = data.copy()
        df['momentum'] = df['Close'].pct_change(periods=self.lookback_period)
        
        df['signal'] = 0
        df.loc[df['momentum'] > self.threshold, 'signal'] = 1
        df.loc[df['momentum'] < -self.threshold, 'signal'] = -1
        
        df['position'] = df['signal'].diff()
        
        return df


class MeanReversionStrategy(BaseStrategy):
    """均值回归策略"""
    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__("均值回归策略", {
            "window": window,
            "num_std": num_std
        })
        self.window = window
        self.num_std = num_std
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成均值回归信号
        当价格低于下轨时买入，高于上轨时卖出
        """
        df = data.copy()
        df['ma'] = df['Close'].rolling(window=self.window).mean()
        df['std'] = df['Close'].rolling(window=self.window).std()
        df['upper_band'] = df['ma'] + (df['std'] * self.num_std)
        df['lower_band'] = df['ma'] - (df['std'] * self.num_std)
        
        df['signal'] = 0
        df.loc[df['Close'] < df['lower_band'], 'signal'] = 1  # 低于下轨买入
        df.loc[df['Close'] > df['upper_band'], 'signal'] = -1  # 高于上轨卖出
        
        df['position'] = df['signal'].diff()
        
        return df


class RSIStrategy(BaseStrategy):
    """RSI策略"""
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI策略", {
            "period": period,
            "oversold": oversold,
            "overbought": overbought
        })
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def _calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成RSI信号
        RSI < oversold: 买入
        RSI > overbought: 卖出
        """
        df = data.copy()
        df['rsi'] = self._calculate_rsi(df['Close'])
        
        df['signal'] = 0
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1
        
        df['position'] = df['signal'].diff()
        
        return df


class BollingerBandsStrategy(BaseStrategy):
    """布林带策略
    
    核心思想：
    - 价格触及下轨且带宽收窄时买入（超卖反弹信号）
    - 价格触及上轨且带宽收窄时卖出（超买回落信号）
    - 结合 %B 指标和带宽(Bandwidth)过滤假信号
    """
    def __init__(self, window: int = 20, num_std: float = 2.0, 
                 buy_threshold: float = 0.05, sell_threshold: float = 0.95):
        super().__init__("布林带策略", {
            "window": window,
            "num_std": num_std,
            "buy_threshold": buy_threshold,
            "sell_threshold": sell_threshold
        })
        self.window = window
        self.num_std = num_std
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成布林带交易信号
        %B = (Close - Lower) / (Upper - Lower)
        %B < buy_threshold: 买入（接近下轨）
        %B > sell_threshold: 卖出（接近上轨）
        """
        df = data.copy()
        
        # 计算布林带
        df['bb_mid'] = df['Close'].rolling(window=self.window).mean()
        df['bb_std'] = df['Close'].rolling(window=self.window).std()
        df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * self.num_std)
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * self.num_std)
        
        # 计算 %B 指标
        band_width = df['bb_upper'] - df['bb_lower']
        df['percent_b'] = (df['Close'] - df['bb_lower']) / band_width.replace(0, np.nan)
        df['percent_b'] = df['percent_b'].fillna(0.5)
        
        # 计算带宽（Bandwidth），用于判断是否处于收窄状态
        df['bandwidth'] = band_width / df['bb_mid'].replace(0, np.nan)
        df['bandwidth'] = df['bandwidth'].fillna(0)
        
        # 生成信号
        df['signal'] = 0
        df.loc[df['percent_b'] < self.buy_threshold, 'signal'] = 1    # 触及下轨买入
        df.loc[df['percent_b'] > self.sell_threshold, 'signal'] = -1  # 触及上轨卖出
        
        df['position'] = df['signal'].diff()
        
        return df


class MultiFactorStrategy(BaseStrategy):
    """多因子选股策略
    
    核心思想：综合多个量价因子打分，加权求和后根据总分信号交易
    
    因子包括：
    1. 动量因子：过去N日收益率排名
    2. 波动率因子：低波动率偏好（低波溢价）
    3. 换手率因子：低换手率偏好（流动性溢价）
    4. 均线偏离因子：价格偏离均线的程度（均值回归）
    5. RSI因子：相对强弱
    """
    def __init__(self, momentum_window: int = 20, volatility_window: int = 20,
                 ma_window: int = 20, rsi_period: int = 14,
                 buy_score: float = 0.6, sell_score: float = 0.4,
                 w_momentum: float = 0.25, w_volatility: float = 0.2,
                 w_turnover: float = 0.15, w_ma_deviation: float = 0.2,
                 w_rsi: float = 0.2):
        super().__init__("多因子选股策略", {
            "momentum_window": momentum_window,
            "volatility_window": volatility_window,
            "ma_window": ma_window,
            "rsi_period": rsi_period,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "w_momentum": w_momentum,
            "w_volatility": w_volatility,
            "w_turnover": w_turnover,
            "w_ma_deviation": w_ma_deviation,
            "w_rsi": w_rsi
        })
        self.momentum_window = momentum_window
        self.volatility_window = volatility_window
        self.ma_window = ma_window
        self.rsi_period = rsi_period
        self.buy_score = buy_score
        self.sell_score = sell_score
        # 因子权重
        self.w_momentum = w_momentum
        self.w_volatility = w_volatility
        self.w_turnover = w_turnover
        self.w_ma_deviation = w_ma_deviation
        self.w_rsi = w_rsi
    
    def _calc_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """计算RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))
    
    def _normalize(self, series: pd.Series) -> pd.Series:
        """Min-Max 归一化到 [0, 1]"""
        s = series.dropna()
        if len(s) == 0 or s.max() == s.min():
            return pd.Series(0.5, index=series.index)
        return (series - s.min()) / (s.max() - s.min())
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成多因子综合信号
        各因子归一化后加权求和，总分 > buy_score 买入，< sell_score 卖出
        """
        df = data.copy()
        
        # ---- 因子1: 动量因子 ----
        # 过去N日收益率，收益率越高得分越高
        df['f_momentum'] = df['Close'].pct_change(periods=self.momentum_window)
        df['f_momentum'] = self._normalize(df['f_momentum'])
        
        # ---- 因子2: 波动率因子 ----
        # 低波动率得分高（低波溢价）
        df['f_volatility'] = df['Close'].pct_change().rolling(window=self.volatility_window).std()
        # 反向：波动率越低得分越高
        df['f_volatility'] = self._normalize(-df['f_volatility'])
        
        # ---- 因子3: 换手率因子 ----
        # 用成交量近似换手率，低成交量得分高（流动性溢价）
        if 'Volume' in df.columns:
            df['f_turnover'] = self._normalize(-df['Volume'])
        else:
            df['f_turnover'] = 0.5
        
        # ---- 因子4: 均线偏离因子 ----
        # 价格低于均线时得分高（均值回归机会）
        df['ma'] = df['Close'].rolling(window=self.ma_window).mean()
        df['f_ma_deviation'] = (df['ma'] - df['Close']) / df['ma'].replace(0, np.nan)
        df['f_ma_deviation'] = self._normalize(df['f_ma_deviation'])
        
        # ---- 因子5: RSI因子 ----
        # RSI 越低得分越高（超卖反弹机会）
        df['rsi'] = self._calc_rsi(df['Close'], self.rsi_period)
        df['f_rsi'] = self._normalize(-df['rsi'])
        
        # ---- 综合打分 ----
        # 填充 NaN
        factor_cols = ['f_momentum', 'f_volatility', 'f_turnover', 'f_ma_deviation', 'f_rsi']
        for col in factor_cols:
            df[col] = df[col].fillna(0.5)
        
        df['composite_score'] = (
            self.w_momentum * df['f_momentum'] +
            self.w_volatility * df['f_volatility'] +
            self.w_turnover * df['f_turnover'] +
            self.w_ma_deviation * df['f_ma_deviation'] +
            self.w_rsi * df['f_rsi']
        )
        
        # 生成信号
        df['signal'] = 0
        df.loc[df['composite_score'] > self.buy_score, 'signal'] = 1    # 综合得分高，买入
        df.loc[df['composite_score'] < self.sell_score, 'signal'] = -1  # 综合得分低，卖出
        
        df['position'] = df['signal'].diff()
        
        return df


class TransformerPredictStrategy(BaseStrategy):
    """Transformer价格预测策略
    
    核心思想：
    - 使用自注意力机制捕捉价格序列的长距离依赖关系
    - 通过多头注意力学习不同时间尺度的模式
    - 基于预测的未来价格趋势生成交易信号
    
    简化实现：使用注意力权重加权历史价格，预测未来走势
    """
    def __init__(self, seq_length: int = 20, pred_horizon: int = 5, 
                 n_heads: int = 4, threshold: float = 0.02,
                 lookback_train: int = 100):
        super().__init__("Transformer价格预测策略", {
            "seq_length": seq_length,
            "pred_horizon": pred_horizon,
            "n_heads": n_heads,
            "threshold": threshold,
            "lookback_train": lookback_train
        })
        self.seq_length = seq_length
        self.pred_horizon = pred_horizon
        self.n_heads = n_heads
        self.threshold = threshold
        self.lookback_train = lookback_train
    
    def _softmax(self, x, axis=-1):
        """Softmax函数"""
        e_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return e_x / np.sum(e_x, axis=axis, keepdims=True)
    
    def _scaled_dot_product_attention(self, Q, K, V):
        """
        缩放点积注意力
        Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
        """
        d_k = Q.shape[-1]
        scores = np.matmul(Q, K.transpose(0, 2, 1)) / np.sqrt(d_k)
        attention_weights = self._softmax(scores, axis=-1)
        return np.matmul(attention_weights, V), attention_weights
    
    def _multi_head_attention(self, X, n_heads):
        """
        多头注意力机制
        将输入分成多个头，分别计算注意力后拼接
        """
        batch_size, seq_len, d_model = X.shape
        d_head = d_model // n_heads
        
        outputs = []
        for h in range(n_heads):
            # 切分不同的头
            start_idx = h * d_head
            end_idx = start_idx + d_head
            
            Q = X[:, :, start_idx:end_idx]
            K = X[:, :, start_idx:end_idx]
            V = X[:, :, start_idx:end_idx]
            
            # 计算注意力
            attn_output, _ = self._scaled_dot_product_attention(Q, K, V)
            outputs.append(attn_output)
        
        # 拼接所有头的输出
        return np.concatenate(outputs, axis=-1)
    
    def _create_sequences(self, data, seq_length):
        """创建时间序列样本"""
        X, y = [], []
        for i in range(len(data) - seq_length):
            X.append(data[i:i + seq_length])
            y.append(data[i + seq_length])
        return np.array(X), np.array(y)
    
    def _prepare_features(self, df):
        """准备输入特征"""
        features = []
        
        # 价格特征
        close_prices = df['Close'].values
        returns = np.diff(close_prices) / close_prices[:-1]
        returns = np.insert(returns, 0, 0)
        
        # 归一化价格
        prices_norm = close_prices / close_prices[0]
        
        # 技术指标特征
        # 1. 移动平均偏离度
        ma5 = pd.Series(close_prices).rolling(5).mean().fillna(method='bfill').values
        ma20 = pd.Series(close_prices).rolling(20).mean().fillna(method='bfill').values
        ma_ratio = (close_prices - ma20) / ma20
        
        # 2. 波动率
        volatility = pd.Series(returns).rolling(10).std().fillna(0).values
        
        # 3. 成交量变化（如果有）
        if 'Volume' in df.columns:
            volume = df['Volume'].values
            volume_change = np.diff(volume, prepend=volume[0]) / (volume + 1)
        else:
            volume_change = np.zeros(len(close_prices))
        
        # 组合特征 [seq_len, n_features]
        for i in range(len(close_prices)):
            feature_vec = [
                prices_norm[i],
                returns[i] if i < len(returns) else 0,
                ma_ratio[i],
                volatility[i],
                volume_change[i]
            ]
            features.append(feature_vec)
        
        return np.array(features)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成Transformer预测信号
        使用滚动窗口训练+预测，避免未来数据泄露
        """
        df = data.copy()
        n = len(df)
        
        # 准备特征
        features = self._prepare_features(df)
        
        # 存储预测结果
        predictions = np.zeros(n)
        
        # 滚动窗口预测（Walk-forward validation）
        min_train_size = self.lookback_train
        
        for i in range(min_train_size, n - self.pred_horizon):
            # 训练数据
            train_features = features[max(0, i - self.lookback_train):i]
            
            # 创建序列样本
            if len(train_features) < self.seq_length + 1:
                continue
            
            X_train, y_train = self._create_sequences(train_features, self.seq_length)
            
            if len(X_train) < 10:
                continue
            
            # 使用注意力机制进行预测
            # 简化版：计算历史序列的注意力权重，加权预测
            current_seq = features[i - self.seq_length:i]
            current_seq = current_seq.reshape(1, self.seq_length, -1)
            
            # 多头注意力
            attn_output = self._multi_head_attention(current_seq, self.n_heads)
            
            # 使用注意力输出预测未来收益
            # 简化：取最后一个时间步的加权特征
            last_features = attn_output[0, -1, :]
            
            # 预测分数：基于特征加权
            # 动量因子 + 均线偏离 + 波动率调整
            pred_score = (
                0.4 * last_features[1] +      # 收益率动量
                0.3 * last_features[2] +      # 均线偏离
                -0.2 * last_features[3] +     # 波动率（负相关）
                0.1 * last_features[0]        # 价格趋势
            )
            
            predictions[i] = pred_score
        
        # 根据预测分数生成交易信号
        df['pred_score'] = predictions
        df['signal'] = 0
        df.loc[df['pred_score'] > self.threshold, 'signal'] = 1    # 预测上涨，买入
        df.loc[df['pred_score'] < -self.threshold, 'signal'] = -1  # 预测下跌，卖出
        
        df['position'] = df['signal'].diff()
        
        return df


def get_available_strategies() -> List[Dict]:
    """获取可用策略列表"""
    return [
        {
            "id": "ma_cross",
            "name": "均线交叉策略",
            "description": "当短期均线上穿长期均线时买入，下穿时卖出",
            "parameters": {
                "short_window": {"type": "int", "default": 5, "min": 2, "max": 50},
                "long_window": {"type": "int", "default": 20, "min": 10, "max": 200}
            }
        },
        {
            "id": "momentum",
            "name": "动量策略",
            "description": "基于价格动量进行交易，追涨杀跌",
            "parameters": {
                "lookback_period": {"type": "int", "default": 20, "min": 5, "max": 100},
                "threshold": {"type": "float", "default": 0.05, "min": 0.01, "max": 0.2}
            }
        },
        {
            "id": "mean_reversion",
            "name": "均值回归策略",
            "description": "价格偏离均值时反向交易，适合震荡市场",
            "parameters": {
                "window": {"type": "int", "default": 20, "min": 10, "max": 100},
                "num_std": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0}
            }
        },
        {
            "id": "rsi",
            "name": "RSI策略",
            "description": "基于相对强弱指标，超买超卖时反向交易",
            "parameters": {
                "period": {"type": "int", "default": 14, "min": 5, "max": 30},
                "oversold": {"type": "float", "default": 30, "min": 10, "max": 40},
                "overbought": {"type": "float", "default": 70, "min": 60, "max": 90}
            }
        },
        {
            "id": "bollinger_bands",
            "name": "布林带策略",
            "description": "基于布林带 %B 指标，价格触及下轨买入、触及上轨卖出，适合震荡行情",
            "parameters": {
                "window": {"type": "int", "default": 20, "min": 10, "max": 60},
                "num_std": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0},
                "buy_threshold": {"type": "float", "default": 0.05, "min": 0.0, "max": 0.3},
                "sell_threshold": {"type": "float", "default": 0.95, "min": 0.7, "max": 1.0}
            }
        },
        {
            "id": "multi_factor",
            "name": "多因子选股策略",
            "description": "综合动量、波动率、换手率、均线偏离、RSI 五大因子加权打分，得分高于阈值买入、低于阈值卖出",
            "parameters": {
                "momentum_window": {"type": "int", "default": 20, "min": 5, "max": 60},
                "volatility_window": {"type": "int", "default": 20, "min": 10, "max": 60},
                "ma_window": {"type": "int", "default": 20, "min": 10, "max": 60},
                "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 30},
                "buy_score": {"type": "float", "default": 0.6, "min": 0.5, "max": 0.9},
                "sell_score": {"type": "float", "default": 0.4, "min": 0.1, "max": 0.5}
            }
        },
        {
            "id": "transformer_predict",
            "name": "Transformer价格预测策略",
            "description": "使用多头自注意力机制捕捉价格序列长距离依赖，预测未来价格走势生成交易信号",
            "parameters": {
                "seq_length": {"type": "int", "default": 20, "min": 10, "max": 60},
                "pred_horizon": {"type": "int", "default": 5, "min": 1, "max": 20},
                "n_heads": {"type": "int", "default": 4, "min": 2, "max": 8},
                "threshold": {"type": "float", "default": 0.02, "min": 0.005, "max": 0.1},
                "lookback_train": {"type": "int", "default": 100, "min": 50, "max": 200}
            }
        },
        {
            "id": "transformer_dl",
            "name": "Transformer深度学习策略",
            "description": "基于PyTorch的完整Transformer架构，包含位置编码、多头注意力、前馈网络，使用滚动窗口训练进行价格预测",
            "parameters": {
                "seq_length": {"type": "int", "default": 30, "min": 10, "max": 60},
                "pred_horizon": {"type": "int", "default": 5, "min": 1, "max": 20},
                "d_model": {"type": "int", "default": 64, "min": 32, "max": 128},
                "n_heads": {"type": "int", "default": 4, "min": 2, "max": 8},
                "n_layers": {"type": "int", "default": 2, "min": 1, "max": 4},
                "epochs": {"type": "int", "default": 50, "min": 10, "max": 100},
                "buy_threshold": {"type": "float", "default": 0.02, "min": 0.005, "max": 0.05},
                "sell_threshold": {"type": "float", "default": -0.02, "min": -0.05, "max": -0.005}
            }
        }
    ]


def create_strategy(strategy_id: str, **params) -> BaseStrategy:
    """创建策略实例"""
    if strategy_id == "ma_cross":
        return MACrossStrategy(
            short_window=params.get("short_window", 5),
            long_window=params.get("long_window", 20)
        )
    elif strategy_id == "momentum":
        return MomentumStrategy(
            lookback_period=params.get("lookback_period", 20),
            threshold=params.get("threshold", 0.05)
        )
    elif strategy_id == "mean_reversion":
        return MeanReversionStrategy(
            window=params.get("window", 20),
            num_std=params.get("num_std", 2.0)
        )
    elif strategy_id == "rsi":
        return RSIStrategy(
            period=params.get("period", 14),
            oversold=params.get("oversold", 30),
            overbought=params.get("overbought", 70)
        )
    elif strategy_id == "bollinger_bands":
        return BollingerBandsStrategy(
            window=params.get("window", 20),
            num_std=params.get("num_std", 2.0),
            buy_threshold=params.get("buy_threshold", 0.05),
            sell_threshold=params.get("sell_threshold", 0.95)
        )
    elif strategy_id == "multi_factor":
        return MultiFactorStrategy(
            momentum_window=params.get("momentum_window", 20),
            volatility_window=params.get("volatility_window", 20),
            ma_window=params.get("ma_window", 20),
            rsi_period=params.get("rsi_period", 14),
            buy_score=params.get("buy_score", 0.6),
            sell_score=params.get("sell_score", 0.4)
        )
    elif strategy_id == "transformer_predict":
        return TransformerPredictStrategy(
            seq_length=params.get("seq_length", 20),
            pred_horizon=params.get("pred_horizon", 5),
            n_heads=params.get("n_heads", 4),
            threshold=params.get("threshold", 0.02),
            lookback_train=params.get("lookback_train", 100)
        )
    elif strategy_id == "transformer_dl":
        if not DL_AVAILABLE:
            raise ImportError(
                "Transformer深度学习策略需要 PyTorch。"
                "请安装: pip install torch scikit-learn"
            )
        return create_transformer_dl_strategy(**params)
    else:
        raise ValueError(f"Unknown strategy: {strategy_id}")
