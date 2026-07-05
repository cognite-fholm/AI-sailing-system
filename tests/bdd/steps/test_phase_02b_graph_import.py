"""Phase 2B — skipped until Neo4j import ships."""

import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.skip(reason="Phase 2B graph import not implemented")

scenarios("../features/phase_02b_graph_import.feature")
