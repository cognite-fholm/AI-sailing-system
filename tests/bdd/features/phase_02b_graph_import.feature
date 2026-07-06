@phase_02b
Feature: Phase 2B — Graph import and sync (scaffold)
  Neo4j import services and sync contract from AI-sailing-data.
  Live Neo4j scenarios: phase_02b_graph_import_live.feature (@wip).
  See spec §7.3, §7.15, FR-102–104, ADR-0009.

  Background:
    Given the AI Sailing System repository is checked out

  Scenario: SLA-2 compose includes graph import services
    Then file "docker-compose.sla-2.yml" contains service "neo4j"
    And file "docker-compose.sla-2.yml" contains service "race-import"
    And file "docker-compose.sla-2.yml" contains service "race-data-sync"

  Scenario: FR-104 race-import HTTP API is defined
    Then file "race-import/race_import/api.py" exists
    And race-import exposes route "/health"
    And race-import exposes route "/import"

  Scenario: FR-104 declarative importer module exists
    Then file "race-import/race_import/importer.py" exists

  Scenario: FR-103 race-data-sync service exists
    Then file "race-data-sync/race_data_sync/sync.py" exists
    And file "config/data-repo.yaml" exists
