"""Korean vocab trainer. Run: uv run python -m trainer [--deck path/to/deck.md] [--port N]"""

import argparse
from pathlib import Path

from trainer.paths import DEFAULT_DECK
from trainer.ui.trainer import run

if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", type=Path, default=DEFAULT_DECK)
    parser.add_argument("--port", type=int, default=8520)
    args = parser.parse_args()
    run(args.deck, args.port)
