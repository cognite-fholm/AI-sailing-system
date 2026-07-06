"""Phase 1 — SLA-1 scaffold + live @wip scenarios."""

from pytest_bdd import scenarios

scenarios(
    "../features/phase_01_sla1_telemetry.feature",
    "../features/phase_01_sla1_telemetry_live.feature",
)
