import sys
from pathlib import Path

V2 = Path(__file__).resolve().parents[1]
REPO = V2.parent
sys.path.insert(0, str(V2 / "src"))
sys.path.insert(0, str(REPO / "code"))
