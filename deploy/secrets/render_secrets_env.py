"""Render gitignored env file from on-device secret files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


REQUIRED_MAPPINGS = {
    "RACE_MCP_API_KEY": "race_mcp_api_key",
    "NEO4J_MCP_PASSWORD": "neo4j_mcp_password",
    "INFLUX_READ_TOKEN": "influx_read_token",
}


def _read_secret(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required secret file: {path}")
    return path.read_text(encoding="utf-8").strip()


def render_env_file(
    secrets_dir: Path, output_file: Path, *, overwrite: bool = False
) -> list[str]:
    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_file} (use --overwrite)"
        )

    lines = [
        "# Generated from on-device secret files.",
        "# Do not commit this file.",
    ]
    for env_name, secret_name in REQUIRED_MAPPINGS.items():
        value = _read_secret(secrets_dir / secret_name)
        lines.append(f"{env_name}={value}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render deploy/env/harbor.secrets.env from secret files."
    )
    parser.add_argument(
        "--secrets-dir",
        default=os.environ.get("AI_SAILING_SECRETS_DIR", "/opt/ai-sailing-system/secrets"),
        help="Directory containing runtime secret files.",
    )
    parser.add_argument(
        "--output",
        default="deploy/env/harbor.secrets.env",
        help="Output env file path.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it already exists.",
    )
    args = parser.parse_args()

    render_env_file(
        Path(args.secrets_dir), Path(args.output), overwrite=args.overwrite
    )
    print(f"OK: wrote {args.output} from secrets in {args.secrets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
