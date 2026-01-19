#!/usr/bin/env python3
"""
KOR SDK - Scenario: Configuration System Verification
Validates configuration loading, migration, and environment variable interpolation.
"""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))

from kor_core.config import ConfigManager, KorConfig, AgentConfig

def test_configuration_system():
    """Test configuration loading and validation."""
    print("=" * 50)
    print("   SCENARIO: Configuration System Verification")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    # 1. Default Config Creation
    print("\n[1] Testing Default Config Creation...")
    config = KorConfig()
    
    if config.user is not None and config.agent is not None:
        print("    ✅ Default config created with all sections")
        results["passed"] += 1
    else:
        print("    ❌ Missing config sections")
        results["failed"] += 1
    
    # 2. Config Manager with Temp File
    print("\n[2] Testing Config Manager...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        manager = ConfigManager(config_path)
        manager.load()  # Just execute, don't store
        
        if config_path.exists():
            print("    ✅ Config file created automatically")
            results["passed"] += 1
        else:
            print("    ❌ Config file not created")
            results["failed"] += 1
    
    # 3. Environment Variable Interpolation
    print("\n[3] Testing Environment Variable Interpolation...")
    os.environ["TEST_API_KEY"] = "sk-test-12345"
    
    manager = ConfigManager()
    test_data = {"secrets": {"openai_api_key": "${TEST_API_KEY}"}}
    interpolated = manager._interpolate_env_vars(test_data)
    
    if interpolated["secrets"]["openai_api_key"] == "sk-test-12345":
        print("    ✅ Environment variables interpolated correctly")
        results["passed"] += 1
    else:
        print(f"    ❌ Interpolation failed: {interpolated}")
        results["failed"] += 1
    
    del os.environ["TEST_API_KEY"]
    
    # 4. Legacy Config Migration
    print("\n[4] Testing Legacy Config Migration...")
    legacy_data = {
        "model": {
            "provider": "openai",
            "name": "gpt-4",
            "temperature": 0.5
        },
        "secrets": {"openai_api_key": "sk-legacy"}
    }
    
    migrated = manager._migrate_legacy_config(legacy_data)
    
    if "llm" in migrated and "model" not in migrated:
        print("    ✅ Legacy [model] migrated to [llm]")
        results["passed"] += 1
    else:
        print("    ❌ Migration failed")
        results["failed"] += 1
    
    if migrated["llm"]["default"]["provider"] == "openai":
        print("    ✅ Provider correctly migrated")
        results["passed"] += 1
    else:
        print("    ❌ Provider migration failed")
        results["failed"] += 1
    
    # 5. Validate Assignment (Pydantic)
    print("\n[5] Testing Pydantic Validation...")
    config = KorConfig()
    
    try:
        config.security.paranoid_mode = True
        if config.security.paranoid_mode:
            print("    ✅ Validated assignment works")
            results["passed"] += 1
    except Exception as e:
        print(f"    ❌ Validation failed: {e}")
        results["failed"] += 1
    
    # 6. Agent Config Defaults
    print("\n[6] Testing Agent Config Defaults...")
    agent_config = AgentConfig()
    
    if agent_config.active_graph == "default-supervisor":
        print("    ✅ Default active_graph is correct")
        results["passed"] += 1
    else:
        print(f"    ❌ Wrong default: {agent_config.active_graph}")
        results["failed"] += 1
    
    if "Coder" in agent_config.supervisor_members:
        print("    ✅ Supervisor members include Coder")
        results["passed"] += 1
    else:
        print("    ❌ Missing Coder in supervisor_members")
        results["failed"] += 1
    
    # Summary
    print("\n" + "=" * 50)
    total = results["passed"] + results["failed"]
    print(f"   RESULTS: {results['passed']}/{total} passed")
    if results["failed"] == 0:
        print("   STATUS: ✅ ALL TESTS PASSED")
    else:
        print(f"   STATUS: ⚠️ {results['failed']} TESTS FAILED")
    print("=" * 50)
    
    return results["failed"] == 0

if __name__ == "__main__":
    success = test_configuration_system()
    sys.exit(0 if success else 1)
