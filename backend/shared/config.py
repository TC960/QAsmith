"""Configuration management for QAsmith."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    api_key: str
    max_tokens: int = 4096
    temperature: float = 0.7


class CrawlerConfig(BaseModel):
    """Crawler configuration."""
    max_depth: int = 3
    max_pages: int = 50
    timeout: int = 30000
    screenshot: bool = True
    viewport: Dict[str, int] = {"width": 1280, "height": 720}


class RunnerConfig(BaseModel):
    """Test runner configuration."""
    browser: str = "chromium"
    headless: bool = True
    trace: bool = True
    video: bool = True
    screenshot: str = "only-on-failure"


class StorageConfig(BaseModel):
    """Storage paths configuration."""
    artifacts_path: str = "./backend/artifacts"
    app_maps_path: str = "./backend/app_maps"
    test_specs_path: str = "./backend/test_specs"
    reports_path: str = "./backend/reports"


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


class Config(BaseSettings):
    """Main configuration class."""
    llm: LLMConfig
    crawler: CrawlerConfig
    runner: RunnerConfig
    storage: StorageConfig
    api: APIConfig

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from JSON file."""
        if config_path is None:
            # Try multiple locations
            possible_paths = [
                Path("config/config.json"),
                Path("../config/config.json"),
                Path("../../config/config.json"),
            ]
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            else:
                raise FileNotFoundError(
                    "Config file not found. Please create config/config.json from config/config.example.json"
                )

        with open(config_path, "r") as f:
            config_data = json.load(f)

        return cls(**config_data)

    def ensure_storage_paths(self):
        """Create storage directories if they don't exist."""
        for path_attr in ["artifacts_path", "app_maps_path", "test_specs_path", "reports_path"]:
            path = Path(getattr(self.storage, path_attr))
            path.mkdir(parents=True, exist_ok=True)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config.load_from_file()
        _config.ensure_storage_paths()
    return _config