@phase_03 @wip
Feature: Phase 3 — SLA-3 GoPro sail vision
  Multi-camera capture, Coral preprocess, geometry, and grafana-sail.
  See spec §7.7, §7.9–7.11, FR-61–71, ADR-0003.

  Background:
    Given the SLA-3 docker compose stack is deployed
    And SLA-1 telemetry is available for alignment

  Scenario: FR-61 GoPro HERO13 fleet orchestration
    When gopro-orchestrator discovers configured cameras
    Then three to five HERO13 cameras are reachable via Open GoPro

  Scenario: FR-62 synchronized multi-camera burst
    When a capture burst is triggered
    Then still frames from all cameras fall within 200 milliseconds of each other

  Scenario: FR-65 geometry aligned to telemetry
    When sail-geometry processes a capture burst
    Then each result references SLA-1 telemetry within 100 milliseconds

  Scenario: FR-67 grafana-sail current versus best trim
    When a new SailGeometry result is published
    Then grafana-sail shows delta for boom heel and draft versus BestTrimSnapshot

  Scenario: FR-70 SLA-3 pause does not affect SLA-1 or SLA-2
    Given SLA-3 capture is paused
    When instruments and race services continue
    Then Signal K and live-results remain unaffected
