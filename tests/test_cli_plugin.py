import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from kor_cli.commands.plugin import list as list_cmd
from kor_cli.commands.plugin import install as install_cmd

def test_plugin_list_empty():
    """Verify list command handles no plugins."""
    runner = CliRunner()
    with patch("importlib.metadata.entry_points") as mock_eps:
        mock_eps.return_value = []
        result = runner.invoke(list_cmd)
        assert result.exit_code == 0
        assert "No plugins found" in result.output

def test_plugin_install_success():
    """Verify install command calls subprocess correctly."""
    runner = CliRunner()
    with patch("subprocess.check_call") as mock_call:
        result = runner.invoke(install_cmd, ["my-plugin"])
        
        assert result.exit_code == 0
        assert "Successfully installed my-plugin" in result.output
        
        # Check calling args
        args = mock_call.call_args[0][0]
        # Should be something like [sys.executable, "-m", "pip", "install", "my-plugin"]
        assert "pip" in args
        assert "install" in args
        assert "my-plugin" in args
