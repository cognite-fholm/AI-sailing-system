@phase_02d @wip
Feature: Phase 2D — Courses, handicaps, and live results
  SI course parsing, waypoint editing, scoring, and corrected-time standings.
  See spec §7.13–7.14, FR-27–41, ADR-0005, ADR-0006.

  Background:
    Given Phase 2C GRIB and polar services are running
    And course YAML exists for the target regatta

  Scenario: FR-28 course-parser extracts routes from SI PDF
    Given the Færderseilasen SI PDF chapter 11
    When course-parser runs
    Then CourseCatalog YAML contains multiple course variants

  Scenario: FR-29 Norwegian coordinate format parsing
    When a waypoint line contains "N59°52,50' Ø010°38,76'"
    Then the parser stores WGS-84 latitude 59.875 and longitude 10.646

  Scenario: FR-30 course-editor for missing coordinates
    When I open course-editor on port 3010
    Then I can drag waypoints without coordinates onto the chart

  Scenario: FR-31 live corrected-time standings
    Given an active race session with handicaps loaded
    When competitors round marks tracked by AIS
    Then live-results ranks boats by elapsed time multiplied by handicap

  Scenario: FR-37 start-boat course signal mapping
    When the start boat displays course numeral 2
    Then the system maps StartBoatSignal to the configured CourseRoute Bane B

  Scenario: FR-39 user confirms active course at start
    When the crew confirms the active course in course-editor
    Then a CourseSelection node is stored in Neo4j
