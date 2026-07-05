"""Phase 1 — skipped until SLA-1 stack is implemented."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 1 SLA-1 telemetry not implemented")

scenarios("../features/phase_01_sla1_telemetry.feature")
