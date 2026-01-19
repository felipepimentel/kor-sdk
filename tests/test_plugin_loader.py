import json
import tempfile
from pathlib import Path
from kor_core.loader import PluginLoader
from kor_core.plugin.manifest import PluginManifest
from kor_core.plugin import KorPlugin, KorContext, ServiceRegistry

class MockPlugin(KorPlugin):
    @property
    def id(self) -> str:
        return "mock-plugin"
    
    def initialize(self, context: KorContext) -> None:
        context.registry.register_service("mock_service", lambda: "hello")

def test_manifest_validation():
    """Test that PluginManifest validates correctly."""
    data = {
        "name": "test-plugin",
        "version": "0.1.0",
        "description": "A test plugin",
        "entry_point": "test_plugin:Plugin",
        "provides": ["test-cap"],
        "dependencies": ["other-cap"]
    }
    manifest = PluginManifest(**data)
    assert manifest.name == "test-plugin"
    assert manifest.provides == ["test-cap"]


def test_loader_directory_discovery():
    """Test that PluginLoader discovers plugins in a directory."""
    loader = PluginLoader()
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = Path(tmpdir) / "test-plugin"
        plugin_dir.mkdir()
        
        manifest_data = {
            "name": "dir-plugin",
            "version": "0.1.0",
            "description": "Test",
            "entry_point": "test:Plugin"
        }
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(manifest_data, f)
            
        loader.load_directory_plugins(Path(tmpdir))
        assert "dir-plugin" in loader._discovered_manifests
        assert loader._discovered_manifests["dir-plugin"].version == "0.1.0"

def test_plugin_instantiation():
    """Test manual registration and instantiation of plugin classes."""
    loader = PluginLoader()
    loader.register_plugin_class(MockPlugin)
    
    registry = ServiceRegistry()
    context = KorContext(registry=registry, config={})
    
    loader.load_plugins(context)
    assert "mock-plugin" in loader._plugins
    assert registry.get_service("mock_service")() == "hello"

def test_loader_isolation():
    """Test that a failing plugin does not stop others from loading."""
    class FailingPlugin(KorPlugin):
        @property
        def id(self) -> str:
            return "failing-plugin"
        def initialize(self, context: KorContext) -> None:
            raise RuntimeError("Initialization failed!")

    loader = PluginLoader()
    loader.register_plugin_class(FailingPlugin)
    loader.register_plugin_class(MockPlugin)
    
    registry = ServiceRegistry()
    context = KorContext(registry=registry, config={})
    
    # Should not raise exception
    loader.load_plugins(context)
    
    assert "mock-plugin" in loader._plugins
    assert "failing-plugin" not in loader._plugins
