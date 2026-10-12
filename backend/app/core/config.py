"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "量化策略查看系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./quant.db"
    
    # 数据源配置
    DEFAULT_MARKET: str = "CN"  # CN, US, HK
    
    class Config:
        env_file = ".env"


settings = Settings()
