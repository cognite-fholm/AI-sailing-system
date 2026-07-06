@phase_04
Feature: Phase 4 — CI/CD (scaffold)
  Compose files and publish workflows per spec §9 and ADR-0008.
  Live release/harbor scenarios: phase_04_cicd_live.feature (@wip).

  Background:
    Given the AI Sailing System repository is checked out

  Scenario: FR-94 per-tier docker compose files
    Then file "docker-compose.sla-1.yml" exists
    And file "docker-compose.sla-2.yml" exists
    And file "docker-compose.harbor.yml" exists

  Scenario: Publish workflows exist for SLA-1 and SLA-2 images
    Then file ".github/workflows/publish-sla-1.yml" exists
    And file ".github/workflows/publish-sla-1.yml" contains service "signalk-server"
    And file ".github/workflows/publish-sla-2.yml" exists
    And file ".github/workflows/publish-sla-2.yml" contains service "polar-manager"

  Scenario: CI validates compose and runs acceptance tests
    Then file ".github/workflows/ci.yml" exists
