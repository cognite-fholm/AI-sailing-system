"""Phase 2C — skipped until GRIB/polar/AIS services ship."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 2C GRIB polars AIS not implemented")

scenarios("../features/phase_02c_grib_polars_ais.feature")
