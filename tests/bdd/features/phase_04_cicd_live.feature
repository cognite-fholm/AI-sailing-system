@phase_04 @wip
Feature: Phase 4 — CI/CD and multi-Pi operations (live)
  GitHub Actions, GHCR images, harbor scripts, and race-mode guardrails.
  See spec §9, FR-90–101, FR-105, ADR-0008.

  Background:
    Given the project uses GitHub Actions and GHCR for container delivery

  Scenario: FR-96 arm64 images published to GHCR
    When a release tag is pushed
    Then publish workflows build linux/arm64 images to GHCR

  Scenario: FR-99 digest-pinned deploy locks
    When release.yml runs for tag vX.Y.Z
    Then deploy/locks/vX.Y.Z.env records image digests or placeholders

  Scenario: FR-92 RACE_MODE disables Watchtower
    Given RACE_MODE is true in deploy environment
    When harbor sync runs
    Then Watchtower does not auto-update running containers

  Scenario: FR-101 harbor sync separates images from models and data
    When harbor-sync.sh runs in harbor
    Then container pulls use harbor-pull.sh and models OKF and data repo sync separately
