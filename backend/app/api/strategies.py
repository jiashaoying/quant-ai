"""
策略API路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.strategies.engine import get_available_strategies

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_strategies():
    """获取所有可用策略"""
    return get_available_strategies()


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    """获取策略详情"""
    strategies = get_available_strategies()
    for strategy in strategies:
        if strategy["id"] == strategy_id:
            return strategy
    raise HTTPException(status_code=404, detail="Strategy not found")
