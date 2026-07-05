@phase_02e @wip
Feature: Phase 2E — Race UX (iRegatta and H5000 parity)
  Grafana race dashboards and race-intelligence service matching reference UX.
  See spec §7.6, §7.16–7.17, FR-42–59, FR-107–123, ADR-0010, ADR-0011.

  Background:
    Given Phase 2D courses and live results are running
    And grafana-race is provisioned

  Scenario: FR-42 iRegatta-style configurable instrument readouts
    When I open the race dashboard
    Then panels show SOG COG VMG wind DTM and performance percent

  Scenario: FR-48 layline overlay when navigating
    Given an active waypoint on the course
    When navigating toward the mark
    Then the map panel shows port and starboard laylines

  Scenario: FR-50 start line geometry and favored end
    Given start line pin and committee boat ends are configured
    When the start page is displayed
    Then DTL perpendicular favored end and bias are shown

  Scenario: FR-108 Grafana race-sailsteer mirrors H5000 SailSteer
    When I open race-sailsteer
    Then laylines heel wind and performance bargraph match H5000 field semantics

  Scenario: FR-111 race-highway shows leg progress
    Given an active route leg
    When I open race-highway
    Then XTE DTM ETA and COG are shown for the leg

  Scenario: race-intelligence publishes start and lift guidance
    Given an active race session near the start line
    When race-intelligence evaluates fleet and wind context
    Then structured guidance is available to grafana-race and insight producers
