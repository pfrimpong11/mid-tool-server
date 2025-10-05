from typing import List, Optional
from pydantic_settings import BaseSettings
import os
import urllib.parse


class Settings(BaseSettings):
    # Basic settings
    PROJECT_NAME: str = "Medical Image Diagnostics API"
    API_V1_STR: str = "/api/v1"
    
    # Security settings - required from environment
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    ALGORITHM: str = "HS256"
    
    # Database settings - required from environment
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    
    # Use SQLite for development - controlled by environment
    USE_SQLITE: bool = False
    
    # Email settings - optional
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # CORS settings - required from environment
    BACKEND_CORS_ORIGINS: str
    
    # Cloudinary settings - required from environment
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    @property
    def BACKEND_CORS_ORIGINS_LIST(self) -> List[str]:
        """Parse CORS origins from string"""
        origins = self.BACKEND_CORS_ORIGINS
        if not origins:
            return []
        return [origin.strip() for origin in origins.split(",") if origin.strip()]
    
    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite:///./{self.POSTGRES_DB}.db"
        # URL encode the password to handle special characters
        encoded_password = urllib.parse.quote(self.POSTGRES_PASSWORD, safe='')
        return f"postgresql://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///./{self.POSTGRES_DB}.db"
        # URL encode the password to handle special characters
        encoded_password = urllib.parse.quote(self.POSTGRES_PASSWORD, safe='')
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Password reset settings
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    
    model_config = {"case_sensitive": True, "env_file": ".env"}


settings = Settings()