# Configuration Guide

KOR SDK uses a flexible configuration system based on `config.toml` and environment variables. This guide explains how to configure every aspect of the system.

## Configuration File

By default, KOR looks for a configuration file at `~/.kor/config.toml`. You can override this path by setting the `KOR_CONFIG` environment variable.

### Structure

The configuration is divided into several sections:

- **[user]**: User identity and tokens.
- **[security]**: Security policies (e.g., paranoid mode).
- **[secrets]**: API keys for external services.
- **[network]**: Proxy and SSL settings.
- **[persistence]**: Database configuration.
- **[llm]**: Large Language Model settings.
- **[agent]**: Agent definitions and graph settings.
- **[languages]**: Language-specific tooling config.

## Example `config.toml`

```toml
[user]
name = "Developer"
token = "kor_dev_token"

[security]
paranoid_mode = false  # If true, all sensitive actions require explicit approval

[secrets]
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."

[network]
http_proxy = "http://proxy.internal:8080"
no_proxy = "localhost,127.0.0.1"
verify_ssl = true
connect_timeout = 30

[persistence]
type = "sqlite"
path = "~/.kor/memories.db"

[llm]
cache_models = true

# DEFAULT MODEL (Required)
[llm.default]
provider = "openai"
model = "gpt-4-turbo"
temperature = 0.5

# Purpose-specific overrides
[llm.purposes.coding]
provider = "anthropic"
model = "claude-3-opus-20240229"
temperature = 0.2

[llm.purposes.fast]
provider = "openai"
model = "gpt-3.5-turbo"

# Provider-specific settings
[llm.providers.openai]
base_url = "https://api.openai.com/v1"
# chain fallback: if openai fails, try anthropic
fallback = "anthropic"

[llm.providers.anthropic]
# extra settings passed to the provider
extra = { max_retries = 3 }
```

## Environment Variables

All configuration values can be overridden using environment variables or interpolated within the config file.

### Environment Variable Overrides

Format: `KOR_<SECTION>_<KEY>` (case-insensitive).

- `KOR_SECRETS_OPENAI_API_KEY` overrides `[secrets] openai_api_key`
- `KOR_LLM_DEFAULT_MODEL` overrides `[llm.default] model`
- `KOR_SECURITY_PARANOID_MODE=true` overrides `[security] paranoid_mode`

### Variable Interpolation

You can use `${VAR_NAME}` syntax inside `config.toml`:

```toml
[secrets]
openai_api_key = "${MY_OPENAI_KEY}"
```

## Network Configuration

KOR respects standard proxy environment variables, but you can also configure them explicitly in `[network]`.

- `http_proxy` / `https_proxy`: Proxy URL.
- `ca_bundle`: Path to a custom CA certificate bundle for SSL verification.
- `verify_ssl`: Set to `false` to disable SSL verification (not recommended).

## Programmatic Usage

You can load and modify configuration programmatically using `ConfigManager`.

```python
from kor_core.config import ConfigManager

manager = ConfigManager()
config = manager.load() # Loads from disk

# Access values
print(f"Using model: {config.llm.default.model}")

# Update values (runtime only)
manager.update({
    "llm.default.temperature": 0.9
})

# Persist changes to disk
manager.set("user.name", "Alice", persist=True)
```
