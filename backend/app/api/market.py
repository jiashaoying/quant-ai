"""
市场数据API路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.market_data import MarketDataService

router = APIRouter()


@router.get("/stock/{symbol}")
async def get_stock_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "1y"
):
    """获取股票数据"""
    try:
        service = MarketDataService()
        data = service.get_stock_data(symbol, start_date, end_date, period)
        return {
            "symbol": symbol,
            "data": data.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stock/{symbol}/info")
async def get_stock_info(symbol: str):
    """获取股票基本信息"""
    try:
        service = MarketDataService()
        info = service.get_stock_info(symbol)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search_symbol(keyword: str = Query(..., min_length=1)):
    """搜索股票代码"""
    service = MarketDataService()
    results = service.search_symbol(keyword)
    return results
