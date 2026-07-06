"""Phase 4 — CI/CD scaffold + live @wip scenarios."""

from pytest_bdd import scenarios

scenarios(
    "../features/phase_04_cicd.feature",
    "../features/phase_04_cicd_live.feature",
)
