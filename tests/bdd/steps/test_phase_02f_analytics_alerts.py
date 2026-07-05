"""Phase 2F — skipped until fleet analytics and alerts ship."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 2F analytics and alerts not implemented")

scenarios("../features/phase_02f_analytics_alerts.feature")
