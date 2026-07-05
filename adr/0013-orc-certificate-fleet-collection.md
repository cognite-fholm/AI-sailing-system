# ADR-0013: Automated ORC certificate collection for race fleets

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0009](./0009-dual-repository-race-data.md), [spec §7.19](../spec.md#719-orc-certificate-collection--fleet-enrichment), [AI-sailing-data orc-sailor-services skill](https://github.com/cognite-fholm/AI-sailing-data/tree/main/.cursor/skills/orc-sailor-services)

## Context

Race preparation requires **ORC certificate metadata and PDFs** for every entrant in the relevant class — refs, handicaps, cert types, and polar inputs for `handicap-manager` and `polar-certificate-extractor`.

Today:

- **Manage2Sail** and **SailRace System** provide fleet lists with `orc_ref` and `hcp` at registration time.
- **ORC Sailor Services** (`data.orc.org/public/WPub.dll`) holds authoritative cert data and PDF copies.
- **crawl_web** `orc_certificates.py` bulk-fetches active NOR certs to CDF but does not map cleanly to per-race `fleet.yaml` or `boats/{sail_number}/` layout.
- **ORC måletall** zip packages supply SLK and PDFs for the own boat but not the full competitor fleet.

Browser HAR captures (`data.orc.org.har`) show stable endpoints:

| Endpoint | Format | Auth |
|----------|--------|------|
| `activecerts&CountryId=NOR&Family={1\|3\|5}` | XML | None |
| POST `ListCert` + `SailNo` | HTML | None |
| `CC/{dxtID}` or `CC/{RefNo}` | PDF | Sailor Services session |

For a typical Norwegian Doublehanded regatta, **one `activecerts` Family=3 request** matches the entire starter list (verified: Færderseilasen 2026, 37/37).

## Decision

1. **Shore collection lives in AI-sailing-data** via Cursor skill **`orc-sailor-services`** — not a new SLA-2 container in v1.
2. **Three-step pipeline:**
   - `fetch_fleet_certs.py` — bulk metadata from `activecerts` + per-boat `ListCert` fallback → `collected/orc/{race}/fleet-orc-index.yaml`
   - `download_cert_pdfs.py` — PDF binaries using exported browser session cookie → `collected/orc/{race}/pdfs/`
   - `materialize_boat_certs.py` — `boats/{sail}/{year}/certificates/{type}-{orc_ref}/` stubs + `manifest.yaml`
3. **Integration order:** manage2sail or sailracesystem → orc-sailor-services → optional måletall zip for own-boat SLK.
4. **PDF auth:** Document cookie export; do not store credentials in git. Optional future: dedicated `orc-cert-sync` container with vault-held session (Phase 2+).
5. **Downstream consumers unchanged:** `race-import`, `handicap-manager`, `polar-certificate-extractor` read YAML + `assets/orc-certificate.pdf` from data repo paths.

## Rationale

- **Bulk XML** avoids N browser sessions for fleet metadata — fast, polite, reproducible.
- **Cursor skill** matches existing race-prep pattern (manage2sail, sailracesystem) and keeps collection logic versioned with data schemas.
- **Separating metadata and PDF download** reflects ORC portal auth: refs are public; PDF copies require login.
- **Validating registration `orc_ref`** against live ORC catches stale Manage2Sail data before race day.

## Consequences

### Positive

- Full class certificate index in minutes after `fleet.yaml` exists.
- Ref mismatches surfaced explicitly (`ref_mismatches` in index).
- Competitor `boats/` folders can be bootstrapped automatically.
- Clear provenance via `collected_from.source: orc_sailor_services` in `schema/collected-sources.yaml`.

### Negative

- PDF automation depends on a **manual cookie export** or måletall/crawl_web until a headless auth flow exists.
- `ListCert` HTML parsing is brittle if ORC changes markup (mitigated by XML-first path).
- Large `activecerts` XML snapshots in git (~hundreds of KB per family per race).

### Risks

| Risk | Mitigation |
|------|------------|
| ORC rate-limits or blocks scripted access | Sleep between ListCert calls; cache XML; user-agent identify |
| Session cookie expires mid-download | Re-export; download-report.json lists failures |
| Wrong cert type when boat has multiple active certs | Match `orc_certificate_type` from fleet; prefer fleet `orc_ref` |

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Browser automation (Playwright) for every boat | Slower, heavier, harder in CI; still needs login |
| Extend crawl_web only | No fleet.yaml integration; CDF-centric |
| New `orc-cert-sync` SLA-2 service immediately | Over-engineering before shore skill is proven |
| Manual portal search per boat | Does not scale to 30+ boat classes |

## Follow-up

- [ ] Phase 2 optional `orc-cert-sync` container for scheduled refresh in harbor (LTE)
- [ ] Link prep guide Phase 3–4 to skill workflow
- [ ] `polar-certificate-extractor` consume stubs when SLK absent
