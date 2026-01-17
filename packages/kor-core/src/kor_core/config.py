from pathlib import Path
from typing import Optional, Dict, Any
import logging
from pydantic import BaseModel, Field

try:
    import tomllib
except ImportError:
    import tomli as tomllib
import tomli_w

logger = logging.getLogger(__name__)

class UserConfig(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    token: Optional[str] = None

class SecurityConfig(BaseModel):
    paranoid_mode: bool = False

class SecretsConfig(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

class KorConfig(BaseModel):
    user: UserConfig = Field(default_factory=UserConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    plugins: Dict[str, Any] = Field(default_factory=dict)

class ConfigManager:
    """
    Manages loading and saving of the KOR configuration.
    Default path: ~/.kor/config.toml
    """
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (Path.home() / ".kor" / "config.toml")
        self._config: KorConfig = KorConfig()

    def load(self) -> KorConfig:
        """Loads configuration from disk, creating default if missing."""
        if not self.config_path.exists():
            logger.info(f"Config not found at {self.config_path}. Creating default.")
            self.save()
            return self._config

        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)
            self._config = KorConfig(**data)
            logger.debug(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
        
        return self._config

    def save(self) -> None:
        """Saves current configuration to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "wb") as f:
                tomli_w.dump(self._config.model_dump(exclude_none=True), f)
            logger.debug(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def set(self, key: str, value: str) -> None:
        """Sets a configuration value using dot notation (e.g., 'secrets.openai_api_key')."""
        parts = key.lower().split(".")
        if len(parts) == 1:
            # Shorthand for secrets
            if parts[0] in ["openai_api_key", "anthropic_api_key"]:
                setattr(self._config.secrets, parts[0], value)
            else:
                raise KeyError(f"Unknown config key: {key}")
        elif len(parts) == 2:
            section, field = parts
            if hasattr(self._config, section):
                section_obj = getattr(self._config, section)
                if hasattr(section_obj, field):
                    setattr(section_obj, field, value)
                else:
                    raise KeyError(f"Unknown field '{field}' in section '{section}'")
            else:
                raise KeyError(f"Unknown section: {section}")
        else:
            raise KeyError(f"Invalid key format: {key}")
        self.save()

    def get(self, key: str) -> Any:
        """Gets a configuration value using dot notation."""
        parts = key.lower().split(".")
        if len(parts) == 1:
            if parts[0] in ["openai_api_key", "anthropic_api_key"]:
                return getattr(self._config.secrets, parts[0])
            raise KeyError(f"Unknown config key: {key}")
        elif len(parts) == 2:
            section, field = parts
            if hasattr(self._config, section):
                section_obj = getattr(self._config, section)
                if hasattr(section_obj, field):
                    return getattr(section_obj, field)
        raise KeyError(f"Unknown key: {key}")

    @property
    def config(self) -> KorConfig:
        return self._config
