"""CLI entry for config-driven cell-cluster biovalidation."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_RLS = _REPO / "response_latent_space"
if str(_RLS) not in sys.path:
    sys.path.insert(0, str(_RLS))

from src.biovalidate_cell_clusters import main  # noqa: E402

if __name__ == "__main__":
    main()
