"""
回测引擎
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class BacktestEngine:
    """回测引擎"""
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        
    def run(self, data: pd.DataFrame, signals: pd.DataFrame) -> Dict:
        """
        运行回测
        
        Args:
            data: 股票数据 (Open, High, Low, Close, Volume)
            signals: 交易信号 (signal, position)
            
        Returns:
            回测结果字典
        """
        # 合并数据和信号
        df = data.copy()
        df['signal'] = signals['signal']
        df['position_change'] = signals['position']
        
        # 计算策略收益
        df = df.copy()
        df['market_return'] = df['Close'].pct_change()
        df['strategy_return'] = df['market_return'] * df['signal'].shift(1)
        df.loc[df.index[0], 'strategy_return'] = 0
        
        # 计算累计收益
        df['cumulative_market_return'] = (1 + df['market_return']).cumprod()
        df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()
        
        # 计算资金曲线
        df['equity'] = self.initial_capital * df['cumulative_strategy_return']
        
        # 提取交易记录
        trades = self._extract_trades(df)
        
        # 确保 Date 列为 datetime 类型（兼容字符串和 datetime 输入）
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 计算性能指标
        metrics = self._calculate_metrics(df, trades)
        
        # 准备返回数据
        # 处理日期格式，确保可以JSON序列化
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # 清理所有浮点数，确保没有NaN或Inf
        numeric_columns = ['equity', 'Close', 'signal', 'position_change']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0).replace([np.inf, -np.inf], 0)
        
        result = {
            "metrics": metrics,
            "trades": trades,
            "equity_curve": df[['Date', 'equity', 'Close', 'signal']].to_dict('records'),
            "signals_data": df[['Date', 'Close', 'signal', 'position_change']].to_dict('records')
        }
        
        return result
    
    def _extract_trades(self, df: pd.DataFrame) -> List[Dict]:
        """提取交易记录"""
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        
        for idx, row in df.iterrows():
            if row['position_change'] != 0:
                if row['position_change'] > 0 and position == 0:  # 买入
                    position = 1
                    entry_price = row['Close']
                    entry_date = row['Date']
                elif row['position_change'] < 0 and position == 1:  # 卖出
                    position = 0
                    exit_price = row['Close']
                    exit_date = row['Date']
                    
                    pnl = exit_price - entry_price
                    pnl_pct = pnl / entry_price
                    
                    trades.append({
                        "entry_date": str(entry_date),
                        "exit_date": str(exit_date),
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct * 100, 2),
                        "direction": "long"
                    })
        
        return trades
    
    def _calculate_metrics(self, df: pd.DataFrame, trades: List[Dict]) -> Dict:
        """计算性能指标"""
        # 总收益率
        total_return = (df['equity'].iloc[-1] / self.initial_capital - 1) * 100
        
        # 年化收益率
        days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
        years = days / 365.0
        annual_return = ((df['equity'].iloc[-1] / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # 最大回撤
        df['rolling_max'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['rolling_max']) / df['rolling_max'] * 100
        max_drawdown = df['drawdown'].min()
        
        # 夏普比率 (假设无风险利率为3%)
        risk_free_rate = 0.03
        daily_return = df['strategy_return'].dropna()
        excess_return = daily_return - risk_free_rate / 252
        std = excess_return.std()
        if std != 0 and not np.isnan(std):
            sharpe_ratio = np.sqrt(252) * excess_return.mean() / std
        else:
            sharpe_ratio = 0.0
        
        # 确保所有指标都是有效数字
        sharpe_ratio = 0.0 if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio) else sharpe_ratio
        
        # 胜率
        winning_trades = [t for t in trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        # 盈亏比
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        avg_loss = abs(np.mean([t['pnl_pct'] for t in losing_trades])) if losing_trades else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss != 0 else 0
        
        # 确保所有值都是有效的JSON数字
        def safe_round(value, decimals=2):
            """安全的四舍五入，处理NaN和Inf"""
            if pd.isna(value) or np.isinf(value):
                return 0.0
            return round(float(value), decimals)
        
        return {
            "initial_capital": safe_round(self.initial_capital),
            "final_value": safe_round(df['equity'].iloc[-1]),
            "total_return": safe_round(total_return),
            "annual_return": safe_round(annual_return),
            "max_drawdown": safe_round(max_drawdown),
            "sharpe_ratio": safe_round(sharpe_ratio),
            "win_rate": safe_round(win_rate),
            "total_trades": int(len(trades)),
            "winning_trades": int(len(winning_trades)),
            "losing_trades": int(len(losing_trades)),
            "profit_loss_ratio": safe_round(profit_loss_ratio)
        }
