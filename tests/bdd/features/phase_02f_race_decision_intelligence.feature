@phase_02f
Feature: Phase 2F — Race decision intelligence playbook
  Tactical questions are standardized into a repeatable answer contract for race-winning decisions.
  See spec §7.28, §11.21, ADR-0031.

  Scenario: Decision playbook is documented for users
    Given the file "docs/race-decision-playbook.md" exists in the system repo
    Then the file "docs/race-decision-playbook.md" contains "Recommendation now"
    And the file "docs/race-decision-playbook.md" contains "Core race-winning questions"
    And the file "docs/race-decision-playbook.md" contains "Corrected-time if finished now"
    And the file "docs/race-day-command-sheet.md" exists in the system repo
    And the file "docs/race-day-command-sheet.md" contains "How your sail matrix contributes"

  Scenario: Project skill exists for tactical decision answering
    Given the file ".cursor/skills/race-decision-intelligence/SKILL.md" exists in the system repo
    Then the file ".cursor/skills/race-decision-intelligence/SKILL.md" contains "name: race-decision-intelligence"
    And the file ".cursor/skills/race-decision-intelligence/SKILL.md" contains "Required output format"
    And the file ".cursor/skills/race-decision-intelligence/reference.md" exists in the system repo

  Scenario: Spec includes decision intelligence sections and FR coverage
    Then spec.md contains section "7.28 Race decision intelligence"
    And the file "spec.md" contains "FR-246"
    And the file "spec.md" contains "FR-255"

  Scenario: ADR and architecture reference decision intelligence
    Given the file "adr/0031-race-decision-intelligence-playbook.md" exists in the system repo
    Then the file "adr/README.md" contains "0031"
    And the file "docs/ARCHITECTURE.md" contains "0031"
