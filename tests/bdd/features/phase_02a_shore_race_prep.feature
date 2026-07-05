@phase_02a
Feature: Phase 2A — Shore race prep (AI-sailing-data)
  Shore-side skills and YAML artifacts before onboard import.
  See spec §7.19–7.20, §7.23, FR-133–149, FR-173–180, ADR-0013, 0014, 0017.

  Background:
    Given the AI-sailing-data repository is available

  Scenario: Race preparation guide and skills exist
    Then file "docs/RACE_PREPARATION_GUIDE.md" exists in the data repo
    And directory ".cursor/skills/race-preparation" exists in the data repo

  Scenario: FR-133 ORC fleet metadata collection skill
    Then directory ".cursor/skills/orc-sailor-services" exists in the data repo
    And collected-sources.yaml in the data repo registers orc_sailor_services

  Scenario: FR-143 MET Norway GRIB shore collection skill
    Then directory ".cursor/skills/metno-oslofjord-weather" exists in the data repo

  Scenario: FR-144 Oslofjord current plot skill
    Then directory ".cursor/skills/oslofjord-current-plots" exists in the data repo

  Scenario: FR-145 SMHI wind validation skill
    Then directory ".cursor/skills/smhi-wind-observations" exists in the data repo

  Scenario: FR-173 Marine map GPX export for a race course
    Given a race folder with resolved course waypoints in the data repo
    When the marine-map-gpx-export skill is run
    Then export/marine-map contains Route GPX files and a MarineMapExport manifest

  Scenario: Prep status tracks shore workflow completion
    Then at least one race has planning/prep-status.yaml in the data repo
