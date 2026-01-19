from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static, LoadingIndicator
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
import asyncio

from kor_core import EventBus, AgentRuntime, EventType, KorEvent

class ChatApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 20% 80%;
    }
    #sidebar {
        background: $panel;
        border-right: vkey $accent;
        height: 100%;
    }
    #chat-area {
        height: 100%;
        layout: vertical;
    }
    #log {
        height: 1fr;
        border: solid $accent;
    }
    #input-box {
        dock: bottom;
        height: 3;
    }
    .status-bar {
        dock: top;
        height: 1;
        background: $accent;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()
        self.agent = AgentRuntime(self.event_bus)
        self.log_widget = RichLog(id="log", wrap=True, highlight=True, markup=True)
        self.input_widget = Input(placeholder="Type a command...", id="input-box")
        self.status = Static("Ready", classes="status-bar")
        self.loading = LoadingIndicator()
        self.loading.display = False

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="sidebar"):
            yield Static("Plugins (Loaded)")
            yield Static("- Core\n- TUI")

        with Vertical(id="chat-area"):
            yield self.status
            yield self.loading
            yield self.log_widget
            yield self.input_widget
            
        yield Footer()

    async def on_mount(self):
        self.input_widget.focus()
        
        # Bridge kor-core events to Textual app
        class EventBridge:
            def __init__(self, app):
                self.app = app
            async def on_event(self, event: KorEvent):
                # We must schedule the callback on the main thread/loop if needed
                # But here we just call the handler
                await self.app.on_kor_event(event)

        self.event_bus.subscribe(EventBridge(self))

    async def on_kor_event(self, event: KorEvent):
        """Handle events from Core."""
        if event.type == EventType.AGENT_THINKING:
            status = event.payload.get("status")
            if status == "started":
                 self.status.update("Agent is thinking...")
                 self.loading.display = True
            else:
                 self.status.update("Ready")
                 self.loading.display = False
        
        elif event.type == EventType.TOOL_CALL_STARTED:
            tool = event.payload.get("tool")
            self.log_widget.write(f"[yellow]Executing Tool: {tool}[/yellow]")

    async def on_input_submitted(self, message: Input.Submitted):
        user_input = message.value
        self.input_widget.value = ""
        
        self.log_widget.write(f"[bold green]User:[/bold green] {user_input}")
        
        # Run interaction in background
        asyncio.create_task(self.process_input(user_input))

    async def process_input(self, text: str):
        async for token in self.agent.run_interaction(text):
            self.log_widget.write(token, end="")
        self.log_widget.write("\n")

def run():
    app = ChatApp()
    app.run()
