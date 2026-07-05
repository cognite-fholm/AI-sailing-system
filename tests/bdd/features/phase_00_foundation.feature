@phase_00
Feature: Phase 0 — Foundation
  Specification, ADRs, dual-repo model, and deploy scaffolding must exist before runtime work.
  See spec §1.1 Phase 0 and ADR-0001, 0002, 0008, 0009.

  Background:
    Given the AI Sailing System repository is checked out

  Scenario: Specification and implementation map are published
    Then spec.md exists with version at least "0.18.0-draft"
    And spec.md contains section "1.1 Implementation map"
    And spec.md contains section "7.0 Implementation order — section index"
    And spec.md contains section "14. Implementation phases"

  Scenario: ADR index covers all accepted decisions through ADR-0017
    Then adr/README.md exists with implementation order section
    And accepted ADR files exist from "0001" through "0017"

  Scenario: Architecture documentation is linked from the spec
    Then file "docs/ARCHITECTURE.md" exists
    And docs/ARCHITECTURE.md references spec version "0.18"

  Scenario: Deploy and harbor scaffolding is present
    Then file "scripts/harbor-pull.sh" exists
    And file "scripts/harbor-sync.sh" exists
    And file "deploy/env/race.env.example" exists
    And file ".github/workflows/release.yml" exists

  Scenario: Dual-repository contract is documented
    Then spec.md documents AI-sailing-data as the race content repository
    And file "config/data-repo.yaml" exists

  Scenario: Race MCP gateway scaffold exists for Phase 2G
    Then directory "race-mcp-gateway" exists
    And file "race-mcp-gateway/race_mcp_gateway/gateway.py" exists
    And file "docs/race-laptop-mcp.md" exists
