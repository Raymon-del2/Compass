"""Global configuration for Compass backend.
Currently reads configuration from environment variables or defaults.
In real deployment, could load from .env or config files.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# load .env from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)
from typing import Dict

class Settings:
    # Comma-separated list of enabled adapter names
    enabled_adapters: list[str]
    # Mapping of adapter name to API key (optional)
    api_keys: Dict[str, str]

    def __init__(self):
        adapters = os.getenv("COMPASS_ADAPTERS", "duckduckgo,bing_stub,brave_stub,google_cse")
        self.enabled_adapters = [a.strip() for a in adapters.split(',') if a.strip()]
        keys_env = os.getenv("COMPASS_API_KEYS", "")
        # expected format: name:key;name2:key2
        self.api_keys = {}
        for pair in keys_env.split(';'):
            if ':' in pair:
                name, key = pair.split(':', 1)
                self.api_keys[name.strip()] = key.strip()

        # Turso database credentials
        self.turso_db_url: str = os.getenv("TURSO_DB_URL", "")
        self.turso_auth_token: str = os.getenv("TURSO_AUTH_TOKEN", "")
        
        # Compass AI API key (Serper API key)
        self.compass_api_key: str = os.getenv("SERPER_API_KEY", "")

settings = Settings()
