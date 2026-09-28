"""Makes `freep_pipeline` (under src/) and `config` (at the repo root)
importable without an editable install, for pytest runs."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
