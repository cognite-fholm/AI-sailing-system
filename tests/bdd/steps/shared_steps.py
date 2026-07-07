"""Reusable Gherkin step definitions."""

from __future__ import annotations

import re
from pathlib import Path

from pytest_bdd import given, parsers, then, when

from tests.bdd.steps.common import require_data_repo


@given("the AI Sailing System repository is checked out")
def ai_sailing_system_repository_is_checked_out(repo_root: Path) -> None:
    assert (repo_root / "spec.md").is_file()


@given("the AI-sailing-data repository is available")
def ai_sailing_data_repository_is_available(data_repo_root: Path | None) -> None:
    require_data_repo(data_repo_root)


@given("the race-mcp-gateway scaffold is present in the system repository")
def race_mcp_gateway_scaffold_present(repo_root: Path) -> None:
    assert (repo_root / "race-mcp-gateway" / "race_mcp_gateway" / "gateway.py").is_file()


@then(parsers.parse('file "{path}" exists'))
def file_exists(repo_root: Path, path: str) -> None:
    assert (repo_root / path).is_file(), f"Missing file: {path}"


@given(parsers.parse('the file "{path}" exists in the system repo'))
def given_file_exists_in_system_repo(repo_root: Path, path: str) -> None:
    assert (repo_root / path).is_file(), f"Missing file: {path}"


@then(parsers.parse('the file "{path}" contains "{text}"'))
def file_contains_text(repo_root: Path, path: str, text: str) -> None:
    content = (repo_root / path).read_text(encoding="utf-8")
    assert text in content, f"{text!r} not found in {path}"


@then(parsers.parse('file "{path}" exists in the data repo'))
def file_exists_in_data_repo(data_repo_root: Path | None, path: str) -> None:
    require_data_repo(data_repo_root)
    assert (data_repo_root / path).is_file(), f"Missing file in data repo: {path}"


@then(parsers.parse('directory "{path}" exists'))
def directory_exists(repo_root: Path, path: str) -> None:
    assert (repo_root / path).is_dir(), f"Missing directory: {path}"


@then(parsers.parse('directory "{path}" exists in the data repo'))
def directory_exists_in_data_repo(data_repo_root: Path | None, path: str) -> None:
    require_data_repo(data_repo_root)
    assert (data_repo_root / path).is_dir(), f"Missing directory in data repo: {path}"


@then(parsers.parse('spec.md exists with version at least "{min_version}"'))
def spec_version_at_least(repo_root: Path, min_version: str) -> None:
    text = (repo_root / "spec.md").read_text(encoding="utf-8")
    match = re.search(r"\*\*Version:\*\*\s*([\d.]+(?:-draft)?)", text)
    assert match, "spec.md has no Version field"
    actual = match.group(1)

    def parse_version(value: str) -> tuple[int, ...]:
        core = value.replace("-draft", "")
        return tuple(int(part) for part in core.split("."))

    assert parse_version(actual) >= parse_version(min_version), (
        f"spec version {actual} < {min_version}"
    )


@then(parsers.parse('spec.md contains section "{heading}"'))
def spec_contains_section(repo_root: Path, heading: str) -> None:
    text = (repo_root / "spec.md").read_text(encoding="utf-8")
    pattern = rf"^#{{2,3}}\s+{re.escape(heading)}\s*$"
    assert re.search(pattern, text, re.MULTILINE), f"Section not found: {heading}"


@then("adr/README.md exists with implementation order section")
def adr_readme_implementation_order(repo_root: Path) -> None:
    readme = (repo_root / "adr" / "README.md").read_text(encoding="utf-8")
    assert "## Implementation order" in readme


@then(parsers.parse('accepted ADR files exist from "{first}" through "{last}"'))
def adr_files_exist(repo_root: Path, first: str, last: str) -> None:
    start = int(first)
    end = int(last)
    adr_dir = repo_root / "adr"
    for number in range(start, end + 1):
        if number == 7:
            continue
        matches = list(adr_dir.glob(f"{number:04d}-*.md"))
        assert matches, f"Missing ADR {number:04d}"


@then(parsers.parse('docs/ARCHITECTURE.md references spec version "{version}"'))
def architecture_references_spec_version(repo_root: Path, version: str) -> None:
    text = (repo_root / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert version in text


@then("spec.md documents AI-sailing-data as the race content repository")
def spec_documents_data_repo(repo_root: Path) -> None:
    text = (repo_root / "spec.md").read_text(encoding="utf-8")
    assert "AI-sailing-data" in text


@then("collected-sources.yaml in the data repo registers orc_sailor_services")
def collected_sources_orc(data_repo_root: Path | None) -> None:
    require_data_repo(data_repo_root)
    paths = list(data_repo_root.rglob("collected-sources.yaml"))
    assert paths, "collected-sources.yaml not found in data repo"
    text = paths[0].read_text(encoding="utf-8")
    assert "orc_sailor_services" in text


@given("a race folder with resolved course waypoints in the data repo")
def race_with_resolved_waypoints(data_repo_root: Path | None) -> None:
    require_data_repo(data_repo_root)
    gpx_dirs = list(data_repo_root.rglob("export/marine-map"))
    assert gpx_dirs, "No export/marine-map folder found — run marine-map export on a race"


@when("the marine-map-gpx-export skill is run")
def marine_map_skill_run() -> None:
    pass  # Validated by Then step on existing artifacts


@then("export/marine-map contains Route GPX files and a MarineMapExport manifest")
def marine_map_export_artifacts(data_repo_root: Path | None) -> None:
    require_data_repo(data_repo_root)
    export_dirs = list(data_repo_root.rglob("export/marine-map"))
    assert export_dirs, "No marine-map export directory"
    export_dir = export_dirs[0]
    gpx_files = list(export_dir.glob("Route*.gpx")) + list(export_dir.glob("**/Route*.gpx"))
    manifests = list(export_dir.glob("manifest.yaml"))
    assert gpx_files, "No Route*.gpx files in export/marine-map"
    assert manifests, "No manifest.yaml in export/marine-map"


@then("at least one race has planning/prep-status.yaml in the data repo")
def prep_status_exists(data_repo_root: Path | None) -> None:
    require_data_repo(data_repo_root)
    matches = list(data_repo_root.rglob("planning/prep-status.yaml"))
    assert matches, "No planning/prep-status.yaml found in data repo"
