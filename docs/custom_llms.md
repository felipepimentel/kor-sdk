# Custom LLM Integration

KOR SDK features a pluggable LLM architecture that supports arbitrary providers. While it comes with built-in support for OpenAI and LiteLLM (which supports 100+ providers), you can also register your own custom providers.

## The LLM Registry

All LLM interactions are mediated through the `LLMRegistry`. This registry manages:

1. **Providers**: Classes that know how to talk to a specific API (e.g., `OpenAIProvider`, `AnthropicProvider`).
2. **Models**: Instances of configured models bound to a provider.

```python
from kor_core.kernel import get_kernel

kernel = get_kernel()
llm_registry = kernel.registry.get_service("llm")

# Get a model instance (uses default config)
model = llm_registry.get_model("openai:gpt-4")
response = await model.agenerate("Hello!")
```

## Using LiteLLM (Recommended)

KOR integrates with [LiteLLM](https://docs.litellm.ai/), which provides a unified interface for virtually all major LLM providers (Anthropic, Vertex AI, Ollama, HuggingFace, etc.).

To use a LiteLLM model, simply prefix the model name with `litellm/` in your configuration or code.

### Configuration Example

```toml
[llm.providers.litellm]
# No API key needed here as LiteLLM reads from environment variables
extra = { drop_params = true }

[llm.purposes.coding]
provider = "litellm"
model = "claude-3-opus"  # Maps to anthropic/claude-3-opus
```

Ensure you have the necessary environment variables set (e.g., `ANTHROPIC_API_KEY`).

## Creating a Custom Provider

If you need to support a custom model or API not covered by LiteLLM, you can implement `BaseLLMProvider`.

### 1. Implement the Provider Class

```python
from typing import Any, Dict
from kor_core.llm.base import BaseLLMProvider, BaseLLMModel

class MyCustomModel(BaseLLMModel):
    async def agenerate(self, prompt: str, **kwargs) -> str:
        # custom inference logic
        return f"Echo: {prompt}"

class MyCustomProvider(BaseLLMProvider):
    @property
    def id(self) -> str:
        return "my-provider"
        
    def create_model(self, model_name: str, config: Dict[str, Any]) -> BaseLLMModel:
        return MyCustomModel(model_name, config)
```

### 2. Register Your Provider

You can register your provider in a plugin or correct during kernel initialization.

```python
from kor_core.plugin import KorPlugin, KorContext

class MyPlugin(KorPlugin):
    id = "my-custom-llm"
    
    def initialize(self, context: KorContext):
        registry = context.get_llm_registry()
        registry.register(MyCustomProvider())
```

### 3. Use It

Update your `config.toml`:

```toml
[llm.default]
provider = "my-provider"
model = "custom-v1"
```

## Model Selection

KOR uses a `ModelSelector` to dynamically choose the best model for a given task ("purpose").

- **Default Purpose**: Used when no specific purpose is requested.
- **Custom Purposes**: You can define purposes like `coding`, `fast`, `creative` in `config.toml`.

```python
selector = kernel.model_selector
coding_model = selector.get_model(purpose="coding")
```
