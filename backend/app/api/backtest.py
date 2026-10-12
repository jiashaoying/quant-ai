"""
回测API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from app.strategies.engine import create_strategy
from app.backtest.engine import BacktestEngine
from app.services.market_data import MarketDataService

router = APIRouter()


class BacktestRequest(BaseModel):
    """回测请求"""
    strategy_id: str
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: str = "1y"
    initial_capital: float = 100000.0
    source: str = "auto"  # 数据源: auto, tencent, yfinance, akshare, baostock, mock
    parameters: Dict[str, Any] = {}


@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """
    运行策略回测
    """
    try:
        # 1. 获取股票数据
        market_service = MarketDataService()
        data, actual_source = market_service.get_stock_data(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            period=request.period,
            source=request.source
        )
        
        # 2. 创建策略
        strategy = create_strategy(request.strategy_id, **request.parameters)
        
        # 3. 生成交易信号
        signals = strategy.generate_signals(data)
        
        # 4. 运行回测
        engine = BacktestEngine(initial_capital=request.initial_capital)
        result = engine.run(data, signals)
        
        # 5. 添加策略信息
        result["strategy"] = {
            "id": request.strategy_id,
            "name": strategy.name,
            "parameters": strategy.parameters
        }
        
        # 6. 添加股票信息和数据源
        result["symbol"] = request.symbol
        result["data_source"] = actual_source  # 使用实际数据源，而非请求中的数据源
        result["is_mock"] = actual_source == "mock"  # 标识是否为模拟数据
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_backtest_history():
    """获取回测历史（从数据库）"""
    # TODO: 实现从数据库读取历史回测结果
    return {"message": "Not implemented yet"}
