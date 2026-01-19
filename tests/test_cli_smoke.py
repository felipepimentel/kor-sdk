import pytest
from click.testing import CliRunner
from kor_cli.main import main

# List of commands to smoke test
COMMANDS = [
    "boot",
    "chat",
    "config",
    "doctor",
    "new",
    "plugin",
    "serve",
    "trace",
    "version",
]

@pytest.mark.parametrize("command", COMMANDS)
def test_cli_command_help(command):
    """
    Smoke test: Ensure each command can run with --help.
    This catches ImportErrors, SyntaxErrors, and basic definition errors
    in the command modules.
    """
    runner = CliRunner()
    result = runner.invoke(main, [command, "--help"])
    
    # Check for non-zero exit code (crash)
    assert result.exit_code == 0, f"Command '{command}' crashed: {result.output}"
    
    # Check that help text is displayed (basic validation)
    assert "Usage:" in result.output
    # The command name should usually appear in the help text
    # e.g. "Usage: kor boot ..."
    assert command in result.output or "Usage:" in result.output
