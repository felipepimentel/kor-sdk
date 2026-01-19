"""
Tests for declarative hook loading from hooks.json files.
"""
import pytest
import json
from pathlib import Path
from kor_core.events import HooksLoader


@pytest.fixture
def temp_hooks_dir(tmp_path):
    """Create a temporary directory with hooks.json."""
    hooks_config = {
        "on_boot": [
            {"log": "System booted successfully"},
            {"set_context": {"key": "initialized", "value": True}}
        ],
        "on_shutdown": [
            {"log": "Shutting down gracefully"}
        ]
    }
    hooks_file = tmp_path / "hooks.json"
    hooks_file.write_text(json.dumps(hooks_config))
    return tmp_path


def test_hooks_loader_loads_json(temp_hooks_dir):
    """Verify HooksLoader can parse and load hooks.json."""
    loader = HooksLoader()
    hooks = loader.load_file(temp_hooks_dir / "hooks.json")
    
    assert hooks is not None
    assert "on_boot" in hooks
    # Actions are parsed into DeclarativeAction objects, so we check for list
    assert len(hooks["on_boot"]) == 2


def test_hooks_loader_handles_missing_file():
    """Verify HooksLoader handles missing file gracefully."""
    loader = HooksLoader()
    result = loader.load_file(Path("/nonexistent/hooks.json"))
    
    # Should return empty dict for missing file
    assert result == {}


def test_hooks_loader_parses_actions(temp_hooks_dir):
    """Verify actions are parsed into DeclarativeAction objects."""
    loader = HooksLoader()
    hooks = loader.load_file(temp_hooks_dir / "hooks.json")
    
    boot_actions = hooks.get("on_boot", [])
    assert len(boot_actions) == 2
    
    # Each action should be a DeclarativeAction with an action_type
    first_action = boot_actions[0]
    assert hasattr(first_action, "action_type")
    assert first_action.action_type == "log"
