"""
Configuration management via environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration loaded from environment variables."""
    
    # Database
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_pool_size: int
    
    # OpenAI
    openai_api_key: str
    openai_reasoning_model: str
    
    # Finsmart API
    finsmart_base_url: str
    finsmart_api_key: str
    finsmart_password: str
    finsmart_company_guid: Optional[str]
    
    @property
    def dsn(self) -> str:
        """Build PostgreSQL DSN from components."""
        if self.db_password:
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return f"postgresql://{self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}"


def load_config() -> Config:
    """
    Load configuration from environment variables.
    
    Required env vars:
        - OPENAI_API_KEY
        - API_KEY (Finsmart)
        - PASSWORD (Finsmart)
    
    Optional (with defaults):
        - DB_HOST (localhost)
        - DB_PORT (5432)
        - DB_NAME (postgres)
        - DB_USER (ozgurguler)
        - DB_PASSWORD (empty)
        - DB_POOL_SIZE (5)
        - OPENAI_REASONING_MODEL (gpt-4o-mini)
        - FINSMART_BASE_URL
        - COMPANY_GUID
    """
    return Config(
        # Database
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "postgres"),
        db_user=os.getenv("DB_USER", "ozgurguler"),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        
        # OpenAI
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_reasoning_model=os.getenv("OPENAI_REASONING_MODEL", "gpt-4o-mini"),
        
        # Finsmart
        finsmart_base_url=os.getenv("FINSMART_BASE_URL", "https://dev-datauploadapi.finsmart.ai"),
        finsmart_api_key=os.getenv("API_KEY", ""),
        finsmart_password=os.getenv("PASSWORD", ""),
        finsmart_company_guid=os.getenv("COMPANY_GUID"),
    )


# Singleton config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the singleton config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
