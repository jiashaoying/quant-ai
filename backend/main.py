"""
股票量化策略查看系统 - 后端API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import strategies, backtest, market
from app.core.config import settings

app = FastAPI(
    title="量化策略查看系统",
    description="本地股票量化策略查看与回测系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(strategies.router, prefix="/api/strategies", tags=["策略"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["回测"])
app.include_router(market.router, prefix="/api/market", tags=["市场数据"])

@app.get("/")
async def root():
    return {"message": "量化策略查看系统API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
