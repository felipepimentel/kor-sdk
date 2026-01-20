from click.testing import CliRunner
from kor_cli.main import main

def test_cli_entry_point():
    """Verify the main entry point is correctly defined and runnable."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "KOR CLI" in result.output
    assert "boot" in result.output
    assert "chat" in result.output

def test_cli_boot_help():
    """Verify boot command subcommand."""
    runner = CliRunner()
    result = runner.invoke(main, ["boot", "--help"])
    assert result.exit_code == 0
    assert "Boots the Kernel" in result.output
