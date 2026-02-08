"""Unit test package marker for unittest discovery.

Keep tests runnable without requiring an editable install by adding `src/` to sys.path.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = str(_REPO_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
