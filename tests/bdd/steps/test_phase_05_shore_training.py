"""Phase 5 — skipped until shore training pipeline ships."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 5 shore training not implemented")

scenarios("../features/phase_05_shore_training.feature")
