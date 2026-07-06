# BDD acceptance tests (Gherkin)



Executable acceptance criteria for each [implementation phase](../../spec.md#14-implementation-phases). Feature files map to [spec §1.1](../../spec.md#11-implementation-map), functional requirements (§11), and ADRs.



## Layout



```

tests/bdd/

  features/          # Gherkin .feature files (one per phase)

  steps/             # pytest-bdd step definitions

  conftest.py        # Shared fixtures

```



| Feature file | Phase | Spec FR |

|--------------|-------|---------|

| `phase_00_foundation.feature` | 0 | FR-90–106 (partial) |

| `phase_01_sla1_telemetry.feature` | 1 scaffold | FR-1–6, ADR-0021 |
| `phase_01_sla1_telemetry_live.feature` | 1 live `@wip` | FR-1–6 |
| `phase_02a_shore_race_prep.feature` | 2A | FR-133–149, FR-173–180 |
| `phase_02b_graph_import.feature` | 2B scaffold | FR-102–104 |
| `phase_02b_graph_import_live.feature` | 2B live `@wip` | FR-102–104 |
| `phase_02c_grib_polars_ais.feature` | 2C scaffold | FR-19, FR-23 |
| `phase_02c_grib_polars_ais_live.feature` | 2C live `@wip` | FR-15–26 |

| `phase_02d_courses_results.feature` | 2D | FR-27–41 |

| `phase_02e_race_ux.feature` | 2E | FR-42–59, FR-107–123 |

| `phase_02f_analytics_alerts.feature` | 2F | FR-80–85, FR-150–172 |

| `phase_02g_race_laptop_mcp.feature` | 2G | FR-124–142 |

| `phase_03_sla3_vision.feature` | 3 | FR-61–71 |

| `phase_04_cicd.feature` | 4 scaffold | FR-94, publish workflows |
| `phase_04_cicd_live.feature` | 4 live `@wip` | FR-90–101, FR-105 |

| `phase_05_shore_training.feature` | 5 | FR-72–78 |



## Run



```bash

cd AI-sailing-system

python -m venv .venv

.venv\Scripts\activate          # Windows

pip install -r requirements-dev.txt



# Phase 0 (scaffold checks — also run in CI)

pytest tests/bdd/steps/test_phase_00_foundation.py -v



# All non-wip phases + unit tests (CI default)

pytest tests/bdd/steps tests/unit -m "not wip" -v



# With coverage report

pytest tests/bdd/steps tests/unit -m "not wip" --cov=course_sk_sync --cov=polar_manager --cov=signalk_influx_bridge --cov=signalk_polar_performance --cov-report=term-missing



# By tag

pytest tests/bdd/steps/ -m phase_00 -v

pytest tests/bdd/steps/ -m "not wip" -v

```



**CI:** `.github/workflows/ci.yml` runs all **non-@wip** BDD scenarios and unit tests on every push/PR to `main`.



## Shore prep (Phase 2A)



Phase 2A scenarios validate the companion [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) repo. Set:



```bash

set AI_SAILING_DATA_ROOT=C:\Repositories\boat_system\AI-sailing-data

```



If unset, 2A tests skip with a clear message.



## Local Docker stacks



Before live Phase 1/2B scenarios (`@wip`), install host prerequisites: [docs/DEV-SETUP.md](../../docs/DEV-SETUP.md).



## Adding steps



When implementing a phase, add step definitions for `@wip` scenarios (HTTP health checks, Neo4j queries, file artifacts, etc.). Keep scenario text in `.feature` files stable — change step bodies only.


