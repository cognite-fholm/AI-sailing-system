"""Phase 4 — skipped until CI/CD compose files ship."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 4 CI/CD not implemented")

scenarios("../features/phase_04_cicd.feature")
