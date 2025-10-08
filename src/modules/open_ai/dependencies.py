from .service import OpenAIService
from core.dependencies import get_config

def get_ai_service() -> OpenAIService:
    return OpenAIService(config=get_config())