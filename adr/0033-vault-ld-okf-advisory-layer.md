# ADR-0033: Vault-LD for OKF advisory layer only

**Status:** Accepted  
**Date:** 2026-07-10  
**Deciders:** cognite-fholm  
**Related:** [ADR-0022](./0022-yaml-ld-interconnected-data.md), [ADR-0023](./0023-shacl-neo4j-projection-no-fuseki.md), [ADR-0032](./0032-yaml-ld-ontology-pyshacl-dq-reports.md), [AI-sailing-data OKF_VAULT_LD.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/OKF_VAULT_LD.md)

---

## Context

AI-sailing-data uses YAML-LD for **facts** (`boats/`, `races/`) and Markdown **OKF** bundles for agent advisory context (`okf/*.md`). OKF matches the physical shape of [Vault-LD](https://github.com/The-Knowledge-Graph-Guys/vault-ld) (YAML frontmatter + prose body) but lacked a shared `@context` for linked-data reasoning.

Full Vault-LD migration of fact YAML would conflict with `race-import`, Pydantic, fleet matrices, and pySHACL DQ reports.

---

## Decision

Adopt **Vault-LD Appendix B (OKF lift)** for the **OKF layer only**:

1. **Facts unchanged** — `boats/`, `races/` remain W3C YAML-LD source of truth.
2. **OKF context** — `schema/okf-vault/context.jsonld` maps OKF `type` → `@type`, `resource` → `sailing:documentRef`, `entityRef` → entity URNs.
3. **Per-bundle context** — each `okf/context.jsonld` composes the shared context.
4. **Export** — `scripts/okf_vault_export.py` → `okf-export/graph.ttl` (shore only; not Neo4j import).
5. **Frontmatter** — use document `@id` paths and `urn:sailing:entity:*` links to fact layer.

---

## Rationale

- Agents get a queryable RDF view of OKF concepts without duplicating facts in Markdown.
- Vault-LD round-trip and wiki-link ergonomics available for future Obsidian/LLM workflows.
- Zero change to boat/race import pipeline or Pi runtime.

---

## Consequences

### Positive

- OKF notes link formally to YAML-LD facts and entity URNs.
- Shore can export OKF subgraph to Turtle for analytics.
- Aligns with Google OKF conventions already in use.

### Trade-offs

- Two linked-data surfaces (fact YAML + OKF vault) — agents must read `yaml-ld-read` vs OKF docs.
- `okf-export/` must be regenerated when OKF notes change (CI).

---

## Implementation

- AI-sailing-data: `schema/okf-vault/`, `scripts/okf_vault_export.py`, `docs/OKF_VAULT_LD.md`, CI step
- Skills: `race-wiki-okf` updated with Vault-LD frontmatter contract
