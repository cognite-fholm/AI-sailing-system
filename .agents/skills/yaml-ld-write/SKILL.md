---
name: yaml-ld-write
description: >-
  Write or fix YAML in AI-sailing-system that mirrors AI-sailing-data facts
  (config/data-repo.yaml, test fixtures). Delegates to AI-sailing-data yaml-ld-write
  skill. Use when editing data-repo config YAML or adding test fixtures that
  represent boats/races/neo4j kinds — never write non-conformant interconnected YAML.
---

# YAML-LD write — AI-sailing-system (config & fixtures)

**Authoritative write skill:** [AI-sailing-data yaml-ld-write](https://github.com/cognite-fholm/AI-sailing-data/blob/main/.cursor/skills/yaml-ld-write/SKILL.md) — **read and follow it verbatim** for any interconnected fact shape.

**ADR:** [0022-yaml-ld-interconnected-data](../../adr/0022-yaml-ld-interconnected-data.md)

---

## When this skill applies

| File | YAML-LD required? |
|------|-------------------|
| `config/data-repo.yaml` | **Yes** — links to active race/boat paths |
| `tests/**/fixtures/**/*.yaml` copying data kinds | **Yes** |
| `docker-compose*.yml`, `deploy/env/*` | **No** |
| `config/signalk/settings.json` | **No** (JSON) |

---

## DO

| # | Rule |
|---|------|
| D1 | **DO** open the data-repo write skill and apply the same `@context` / `@id` / `@type` header block. |
| D2 | **DO** keep `config/data-repo.yaml` `active` paths as POSIX repo-relative strings. |
| D3 | **DO** add entity node objects for `active_certificate_ref` when migrating `data-repo.yaml` to YAML-LD. |
| D4 | **DO** run unit tests after editing fixtures. |

---

## DON'T

| # | Rule |
|---|------|
| X1 | **DON'T** invent a different context URL or `@base` than the data repo. |
| X2 | **DON'T** add boat/race fact YAML under `AI-sailing-system/` except test fixtures — facts belong in **AI-sailing-data**. |
| X3 | **DON'T** duplicate `schema/yaml-ld/context.jsonld` here — reference the data repo canonical copy. |
| X4 | **DON'T** bypass YAML-LD for "small" fixture files — one-line violations spread. |

---

## `config/data-repo.yaml` target shape (migration)

```yaml
"@context":
  - "https://sailing.cognite-fholm/schema/v1/context.jsonld"
  - "@base": "https://sailing.cognite-fholm/data/v1/"
"@id": "config/data-repo.yaml"
"@type": "sailing:DataRepoConfig"
apiVersion: sailing.cognite-fholm/v1
kind: DataRepoConfig
metadata:
  ref: config-data-repo
spec:
  data_repo:
    url: https://github.com/cognite-fholm/AI-sailing-data.git
    local_path: /opt/ai-sailing-data
  active:
    regatta_id: faerderseilasen-2026
    race_document:
      "@type": "sailing:Race"
      "@id": "races/2026/2026-06-faerderseilasen/race.yaml"
    own_boat:
      "@type": "sailing:Boat"
      "@id": "boats/NOR-10133/boat.yaml"
```

Register `DataRepoConfig` in data-repo `context.jsonld` when migrating this file.

---

## Related

- Read: [yaml-ld-read](../yaml-ld-read/SKILL.md)
- Pydantic: [pydantic-first-coding](../pydantic-first-coding/SKILL.md)
