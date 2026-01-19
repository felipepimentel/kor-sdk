from unittest.mock import MagicMock, patch, AsyncMock
from click.testing import CliRunner
from kor_cli.commands.chat import chat

def test_chat_command_initialization():
    """Verify chat command initializes and calls get_agent correctly."""
    runner = CliRunner()
    
    with patch("kor_core.kernel.get_kernel") as mock_get_kernel, \
         patch("kor_cli.commands.chat.get_checkpointer") as mock_get_cp, \
         patch("kor_cli.commands.chat.create_graph") as mock_create_graph, \
         patch("kor_cli.commands.chat.GraphRunner") as mock_runner_cls, \
         patch("kor_cli.commands.chat.console") as mock_console:
        
        # Setup mocks
        mock_kernel = MagicMock()
        mock_kernel.shutdown = AsyncMock()
        mock_get_kernel.return_value = mock_kernel
        mock_kernel.config.agent.active_graph = "default-supervisor"
        
        mock_registry = MagicMock()
        mock_kernel.registry.get_service.return_value = mock_registry
        
        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner
        # effectively stop the loop immediately
        mock_runner.run.side_effect = KeyboardInterrupt 
        
        # Run chat
        # We simulate user input "exit" to break the loop if it enters it
        result = runner.invoke(chat, input="exit\n")
        
        # Assertions
        mock_kernel.registry.get_service.assert_called_with("agents")
        
        # This is the critical check: It should call get_agent, NOT get_agent_definition
        # And it should not raise AttributeError
        mock_registry.get_agent.assert_called_with("default-supervisor")
        
        # Verify no crash
        assert result.exit_code == 0
