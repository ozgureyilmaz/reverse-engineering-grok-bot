"""Regenerate data/ and figures/ from the redacted transcripts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze import write_outputs
from figures import draw_all
from receipts import load_runs


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    runs = load_runs(root / "evidence" / "transcripts")
    stats = write_outputs(runs, root / "data")
    draw_all(root)
    print(
        f"rebuilt {stats['shopping_runs']} shopping replies, "
        f"{stats['shopping_product_rows']} products"
    )


if __name__ == "__main__":
    main()
