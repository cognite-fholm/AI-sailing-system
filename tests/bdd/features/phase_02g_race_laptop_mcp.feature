@phase_02g
Feature: Phase 2G — Race laptop MCP
  Cursor on boat LAN queries live race state via race-mcp-gateway.
  See spec §7.18, FR-124–142, ADR-0012.

  Background:
    Given the race-mcp-gateway scaffold is present in the system repository

  Scenario: FR-124 MCP gateway package structure
    Then file "race-mcp-gateway/race_mcp_gateway/gateway.py" exists
    And file "race-mcp-gateway/race_mcp_gateway/servers/neo4j.py" exists
    And file "race-mcp-gateway/race_mcp_gateway/servers/influx.py" exists

  Scenario: FR-132 laptop setup documentation
    Then file "docs/race-laptop-mcp.md" exists
    And file "docs/mcp-neo4j-influx.md" exists

  Scenario: FR-141 combined MCP endpoint exposes Neo4j and Influx tools
    Given the SLA-2 stack is deployed with race-mcp-gateway running
    When I connect Cursor to the combined MCP endpoint on boat LAN
    Then Neo4j standing queries and bounded Flux tools are listed

  @wip
  Scenario: FR-129 authenticated read-only MCP access
    Given race-mcp-gateway is running with auth enabled
    When an unauthenticated client connects
    Then the connection is rejected

  @wip
  Scenario: FR-130 rate limits protect SLA-2 CPU
    Given race-mcp-gateway is running
    When an agent issues rapid ad hoc Flux queries
    Then requests beyond the configured rate limit receive HTTP 429
