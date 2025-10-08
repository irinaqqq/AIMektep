from functools import lru_cache
from .config import Config

@lru_cache()
def get_config() -> Config:
    return Config()


