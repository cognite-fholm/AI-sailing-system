"""Parse ORC 7710-target-speeds.txt into an interpolating grid."""

from __future__ import annotations

import logging
import math
from pathlib import Path

from polar_manager.models import PolarGrid, PolarPoint, PolarRow, TargetResponse

logger = logging.getLogger(__name__)


def parse_target_speeds(path: Path, vessel_id: str, certificate_ref: str) -> PolarGrid:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise ValueError(f"Empty polar file: {path}")
    rows: list[PolarRow] = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 5:
            continue
        tws = float(parts[0])
        pairs = parts[3:]
        points: list[PolarPoint] = []
        for idx in range(0, len(pairs) - 1, 2):
            twa = float(pairs[idx])
            bsp = float(pairs[idx + 1])
            points.append(PolarPoint(twa=twa, bsp=bsp))
        if points:
            rows.append(PolarRow(tws=tws, points=points))
    if not rows:
        raise ValueError(f"No polar rows parsed from {path}")
    logger.info("Loaded polar grid vessel=%s rows=%s from %s", vessel_id, len(rows), path.name)
    return PolarGrid(
        vessel_id=vessel_id,
        certificate_ref=certificate_ref,
        source_file=str(path),
        rows=rows,
    )


def _interpolate_row(row: PolarRow, twa: float) -> float:
    points = sorted(row.points, key=lambda p: p.twa)
    if twa <= points[0].twa:
        return points[0].bsp
    if twa >= points[-1].twa:
        return points[-1].bsp
    for left, right in zip(points, points[1:]):
        if left.twa <= twa <= right.twa:
            span = right.twa - left.twa
            if span <= 0:
                return left.bsp
            ratio = (twa - left.twa) / span
            return left.bsp + ratio * (right.bsp - left.bsp)
    return points[-1].bsp


def _interpolate_tws(grid: PolarGrid, tws: float, twa: float) -> float:
    rows = sorted(grid.rows, key=lambda r: r.tws)
    if tws <= rows[0].tws:
        return _interpolate_row(rows[0], twa)
    if tws >= rows[-1].tws:
        return _interpolate_row(rows[-1], twa)
    for low, high in zip(rows, rows[1:]):
        if low.tws <= tws <= high.tws:
            span = high.tws - low.tws
            if span <= 0:
                return _interpolate_row(low, twa)
            ratio = (tws - low.tws) / span
            low_bsp = _interpolate_row(low, twa)
            high_bsp = _interpolate_row(high, twa)
            return low_bsp + ratio * (high_bsp - low_bsp)
    return _interpolate_row(rows[-1], twa)


def _optimum_angle(row: PolarRow, upwind: bool) -> float:
    best_twa = row.points[0].twa
    best_vmg = -1.0
    for point in row.points:
        rad = math.radians(point.twa)
        vmg = point.bsp * math.cos(rad)
        if upwind:
            if point.twa >= 90:
                continue
            score = vmg
        else:
            if point.twa <= 90:
                continue
            score = point.bsp * math.cos(math.pi - rad)
        if score > best_vmg:
            best_vmg = score
            best_twa = point.twa
    return best_twa


def _nearest_row(grid: PolarGrid, tws: float) -> PolarRow:
    return min(grid.rows, key=lambda row: abs(row.tws - tws))


def target_at(grid: PolarGrid, tws: float, twa: float) -> TargetResponse:
    tws = max(0.0, tws)
    twa = abs(twa) % 360
    if twa > 180:
        twa = 360 - twa
    target_bsp = _interpolate_tws(grid, tws, twa)
    row = _nearest_row(grid, tws)
    return TargetResponse(
        vessel_id=grid.vessel_id,
        tws=tws,
        twa=twa,
        target_bsp=round(target_bsp, 3),
        target_angle_upwind=round(_optimum_angle(row, upwind=True), 2),
        target_angle_downwind=round(_optimum_angle(row, upwind=False), 2),
    )
