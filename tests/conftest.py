# Pytest bootstrap: add project root to sys.path so `src` imports resolve.
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))