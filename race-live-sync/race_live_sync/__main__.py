"""CLI entry: sync loop, once tick, or finalize."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import replace
from pathlib import Path

from race_live_sync.config import LiveSyncConfig
from race_live_sync.finalize import run_finalize
from race_live_sync.sync import main as sync_main
from race_live_sync.sync import run_tick


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="race-live-sync")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sync", help="Run continuous 5 min live sync loop (default)")
    once = sub.add_parser("once", help="Run a single live sync tick")
    once.add_argument("--race", dest="race_id", default="", help="Regatta id (optional)")
    fin = sub.add_parser("finalize", help="Write post-race archive and push to main")
    fin.add_argument("--race", dest="race_id", required=True, help="Regatta id")

    args = parser.parse_args(argv)
    command = args.command or "sync"

    if command == "sync":
        sync_main()
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config_path = Path(os.environ.get("DATA_REPO_CONFIG", "/config/data-repo.yaml"))
    if not config_path.is_file():
        print(f"Missing config: {config_path}", file=sys.stderr)
        sys.exit(1)
    config = LiveSyncConfig.from_yaml(config_path)
    if getattr(args, "race_id", ""):
        config = replace(config, regatta_id=args.race_id)

    if command == "once":
        result = run_tick(config)
        print(result)
        return

    if command == "finalize":
        result = run_finalize(config)
        print(result)
        if not result.get("finalized"):
            sys.exit(1)


if __name__ == "__main__":
    main()
