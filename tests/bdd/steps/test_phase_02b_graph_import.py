"""Phase 2B — scaffold + live @wip scenarios."""

from pytest_bdd import scenarios

scenarios(
    "../features/phase_02b_graph_import.feature",
    "../features/phase_02b_graph_import_live.feature",
)
