# KOR SDK Documentation

Welcome to the KOR SDK Documentation. KOR is a powerful, extensible Python SDK for building advanced AI Agents and Multi-Agent Systems.

## Quick Start

```bash
uv pip install kor-sdk  # Installation via UV is recommended
```

Initialize a new project:

```bash
kor new my-agent
cd my-agent
kor boot
```

## Documentation Guides

### 🔧 [Configuration Guide](configuration.md)

Everything you need to know about configuring KOR, from environment variables to strict security policies.

- Learn about `config.toml` structure.
- Configure Proxy and SSL settings.
- Manage API keys securely.

### 🧠 [Custom LLMs](custom_llms.md)

Extend KOR with any Large Language Model.

- Use **LiteLLM** for instant access to 100+ providers.
- Implement your own `BaseLLMProvider`.
- Configure purpose-specific models for coding, reasoning, or speed.

### ⚙️ [Core Concepts](core_concepts.md)

Deep dive into the architecture for plugin developers.

- **Kernel**: The heart of the system.
- **Plugins**: creating reusable bundles of agents and tools.
- **Registry & Hooks**: wiring it all together.

## Advanced Topics

- **Agent Graph**: How to build LangGraph-based agents using KOR's primitives.
- **Persistence**: Checkpointing and memory management.
- **Code Graph**: Using the semantic code indexing features.

---
*Generated for KOR SDK v0.4.0*
