"""Configuration management for QAsmith."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    api_key: str = ""  # Can be empty if using environment variable
    max_tokens: int = 4096
    temperature: float = 0.7


class CrawlerConfig(BaseModel):
    """Crawler configuration."""
    max_depth: int = 3
    max_pages: int = 50
    timeout: int = 30000
    screenshot: bool = True
    viewport: Dict[str, int] = {"width": 1280, "height": 720}
    page_delay_ms: int = 300
    skip_embeddings: bool = True


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


class Neo4jConfig(BaseModel):
    """Neo4j graph database configuration."""
    uri: str = "neo4j://localhost:7687"
    user: str = "neo4j"
    password: str


class Config(BaseSettings):
    """Main configuration class."""
    llm: LLMConfig
    crawler: CrawlerConfig
    runner: RunnerConfig
    storage: StorageConfig
    neo4j: Neo4jConfig
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

        # Prioritize environment variable for API key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            if "llm" not in config_data:
                config_data["llm"] = {}
            config_data["llm"]["api_key"] = anthropic_key
            print("✅ CONFIG: Using ANTHROPIC_API_KEY from environment variable")
        elif "llm" in config_data and not config_data["llm"].get("api_key"):
            raise ValueError(
                "ANTHROPIC_API_KEY must be set in environment variable or config.json"
            )

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


def update_config(updates: Dict[str, Any]) -> None:
    """Update configuration in file."""
    config_path = Path("config/config.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            config_data = json.load(f)
        
        # Update config with new values
        for section, section_updates in updates.items():
            if section in config_data:
                config_data[section].update(section_updates)
            else:
                config_data[section] = section_updates
        
        # Write updated config back to file
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)
        
        # Reset global config to force reload
        global _config
        _config = None
        
        print(f"✅ CONFIG: Updated configuration in {config_path}")
    except Exception as e:
        print(f"❌ CONFIG: Failed to update configuration: {e}")
        raise