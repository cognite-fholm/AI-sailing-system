"""Phase 2E — skipped until race UX dashboards ship."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 2E race UX not implemented")

scenarios("../features/phase_02e_race_ux.feature")
