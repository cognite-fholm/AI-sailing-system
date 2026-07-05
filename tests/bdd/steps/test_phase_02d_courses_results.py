"""Phase 2D — skipped until course and results services ship."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 2D courses and results not implemented")

scenarios("../features/phase_02d_courses_results.feature")
