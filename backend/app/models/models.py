"""
数据库模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    strategy_type = Column(String(50))  # ma_cross, momentum, mean_reversion等
    parameters = Column(JSON)  # 策略参数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BacktestResult(Base):
    """回测结果表"""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, index=True)
    symbol = Column(String(20))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_capital = Column(Float)
    final_value = Column(Float)
    total_return = Column(Float)
    annual_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    trades_data = Column(JSON)  # 交易记录
    equity_curve = Column(JSON)  # 资金曲线
    created_at = Column(DateTime, default=datetime.utcnow)
