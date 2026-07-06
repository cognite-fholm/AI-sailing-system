"""Phase 2C — scaffold + live @wip scenarios."""

from pytest_bdd import scenarios

scenarios(
    "../features/phase_02c_grib_polars_ais.feature",
    "../features/phase_02c_grib_polars_ais_live.feature",
)
