import sys
from pathlib import Path


# Ensure src is on the path so tests can import the package using src layout
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
