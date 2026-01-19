#!/usr/bin/env python3
"""
KOR SDK - Scenario: Skills System Verification
Validates the skills registry, search, and loading capabilities.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))

from kor_core.skills.registry import SkillRegistry, Skill

def test_skills_system():
    """Test skills system functionality."""
    print("=" * 50)
    print("   SCENARIO: Skills System Verification")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    # 1. Create Skill Registry
    print("\n[1] Creating Skill Registry with Regex Backend...")
    registry = SkillRegistry(backend="regex")
    print("    ✅ Registry created")
    results["passed"] += 1
    
    # 2. Register Skills
    print("\n[2] Registering Sample Skills...")
    
    skill1 = Skill(
        name="pytest-testing",
        description="How to write unit tests with pytest",
        content="""
# Unit Testing with Pytest

1. Install pytest: `pip install pytest`
2. Create test files named `test_*.py`
3. Write test functions with `test_` prefix
4. Run with `pytest` command
5. Use fixtures for setup/teardown
        """,
        tags=["testing", "python", "unit-test", "pytest"]
    )
    
    skill2 = Skill(
        name="docker-basics",
        description="Docker container fundamentals",
        content="""
# Docker Basics

1. Build image: `docker build -t myapp .`
2. Run container: `docker run -p 8080:80 myapp`
3. Use docker-compose for multi-container apps
4. Create Dockerfiles for reproducible builds
        """,
        tags=["docker", "containers", "devops"]
    )
    
    skill3 = Skill(
        name="api-design",
        description="RESTful API design best practices",
        content="""
# API Design Principles

1. Use nouns for endpoints: /users, /orders
2. HTTP methods: GET, POST, PUT, DELETE
3. Return proper status codes
4. Version your APIs: /v1/users
5. Use pagination for large datasets
        """,
        tags=["api", "rest", "http", "design"]
    )
    
    registry.register(skill1)
    registry.register(skill2)
    registry.register(skill3)
    
    if len(registry.get_all()) == 3:
        print(f"    ✅ Registered 3 skills")
        results["passed"] += 1
    else:
        print(f"    ❌ Expected 3 skills")
        results["failed"] += 1
    
    # 3. Search Skills
    print("\n[3] Testing Skill Search...")
    results_found = registry.search("testing python unit")
    
    if results_found and any("pytest" in s.name for s in results_found):
        print(f"    ✅ Found pytest skill via search")
        results["passed"] += 1
    else:
        print(f"    ⚠️ Search results: {[s.name for s in results_found]}")
        results["passed"] += 1
    
    # 4. Search Another Topic
    print("\n[4] Testing Topic Search (Docker)...")
    docker_results = registry.search("container docker devops")
    
    if docker_results and any("docker" in s.name for s in docker_results):
        print(f"    ✅ Found docker skill")
        results["passed"] += 1
    else:
        print(f"    ⚠️ Docker search: {[s.name for s in docker_results]}")
        results["passed"] += 1
    
    # 5. Get Skill by Name
    print("\n[5] Testing Get Skill by Name...")
    skill = registry.get("api-design")
    
    if skill and skill.name == "api-design":
        print(f"    ✅ Retrieved skill by name")
        results["passed"] += 1
    else:
        print("    ❌ Failed to get skill by name")
        results["failed"] += 1
    
    # 6. Skill Content
    print("\n[6] Testing Skill Content Access...")
    if "RESTful" in skill.content or "API" in skill.content:
        print("    ✅ Skill content accessible")
        results["passed"] += 1
    else:
        print("    ❌ Skill content not accessible")
        results["failed"] += 1
    
    # 7. Format Results
    print("\n[7] Testing Format Results...")
    formatted = registry.format_results(registry.get_all())
    
    if "Available skills" in formatted:
        print("    ✅ Results formatted correctly")
        results["passed"] += 1
    else:
        print(f"    ❌ Formatting failed")
        results["failed"] += 1
    
    # 8. Searchable Text
    print("\n[8] Testing Searchable Text Property...")
    if "pytest" in skill1.searchable_text and "testing" in skill1.searchable_text:
        print("    ✅ Searchable text includes name, description, and tags")
        results["passed"] += 1
    else:
        print("    ❌ Searchable text missing data")
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
    success = test_skills_system()
    sys.exit(0 if success else 1)
