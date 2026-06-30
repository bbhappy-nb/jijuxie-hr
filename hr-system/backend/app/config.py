"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets


class Settings(BaseSettings):
    APP_NAME: str = "寄居蟹一代 - HR管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = "sqlite:///./hr_system.db"

    # JWT — 生产环境必须通过环境变量设置，否则每次重启自动生成随机密钥
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8小时

    # 文件上传
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"


settings = Settings()
