from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import os
import re
from pydantic import BaseModel, Field

try:
    import tomllib
except ImportError:
    import tomli as tomllib
import tomli_w

logger = logging.getLogger(__name__)

class BaseConfig(BaseModel):
    model_config = {"validate_assignment": True, "extra": "ignore"}

class UserConfig(BaseConfig):
    id: Optional[str] = None
    name: Optional[str] = None
    token: Optional[str] = None

class SecurityConfig(BaseConfig):
    paranoid_mode: bool = False

class SecretsConfig(BaseConfig):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

# New LLM Configuration Schemas
class ProviderConfig(BaseConfig):
    """Config for a single LLM provider."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
    
    # Fallback chain - try next provider if this fails (Opt-in only)
    fallback: Optional[str] = None 

class ModelRef(BaseConfig):
    """Reference to a specific model."""
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None

class LLMConfig(BaseConfig):
    """Complete LLM configuration. NO DEFAULTS - user must configure."""
    default: Optional[ModelRef] = None  # Must be configured!
    
    # Purpose-specific overrides (string keys = dynamic, user-defined)
    purposes: Dict[str, ModelRef] = Field(default_factory=dict)
    
    # Provider configurations
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    
    # Cache settings
    cache_models: bool = True 

class AgentDefinition(BaseConfig):
    """Configuration for a dynamic agent worker."""
    name: Optional[str] = None  # specific instance name
    role: str = "You are a helpful assistant."
    goal: str = "Assist the user."
    llm_purpose: str = "default"
    tools: list[str] = Field(default_factory=list)

class AgentConfig(BaseConfig):
    # Which graph to run
    active_graph: str = "default-supervisor"
    
    # List of active workers for the supervisor
    supervisor_members: list[str] = ["Architect", "Coder", "Reviewer", "Researcher", "Explorer"]
    
    # Dynamic definitions: name -> definition
    definitions: Dict[str, AgentDefinition] = Field(default_factory=dict)

class ValidatorConfig(BaseModel):
    command: str
    args: List[str] = Field(default_factory=list)
    format: str = "json"  # json, text, ruff-json, etc.

class LanguageConfig(BaseConfig):
    extensions: List[str]
    validator: Optional[ValidatorConfig] = None
    linter: Optional[ValidatorConfig] = None
    lsp: Optional[ValidatorConfig] = None # Re-using ValidatorConfig structure for Command+Args

class PersistenceConfig(BaseConfig):
    """Configuration for agent state persistence."""
    type: str = "sqlite"  # options: "sqlite", "memory"
    path: Optional[str] = None  # db path or connection string

class NetworkConfig(BaseConfig):
    """Network configuration for proxy, SSL, and timeouts."""
    http_proxy: Optional[str] = None      # e.g., "http://proxy:8080"
    https_proxy: Optional[str] = None
    no_proxy: str = "localhost,127.0.0.1"
    ca_bundle: Optional[str] = None       # Custom CA cert path
    verify_ssl: bool = True
    connect_timeout: int = 30             # seconds
    read_timeout: int = 120               # seconds

class MCPServerConfig(BaseConfig):
    """Configuration for an MCP server."""
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    disabled: bool = False

class LSPServerConfig(BaseConfig):
    """Configuration for an LSP server."""
    command: str
    args: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)

def default_languages():
    return {
        "python": LanguageConfig(
            extensions=[".py"],
            validator=ValidatorConfig(command="pyright", args=["--outputjson"], format="json"),
            lsp=ValidatorConfig(command="pyright-langserver", args=["--stdio"], format="lsp")
        )
    }

class KorConfig(BaseConfig):
    user: UserConfig = Field(default_factory=UserConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    
    # Persistence
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    
    # Network (proxy, SSL, timeouts)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    
    # New LLM Section
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    agent: AgentConfig = Field(default_factory=AgentConfig)
    
    # Language & Validation
    languages: Dict[str, LanguageConfig] = Field(default_factory=default_languages)
    
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
            
            # Environment variable interpolation
            data = self._interpolate_env_vars(data)
            
            self._config = KorConfig(**data)
            self._validate_config()
            logger.debug(f"Loaded config from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults (which might fail validation if LLM not configured).")
        
        return self._config

    def _validate_config(self):
        """Perform semantic validation on the configuration."""
        if not self._config.llm.default and not self._config.llm.purposes:
            # Only warn if no LLM configured at all, as it might be fine for some use cases
            logger.warning("No default LLM configuration found ([llm.default]). AI features may fail.")


    def _interpolate_env_vars(self, data: Any) -> Any:
        """Resolve ${VAR} or $VAR patterns from environment."""
        
        def resolve(value):
            if isinstance(value, str):
                # Match ${VAR} or $VAR patterns
                pattern = r'\$\{?(\w+)\}?'
                return re.sub(pattern, lambda m: os.environ.get(m.group(1), m.group(0)), value)
            elif isinstance(value, dict):
                return {k: resolve(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve(v) for v in value]
            return value
        
        return resolve(data)

    def save(self, config: Optional[KorConfig] = None) -> None:
        """Saves configuration to disk."""
        if config:
            self._config = config
            
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "wb") as f:
                tomli_w.dump(self._config.model_dump(exclude_none=True), f)
            logger.debug(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def update(self, overrides: Dict[str, Any]) -> None:
        """
        Updates the in-memory configuration with the provided dictionary.
        Does NOT save to disk.
        """
        for k, v in overrides.items():
            self.set(k, v, persist=False)
            
    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Sets a configuration value using dot notation (e.g., 'secrets.openai_api_key')."""
        parts = key.lower().split(".")
        
        # We can't easily set nested attributes on Pydantic models directly with getattr/setattr
        # cleanly without traversing.
        
        # Let's map back to dict, update, and re-validate
        data = self._config.model_dump()
        target = data
        
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        
        target[parts[-1]] = value
        
        # Re-create config to validate
        self._config = KorConfig(**data)
        
        if persist:
            self.save()

    @property
    def config(self) -> KorConfig:
        return self._config
