"""
深度学习 Transformer 价格预测策略

基于 PyTorch 实现的完整 Transformer 架构：
- 位置编码 (Positional Encoding)
- 多头自注意力 (Multi-Head Self-Attention)
- 前馈神经网络 (Feed-Forward Network)
- 层归一化 (Layer Normalization)
- 滚动窗口训练 (Walk-forward Validation)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ============== 特征工程（无 PyTorch 依赖）==============

class FeatureEngineer:
    """特征工程类"""
    
    @staticmethod
    def create_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        创建输入特征和目标变量
        
        特征: 收益率、对数收益率、均线偏离度、波动率、成交量变化、RSI、MACD、布林带位置、动量
        目标: 未来N日收益率
        """
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values
        
        if 'Volume' in df.columns:
            volume = df['Volume'].values
        else:
            volume = np.ones(len(close))
        
        n = len(close)
        features = np.zeros((n, 9))
        
        # 1. 收益率
        returns = np.diff(close) / close[:-1]
        returns = np.insert(returns, 0, 0)
        features[:, 0] = returns
        
        # 2. 对数收益率
        log_returns = np.diff(np.log(close))
        log_returns = np.insert(log_returns, 0, 0)
        features[:, 1] = log_returns
        
        # 3. 移动平均偏离度
        ma20 = pd.Series(close).rolling(20).mean().bfill().values
        features[:, 2] = (close - ma20) / ma20
        
        # 4. 波动率 (20日)
        features[:, 3] = pd.Series(returns).rolling(20).std().bfill().values
        
        # 5. 成交量变化
        volume_change = np.diff(volume, prepend=volume[0]) / (volume + 1)
        features[:, 4] = volume_change
        
        # 6. RSI (14日)
        features[:, 5] = FeatureEngineer._calculate_rsi(close, 14)
        
        # 7. MACD
        features[:, 6] = FeatureEngineer._calculate_macd(close)
        
        # 8. 布林带位置
        features[:, 7] = FeatureEngineer._calculate_bb_position(close)
        
        # 9. 价格动量 (10日)
        momentum = np.zeros(n)
        momentum[10:] = (close[10:] - close[:-10]) / close[:-10]
        features[:, 8] = momentum
        
        # 标准化特征
        features = FeatureEngineer._standardize(features)
        
        # 目标: 未来5日收益率
        future_returns = np.zeros(n)
        for i in range(n - 5):
            future_returns[i] = (close[i + 5] - close[i]) / close[i]
        
        return features, future_returns
    
    @staticmethod
    def _calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """计算 RSI"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = pd.Series(gain).rolling(period).mean().bfill().values
        avg_loss = pd.Series(loss).rolling(period).mean().bfill().values
        
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi = np.insert(rsi, 0, 50)
        return rsi / 100
    
    @staticmethod
    def _calculate_macd(prices: np.ndarray) -> np.ndarray:
        """计算 MACD"""
        ema12 = pd.Series(prices).ewm(span=12).mean().values
        ema26 = pd.Series(prices).ewm(span=26).mean().values
        macd = (ema12 - ema26) / prices
        return macd
    
    @staticmethod
    def _calculate_bb_position(prices: np.ndarray, window: int = 20) -> np.ndarray:
        """计算布林带位置 %B"""
        ma = pd.Series(prices).rolling(window).mean().bfill().values
        std = pd.Series(prices).rolling(window).std().bfill().values
        upper = ma + 2 * std
        lower = ma - 2 * std
        bb_pos = (prices - lower) / (upper - lower + 1e-10)
        return np.clip(bb_pos, 0, 1)
    
    @staticmethod
    def _standardize(features: np.ndarray) -> np.ndarray:
        """Z-score 标准化"""
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0) + 1e-8
        return (features - mean) / std


# ============== PyTorch 模型组件（仅在 PyTorch 可用时定义）==============

if TORCH_AVAILABLE:

    class PositionalEncoding(nn.Module):
        """
        位置编码 - 为序列注入位置信息
        
        PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
        PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
        """
        def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
            super().__init__()
            self.dropout = nn.Dropout(p=dropout)
            
            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
            
            pe[:, 0::2] = torch.sin(position * div_term)
            pe[:, 1::2] = torch.cos(position * div_term)
            pe = pe.unsqueeze(0)
            
            self.register_buffer('pe', pe)
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = x + self.pe[:, :x.size(1), :]
            return self.dropout(x)

    class MultiHeadAttention(nn.Module):
        """
        多头自注意力机制
        
        MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
        Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
        """
        def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
            super().__init__()
            assert d_model % n_heads == 0
            
            self.d_model = d_model
            self.n_heads = n_heads
            self.d_k = d_model // n_heads
            
            self.W_q = nn.Linear(d_model, d_model)
            self.W_k = nn.Linear(d_model, d_model)
            self.W_v = nn.Linear(d_model, d_model)
            self.W_o = nn.Linear(d_model, d_model)
            
            self.dropout = nn.Dropout(p=dropout)
            self.layer_norm = nn.LayerNorm(d_model)
        
        def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
            batch_size, seq_len, _ = x.shape
            
            Q = self.W_q(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
            K = self.W_k(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
            V = self.W_v(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
            
            scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.d_k)
            
            if mask is not None:
                scores = scores.masked_fill(mask == 0, -1e9)
            
            attention_weights = torch.softmax(scores, dim=-1)
            attention_weights = self.dropout(attention_weights)
            
            context = torch.matmul(attention_weights, V)
            context = context.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
            
            output = self.W_o(context)
            output = self.dropout(output)
            output = self.layer_norm(output + x)
            
            return output

    class FeedForwardNetwork(nn.Module):
        """
        位置前馈神经网络
        FFN(x) = max(0, x W_1 + b_1) W_2 + b_2
        """
        def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
            super().__init__()
            self.linear1 = nn.Linear(d_model, d_ff)
            self.linear2 = nn.Linear(d_ff, d_model)
            self.dropout = nn.Dropout(p=dropout)
            self.layer_norm = nn.LayerNorm(d_model)
            self.relu = nn.ReLU()
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            residual = x
            x = self.relu(self.linear1(x))
            x = self.dropout(x)
            x = self.linear2(x)
            x = self.dropout(x)
            x = self.layer_norm(x + residual)
            return x

    class TransformerEncoderLayer(nn.Module):
        """Transformer 编码器层 = Multi-Head Attention + FFN"""
        def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1):
            super().__init__()
            self.attention = MultiHeadAttention(d_model, n_heads, dropout)
            self.ffn = FeedForwardNetwork(d_model, d_ff, dropout)
        
        def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
            x = self.attention(x, mask)
            x = self.ffn(x)
            return x

    class StockTransformer(nn.Module):
        """
        股票价格预测 Transformer 模型
        
        架构:
        Input -> Feature Projection -> Positional Encoding 
              -> N x Transformer Encoder Layers
              -> Output Head -> Prediction
        """
        def __init__(
            self,
            input_dim: int = 9,
            d_model: int = 64,
            n_heads: int = 4,
            n_layers: int = 2,
            d_ff: int = 128,
            dropout: float = 0.1,
            pred_horizon: int = 5
        ):
            super().__init__()
            
            self.d_model = d_model
            
            self.input_projection = nn.Linear(input_dim, d_model)
            self.positional_encoding = PositionalEncoding(d_model, dropout=dropout)
            
            self.encoder_layers = nn.ModuleList([
                TransformerEncoderLayer(d_model, n_heads, d_ff, dropout)
                for _ in range(n_layers)
            ])
            
            self.output_head = nn.Sequential(
                nn.Linear(d_model, d_model // 2),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(d_model // 2, pred_horizon)
            )
            
            self._init_weights()
        
        def _init_weights(self):
            for p in self.parameters():
                if p.dim() > 1:
                    nn.init.xavier_uniform_(p)
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = self.input_projection(x)
            x = self.positional_encoding(x)
            
            for encoder_layer in self.encoder_layers:
                x = encoder_layer(x)
            
            x = x[:, -1, :]
            output = self.output_head(x)
            
            return output

    class StockDataset(Dataset):
        """股票时间序列数据集"""
        
        def __init__(self, features: np.ndarray, targets: np.ndarray, seq_length: int):
            self.features = torch.FloatTensor(features)
            self.targets = torch.FloatTensor(targets)
            self.seq_length = seq_length
        
        def __len__(self):
            return len(self.features) - self.seq_length
        
        def __getitem__(self, idx):
            x = self.features[idx:idx + self.seq_length]
            y = self.targets[idx + self.seq_length]
            return x, y

    # ============== 策略类 ==============

    class TransformerDLStrategy:
        """
        深度学习 Transformer 价格预测策略
        
        使用 PyTorch 实现的完整 Transformer 模型进行价格预测
        """
        
        def __init__(
            self,
            seq_length: int = 30,
            pred_horizon: int = 5,
            d_model: int = 64,
            n_heads: int = 4,
            n_layers: int = 2,
            d_ff: int = 128,
            dropout: float = 0.1,
            learning_rate: float = 0.001,
            batch_size: int = 32,
            epochs: int = 50,
            train_window: int = 200,
            buy_threshold: float = 0.02,
            sell_threshold: float = -0.02,
            device: str = 'auto'
        ):
            self.name = "Transformer深度学习策略"
            self.parameters = {
                "seq_length": seq_length,
                "pred_horizon": pred_horizon,
                "d_model": d_model,
                "n_heads": n_heads,
                "n_layers": n_layers,
                "d_ff": d_ff,
                "dropout": dropout,
                "learning_rate": learning_rate,
                "batch_size": batch_size,
                "epochs": epochs,
                "train_window": train_window,
                "buy_threshold": buy_threshold,
                "sell_threshold": sell_threshold
            }
            
            self.seq_length = seq_length
            self.pred_horizon = pred_horizon
            self.d_model = d_model
            self.n_heads = n_heads
            self.n_layers = n_layers
            self.d_ff = d_ff
            self.dropout = dropout
            self.learning_rate = learning_rate
            self.batch_size = batch_size
            self.epochs = epochs
            self.train_window = train_window
            self.buy_threshold = buy_threshold
            self.sell_threshold = sell_threshold
            
            if device == 'auto':
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            else:
                self.device = torch.device(device)
            
            self.input_dim = 9
        
        def _create_model(self) -> StockTransformer:
            return StockTransformer(
                input_dim=self.input_dim,
                d_model=self.d_model,
                n_heads=self.n_heads,
                n_layers=self.n_layers,
                d_ff=self.d_ff,
                dropout=self.dropout,
                pred_horizon=self.pred_horizon
            ).to(self.device)
        
        def _train_model(
            self, 
            model: StockTransformer, 
            features: np.ndarray, 
            targets: np.ndarray,
            train_end: int
        ) -> StockTransformer:
            train_start = max(0, train_end - self.train_window)
            train_features = features[train_start:train_end]
            train_targets = targets[train_start:train_end]
            
            if len(train_features) < self.seq_length + 10:
                return model
            
            dataset = StockDataset(train_features, train_targets, self.seq_length)
            dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
            
            optimizer = optim.Adam(model.parameters(), lr=self.learning_rate, weight_decay=1e-5)
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.epochs)
            criterion = nn.MSELoss()
            
            model.train()
            for epoch in range(self.epochs):
                total_loss = 0
                for batch_x, batch_y in dataloader:
                    batch_x = batch_x.to(self.device)
                    batch_y = batch_y.to(self.device)
                    
                    optimizer.zero_grad()
                    predictions = model(batch_x)
                    loss = criterion(predictions[:, 0], batch_y)
                    loss.backward()
                    
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    total_loss += loss.item()
                
                scheduler.step()
            
            return model
        
        def _predict(self, model: StockTransformer, features: np.ndarray, start_idx: int) -> float:
            model.eval()
            seq = features[start_idx - self.seq_length:start_idx]
            seq_tensor = torch.FloatTensor(seq).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                prediction = model(seq_tensor)
                pred_return = prediction[0, 0].item()
            
            return pred_return
        
        def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
            df = data.copy()
            n = len(df)
            
            features, targets = FeatureEngineer.create_features(df)
            predictions = np.zeros(n)
            
            model = self._create_model()
            
            min_start = self.train_window + self.seq_length
            
            print(f"🚀 开始 Transformer 深度学习回测...")
            print(f"   数据量: {n} 天, 训练窗口: {self.train_window} 天")
            print(f"   设备: {self.device}")
            
            model = self._train_model(model, features, targets, min_start)
            
            retrain_interval = 20
            last_retrain = min_start
            
            for i in range(min_start, n - self.pred_horizon):
                if i - last_retrain >= retrain_interval:
                    model = self._train_model(model, features, targets, i)
                    last_retrain = i
                
                pred_return = self._predict(model, features, i)
                predictions[i] = pred_return
            
            df['pred_return'] = predictions
            df['signal'] = 0
            df.loc[df['pred_return'] > self.buy_threshold, 'signal'] = 1
            df.loc[df['pred_return'] < self.sell_threshold, 'signal'] = -1
            
            df['position'] = df['signal'].diff()
            
            n_trades = (df['position'].abs() > 0).sum()
            print(f"✅ Transformer 深度学习回测完成, 交易信号: {n_trades} 次")
            
            return df


# ============== 工厂函数 ==============

def create_transformer_dl_strategy(**params):
    """创建 Transformer 深度学习策略实例"""
    if not TORCH_AVAILABLE:
        raise ImportError(
            "Transformer深度学习策略需要 PyTorch。"
            "请安装: pip install torch --index-url https://download.pytorch.org/whl/cpu"
        )
    
    return TransformerDLStrategy(
        seq_length=params.get("seq_length", 30),
        pred_horizon=params.get("pred_horizon", 5),
        d_model=params.get("d_model", 64),
        n_heads=params.get("n_heads", 4),
        n_layers=params.get("n_layers", 2),
        d_ff=params.get("d_ff", 128),
        dropout=params.get("dropout", 0.1),
        learning_rate=params.get("learning_rate", 0.001),
        batch_size=params.get("batch_size", 32),
        epochs=params.get("epochs", 50),
        train_window=params.get("train_window", 200),
        buy_threshold=params.get("buy_threshold", 0.02),
        sell_threshold=params.get("sell_threshold", -0.02),
        device=params.get("device", "auto")
    )
