"""Test CLI chat command basic smoke test."""
from click.testing import CliRunner
from kor_cli.commands.chat import chat
from kor_core.kernel import reset_kernel

def test_chat_command_exits_cleanly():
    """Verify chat command handles exit input without crashing."""
    runner = CliRunner()
    
    # Reset kernel singleton before test
    reset_kernel()
    
    # Run chat with "exit" to break the loop immediately
    # We don't mock create_graph because it may fail (no LLM), 
    # but the error handling should still work
    result = runner.invoke(chat, input="exit\n")
    
    # The command should not crash (exit_code 0 or handled gracefully)
    # Even if create_graph fails, we expect graceful error handling
    assert result.exit_code == 0
    
    # Reset after test
    reset_kernel()
