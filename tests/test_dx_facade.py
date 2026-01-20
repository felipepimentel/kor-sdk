
import pytest
import asyncio
from kor_core.api import Kor

def test_zero_config_init():
    """Test initializing Kor with direct arguments."""
    api_key = "sk-test-key"
    model = "anthropic:claude-3-opus"
    
    kor = Kor(api_key=api_key, model=model)
    
    # Check if config was updated correctly
    # Note: We access internal kernel config for verification
    config = kor.kernel.config
    
    # Check secret injection (heuristic for claude mapped to anthropic key)
    assert config.secrets.anthropic_api_key == api_key
    
    # Check model default
    assert config.llm.default.provider == "anthropic"
    assert config.llm.default.model == "claude-3-opus"

def test_zero_config_init_defaults():
    """Test defaults for zero config."""
    api_key = "sk-test-openai"
    kor = Kor(api_key=api_key)
    
    config = kor.kernel.config
    # Default fallback is openai key
    assert config.secrets.openai_api_key == api_key

@pytest.mark.asyncio
async def test_run_sync_in_async_context_raises_error():
    """Test that calling run_sync from an async context raises RuntimeError."""
    kor = Kor()
    
    # We are inside an async test, so an event loop is running.
    # calling run_sync should trigger the safeguard.
    
    with pytest.raises(RuntimeError) as excinfo:
        kor.run_sync("hello")
    
    assert "active async event loop" in str(excinfo.value)

def test_run_sync_no_loop_works():
    """Test that run_sync works when no loop is running (simulated)."""
    from unittest.mock import patch
    
    # We can't easily test the full success path of run_sync here because it requires
    # a full kernel boot and graph execution which might be heavy.
    # Instead, we mock asyncio.run and asyncio.get_running_loop to verify the logic flow.
    
    with patch("asyncio.get_running_loop", side_effect=RuntimeError), \
         patch("asyncio.run", return_value=["event1", "event2"]) as mock_run:
        
        kor = Kor()
        
        events = kor.run_sync("hello")
        
        assert events == ["event1", "event2"]
        mock_run.assert_called_once()
