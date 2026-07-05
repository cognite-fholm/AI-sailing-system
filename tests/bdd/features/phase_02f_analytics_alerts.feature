@phase_02f @wip
Feature: Phase 2F — Fleet analytics and tactical alerts
  Fleet polar performance timeline, insight alerts, and optional coach.
  See spec §7.21–7.22, §7.5, FR-80–85, FR-150–172, ADR-0015, ADR-0016.

  Background:
    Given Phase 2E race UX is running
    And fleet-performance-tracker and insight-alerts are deployed on SLA-2

  Scenario: FR-162 fleet polar performance sampling
    Given an active race_id with roster vessels and polars loaded
    When 30 seconds elapse during the leg
    Then fleet-performance-tracker writes fleet_polar_performance to Influx race bucket

  Scenario: FR-166 handicap tags on fleet polar points
    When a fleet polar performance point is written
    Then fields include polar_percent vmg_percent and tags handicap_type and handicap_value

  Scenario: FR-150 tactical insight alert evaluation
    When live-results emits a fleet_position InsightEvent
    Then insight-alerts raises an alert matching InsightAlertProfile rules

  Scenario: FR-152 alert feed on grafana-race
    When an active tactical alert exists
    Then the grafana-race alert feed panel shows message_short and severity

  Scenario: FR-154 optional TTS annunciation
    Given channels.tts.enabled is true and a speaker is connected
    When a high-severity insight alert fires
    Then Piper or espeak-ng reads message_short on the helm speaker

  Scenario: FR-80 tactical coach responds within 30 seconds
    When the crew asks a tactical question via the coach API
    Then tactical-coach returns an answer within 30 seconds using OKF and race graph context
