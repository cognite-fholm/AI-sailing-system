"""Phase 3 — skipped until SLA-3 vision stack ships."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 3 SLA-3 vision not implemented")

scenarios("../features/phase_03_sla3_vision.feature")
