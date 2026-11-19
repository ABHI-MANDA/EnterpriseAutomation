"""Core Configuration for the Real Estate Enterprise Command Center."""
import os
import secrets
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    PROJECT_NAME: str = "Centralized Real Estate Command Center"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Secrets
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "prod-secret-change-in-production-" + secrets.token_hex(16))
    CRM_WEBHOOK_SECRET: str = os.getenv("CRM_WEBHOOK_SECRET", "crm-webhook-secret-key-32chars-min!")
    FIELD_ENCRYPTION_KEY: str = os.getenv("FIELD_ENCRYPTION_KEY", "aes-256-gcm-key-32bytes-secret-v1!!")
    HMAC_LOOKUP_KEY: str = os.getenv("HMAC_LOOKUP_KEY", "hmac-lookup-key-32bytes-deterministic!!")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./platform.db")
    
    # Token & Session
    TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours operational session
    MAX_LOGIN_FAILURES: int = 5
    LOCKOUT_MINUTES: int = 15
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # LLM / AI Integration (OpenAI-compatible gateway)
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    
    # Keycloak OIDC Settings
    KEYCLOAK_URL: str = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "realestate-enterprise")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "command-center")

settings = Settings()
