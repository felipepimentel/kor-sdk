import pytest
import sys
from pathlib import Path

# Add packages to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "kor-core" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "kor-cli" / "src"))
