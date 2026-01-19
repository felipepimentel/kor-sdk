import pytest
from unittest.mock import MagicMock
from kor_core.llm.selector import ModelSelector
from kor_core.llm.registry import LLMRegistry
from kor_core.llm.exceptions import ConfigurationError

def test_model_caching(mock_config, llm_registry):
    """Verify that models are cached when cache_models is True."""
    mock_config.llm.cache_models = True
    selector = ModelSelector(llm_registry, mock_config.llm)
    
    # Mock the internal methods to avoid actual instantiation complexity
    mock_model = MagicMock()
    selector._create_model_from_ref = MagicMock(return_value=mock_model)
    
    # First call - should create
    m1 = selector.get_model("default")
    assert m1 == mock_model
    selector._create_model_from_ref.assert_called_once()
    
    # Second call - should return cached
    m2 = selector.get_model("default")
    assert m2 == mock_model
    # Call count should still be 1
    selector._create_model_from_ref.assert_called_once() 

def test_model_caching_disabled(mock_config, llm_registry):
    """Verify caching is skipped when disabled."""
    mock_config.llm.cache_models = False
    selector = ModelSelector(llm_registry, mock_config.llm)
    
    mock_model = MagicMock()
    selector._create_model_from_ref = MagicMock(return_value=mock_model)
    
    m1 = selector.get_model("default")
    m2 = selector.get_model("default")
    
    assert selector._create_model_from_ref.call_count == 2

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
