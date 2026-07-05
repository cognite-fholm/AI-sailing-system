@phase_05 @wip
Feature: Phase 5 — Shore TrimTransformer training (SLA-S)
  Gaming PC training pipeline and trim-predictor deployment to SLA-3.
  See spec §7.11, §9.6, FR-72–78, ADR-0003.

  Background:
    Given a shore gaming PC with CUDA is configured as SLA-S
    And training-export bundles exist from harbor opt-in sessions

  Scenario: FR-73 training export requires explicit consent
    Given TRAINING_EXPORT_CONSENT is not set for a session
    When training-export is requested
    Then export is rejected

  Scenario: FR-74 TrimTransformer trains on shore GPU
    Given a valid multimodal training bundle
    When trim-transformer-trainer runs on the gaming PC
    Then a model checkpoint is produced with held-out regatta evaluation

  Scenario: FR-77 trim-predictor deployable via GHCR
    When the trained model is published
    Then a quantized trim-predictor image is available on GHCR for SLA-3

  Scenario: FR-78 BestTrimSnapshot sync to boat Neo4j
    When shore training completes a round
    Then BestTrimSnapshot nodes sync to boat Neo4j for condition-matcher
