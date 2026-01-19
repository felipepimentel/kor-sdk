#!/usr/bin/env python3
"""
KOR SDK - Complete Test Suite Runner
Runs all scenario tests and produces a comprehensive report.

Usage:
    python examples/scenarios/run_all_scenarios.py
"""
import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Test scenarios to run
SCENARIOS = [
    # Core Components
    ("Plugin System", "test_plugin_system.py"),
    ("Configuration", "test_configuration.py"),
    ("Tool Registry", "test_tool_registry.py"),
    ("File Tools", "test_file_tools.py"),
    ("Hook System", "test_hook_system.py"),
    ("Agent Factory", "test_agent_factory.py"),
    
    # Advanced Features
    ("Skills System", "test_skills_system.py"),
    ("Validation System", "test_validation_system.py"),
    ("Code Graph", "test_code_graph.py"),
    ("Multi-Agent", "test_multi_agent.py"),
    ("LLM System", "test_llm_system.py"),
    ("Persistence", "test_persistence.py"),
]

def run_scenario(name: str, script: str, scenarios_dir: Path) -> dict:
    """Run a single scenario and return results."""
    script_path = scenarios_dir / script
    
    if not script_path.exists():
        return {
            "name": name,
            "status": "SKIPPED",
            "message": f"Script not found: {script}",
            "duration": 0
        }
    
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(Path.cwd())
        )
        duration = time.time() - start
        
        return {
            "name": name,
            "status": "PASSED" if result.returncode == 0 else "FAILED",
            "output": result.stdout,
            "error": result.stderr,
            "duration": duration
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "status": "TIMEOUT",
            "message": "Test exceeded 60 second limit",
            "duration": 60
        }
    except Exception as e:
        return {
            "name": name,
            "status": "ERROR",
            "message": str(e),
            "duration": time.time() - start
        }

def print_header():
    """Print test suite header."""
    print("\n" + "=" * 60)
    print("  ██╗  ██╗ ██████╗ ██████╗     ███████╗██████╗ ██╗  ██╗")
    print("  ██║ ██╔╝██╔═══██╗██╔══██╗    ██╔════╝██╔══██╗██║ ██╔╝")
    print("  █████╔╝ ██║   ██║██████╔╝    ███████╗██║  ██║█████╔╝ ")
    print("  ██╔═██╗ ██║   ██║██╔══██╗    ╚════██║██║  ██║██╔═██╗ ")
    print("  ██║  ██╗╚██████╔╝██║  ██║    ███████║██████╔╝██║  ██╗")
    print("  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝    ╚══════╝╚═════╝ ╚═╝  ╚═╝")
    print()
    print("           COMPLETE TEST SUITE RUNNER")
    print("=" * 60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def print_summary(results: list):
    """Print test summary."""
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    errors = sum(1 for r in results if r["status"] in ("ERROR", "TIMEOUT"))
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    total = len(results)
    total_time = sum(r["duration"] for r in results)
    
    print("\n" + "=" * 60)
    print("                    TEST SUMMARY")
    print("=" * 60)
    print()
    
    # Results table
    for r in results:
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌",
            "ERROR": "💥",
            "TIMEOUT": "⏰",
            "SKIPPED": "⏭️"
        }.get(r["status"], "?")
        
        print(f"  {status_icon} {r['name']:<25} {r['status']:<10} ({r['duration']:.2f}s)")
    
    print()
    print("-" * 60)
    print(f"  Total:    {total} scenarios")
    print(f"  Passed:   {passed} ✅")
    print(f"  Failed:   {failed} ❌")
    print(f"  Errors:   {errors} 💥")
    print(f"  Skipped:  {skipped} ⏭️")
    print(f"  Duration: {total_time:.2f}s")
    print("-" * 60)
    
    if failed == 0 and errors == 0:
        print()
        print("  🎉 ALL TESTS PASSED! SDK IS READY FOR USE 🎉")
    else:
        print()
        print("  ⚠️  SOME TESTS FAILED. Review output above.")
    
    print("=" * 60)
    
    return failed == 0 and errors == 0

def main():
    """Run all scenarios."""
    print_header()
    
    scenarios_dir = Path(__file__).parent
    results = []
    
    for name, script in SCENARIOS:
        print(f"\n▶️  Running: {name}...")
        result = run_scenario(name, script, scenarios_dir)
        results.append(result)
        
        # Show brief status
        if result["status"] == "PASSED":
            print(f"   ✅ {name}: PASSED ({result['duration']:.2f}s)")
        elif result["status"] == "FAILED":
            print(f"   ❌ {name}: FAILED ({result['duration']:.2f}s)")
            if "error" in result and result["error"]:
                # Show first few lines of error
                error_lines = result["error"].strip().split("\n")[-5:]
                for line in error_lines:
                    print(f"      {line}")
        else:
            print(f"   ⚠️  {name}: {result['status']}")
    
    all_passed = print_summary(results)
    
    # Write report to file
    report_path = scenarios_dir / "test_report.txt"
    with open(report_path, "w") as f:
        f.write(f"KOR SDK Test Report - {datetime.now()}\n")
        f.write("=" * 60 + "\n\n")
        
        for r in results:
            f.write(f"{r['name']}: {r['status']} ({r['duration']:.2f}s)\n")
            if "output" in r:
                f.write(r["output"] + "\n")
            if "error" in r and r["error"]:
                f.write("STDERR:\n" + r["error"] + "\n")
            f.write("-" * 40 + "\n")
    
    print(f"\n📄 Full report saved to: {report_path}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
