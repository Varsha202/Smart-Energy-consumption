"""Backend test suite package."""
import sys
from pathlib import Path

# Ensure project root is in sys.path so tests can be run from root or backend/
_root_dir = Path(__file__).resolve().parent.parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
