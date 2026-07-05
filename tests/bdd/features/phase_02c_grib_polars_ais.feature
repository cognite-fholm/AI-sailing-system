@phase_02c @wip
Feature: Phase 2C — GRIB, polars, AIS, and wind-on-course
  Fleet environmental context and polar targets for tactical analysis.
  See spec §7.12, FR-15–26, ADR-0004.

  Background:
    Given Phase 2B graph import is complete
    And the SLA-2 stack is running

  Scenario: FR-15 AIS fleet positions from Signal K
    When competitors are visible on AIS
    Then ais-collector stores MMSI COG SOG and position in Neo4j and ais_tracks bucket

  Scenario: FR-17 GRIB refresh when online
    Given ONLINE_MODE is true
    When six hours elapse since the last GRIB fetch
    Then grib-ingest downloads a new GRIB file into grib-store

  Scenario: FR-18 GRIB usable offline with staleness warning
    Given internet is unavailable
    And a GRIB file exists from the last harbor sync
    When the race session starts with GRIB older than 12 hours
    Then the crew sees a staleness warning on grafana-race

  Scenario: FR-19 Own-boat polar from SLK file
    When polar-manager loads the configured SLK polar file
    Then target BSP and VMG are available for the current TWS and TWA

  Scenario: FR-24 Wind advantage map updates during the race
    Given an active race session with GRIB and AIS data
    When 60 seconds elapse on the race leg
    Then wind-field-analyzer refreshes WindAdvantageZone scores
    And grafana-race shows a heatmap recommendation
