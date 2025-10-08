import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from functools import cached_property

load_dotenv()

class Config:
    # === BASE / AUTH ===
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    OAUTH2_TOKEN_URL: str = "/" \
    "v1/auth/login"

    # === GENERAL SETTINGS ===
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ALLOWED_HOSTS: list[str] = os.getenv("ALLOWED_HOSTS", "").split(",")

    # === DATABASE ===
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # === OPENAI ===
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_VERSION: str = os.getenv("AZURE_OPENAI_VERSION")
    
    @cached_property
    def azure_client(self) -> AzureOpenAI:
        return AzureOpenAI(
            api_key=self.AZURE_OPENAI_API_KEY,
            api_version=self.AZURE_OPENAI_VERSION,
            azure_endpoint=self.AZURE_OPENAI_ENDPOINT
        )