#!/usr/bin/env python3
"""Sync config/data-repo.yaml active section from AI-sailing-data index.yaml."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync active race context from index.yaml")
    parser.add_argument("--config", type=Path, default=Path("/config/data-repo.yaml"))
    parser.add_argument("--data-repo", type=Path, default=Path("/opt/ai-sailing-data"))
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    index_path = args.data_repo / config.get("active", {}).get("index_file", "index.yaml")
    if not index_path.is_file():
        raise SystemExit(f"Missing index: {index_path}")

    index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    spec = index.get("spec", {})
    active = spec.get("active", {})
    regatta_id = active.get("regatta_id")
    if not regatta_id:
        raise SystemExit("index.yaml has no spec.active.regatta_id")

    race_entry = next((r for r in spec.get("races", []) if r.get("id") == regatta_id), None)
    if not race_entry:
        raise SystemExit(f"No races[] entry for {regatta_id}")

    own_boat = spec.get("own_boat_sail_number", "")
    boat = next((b for b in spec.get("boats", []) if b.get("sail_number") == own_boat), {})

    config.setdefault("active", {})
    config["active"].update(
        {
            "regatta_id": regatta_id,
            "race_path": race_entry.get("path"),
            "own_boat_path": f"boats/{own_boat}" if own_boat else config["active"].get("own_boat_path"),
            "active_certificate_ref": boat.get("active_certificate_ref"),
        }
    )

    args.config.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    print(f"Synced active context → regatta_id={regatta_id} path={race_entry.get('path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
