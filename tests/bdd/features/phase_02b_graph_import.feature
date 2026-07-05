@phase_02b @wip
Feature: Phase 2B — Graph import and sync
  Neo4j schema and declarative import from AI-sailing-data.
  See spec §7.3, §7.15, FR-102–104, ADR-0009.

  Background:
    Given the SLA-2 docker compose stack is deployed
    And Neo4j is reachable on the race node
    And AI-sailing-data is mounted for import

  Scenario: FR-104 race-import applies declarative YAML without clobbering runtime nodes
    Given race-import manifest from the data repo for an active regatta
    When race-import runs
    Then Neo4j contains Vessel Polar and Waypoint nodes from the manifest
    And runtime-only nodes such as InsightAlert are preserved

  Scenario: FR-103 race-data-sync pulls newer data from GitHub
    Given a newer commit exists on the data repo remote
    When race-data-sync runs with sync policy enabled
    Then the local data repo checkout matches the remote ref

  Scenario: Neo4j core schema labels exist
    When I query Neo4j for schema labels
    Then labels include Vessel Polar GribModel Waypoint and HandicapRating
