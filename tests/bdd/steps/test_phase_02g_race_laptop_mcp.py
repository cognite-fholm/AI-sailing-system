"""Phase 2G race laptop MCP — scaffold and documentation tests."""

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.bdd.steps.common import skip_phase

scenarios("../features/phase_02g_race_laptop_mcp.feature")


@given("the SLA-2 stack is deployed with race-mcp-gateway running")
def sla2_with_mcp() -> None:
    skip_phase("2G", "deploy race-mcp-gateway on SLA-2")


@when("I connect Cursor to the combined MCP endpoint on boat LAN")
def connect_cursor_mcp() -> None:
    skip_phase("2G", "live MCP connection")


@then("Neo4j standing queries and bounded Flux tools are listed")
def mcp_tools_listed() -> None:
    skip_phase("2G", "live MCP tool listing")


@given("race-mcp-gateway is running with auth enabled")
def mcp_with_auth() -> None:
    skip_phase("2G", "auth-enabled gateway")


@when("an unauthenticated client connects")
def unauthenticated_client() -> None:
    skip_phase("2G")


@then("the connection is rejected")
def connection_rejected() -> None:
    skip_phase("2G")


@given("race-mcp-gateway is running")
def mcp_running() -> None:
    skip_phase("2G", "running gateway")


@when("an agent issues rapid ad hoc Flux queries")
def rapid_flux_queries() -> None:
    skip_phase("2G")


@then("requests beyond the configured rate limit receive HTTP 429")
def rate_limit_429() -> None:
    skip_phase("2G")
