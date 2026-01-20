import pytest
from unittest.mock import MagicMock
from kor_core.llm.selector import ModelSelector
from kor_core.llm import ConfigurationError



def test_override_resolution(mock_config, llm_registry):
    """Verify explicit overrides take precedence."""
    # Setup valid provider config for Pydantic
    mock_config.llm.providers = {"openai": {"api_key": "dummy"}}
    
    selector = ModelSelector(llm_registry, mock_config.llm)
    selector.registry.get_model = MagicMock(return_value="overridden-model")
    
    result = selector.get_model("default", override="openai:gpt-4o")
    
    assert result == "overridden-model"
    # Note: final_config might differ slightly based on extraction logic
    # We allow any kwargs for the last argument
    selector.registry.get_model.assert_called_once()
    assert selector.registry.get_model.call_args[0][:2] == ("openai", "gpt-4o")

def test_missing_config_raises_error(mock_config, llm_registry):
    """Verify checking for missing configuration."""
    mock_config.llm.default = None
    mock_config.llm.purposes = {}
    
    selector = ModelSelector(llm_registry, mock_config.llm)
    
    with pytest.raises(ConfigurationError):
        selector.get_model("unknown")
