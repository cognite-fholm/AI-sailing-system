"""Validate required runtime secrets on a Raspberry Pi host."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path


def _mode_too_open(path: Path) -> bool:
    if os.name == "nt":
        # Windows ACL semantics differ from POSIX chmod bits.
        # Keep CI tests portable and enforce strict mode checks on Pi/Linux.
        return False
    mode = path.stat().st_mode
    disallowed = stat.S_IRWXG | stat.S_IRWXO
    return bool(mode & disallowed)


def _check_file(path: Path, *, must_exist: bool = True) -> list[str]:
    errors: list[str] = []
    if must_exist and not path.is_file():
        errors.append(f"Missing required secret file: {path}")
        return errors
    if not path.exists():
        return errors
    if _mode_too_open(path):
        errors.append(f"Secret file permissions too open (expected 600): {path}")
    return errors


def validate(secrets_dir: Path, *, require_rms: bool) -> list[str]:
    errors: list[str] = []
    if not secrets_dir.is_dir():
        return [f"Secrets directory does not exist: {secrets_dir}"]

    if _mode_too_open(secrets_dir):
        errors.append(
            f"Secrets directory permissions too open (expected 700): {secrets_dir}"
        )

    required = [
        "github_token",
        "race_mcp_api_key",
        "neo4j_mcp_password",
        "influx_read_token",
    ]
    if require_rms:
        required.append("rms_client.ovpn")

    for name in required:
        errors.extend(_check_file(secrets_dir / name, must_exist=True))

    # Optional files should still be private if present.
    for name in ("rms_auth_user", "rms_auth_password"):
        errors.extend(_check_file(secrets_dir / name, must_exist=False))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate on-device secret files for AI-sailing-system."
    )
    parser.add_argument(
        "--secrets-dir",
        default=os.environ.get("AI_SAILING_SECRETS_DIR", "/opt/ai-sailing-system/secrets"),
        help="Directory containing runtime secret files.",
    )
    parser.add_argument(
        "--require-rms",
        action="store_true",
        help="Require RMS OpenVPN profile (rms_client.ovpn).",
    )
    args = parser.parse_args()

    errors = validate(Path(args.secrets_dir), require_rms=args.require_rms)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print(f"OK: secrets validated in {args.secrets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
