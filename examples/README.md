# Reference polar input files

Polar source files live in the **parent** `boat_system` directory (not inside this git repo):

| File | Vessel | Format | Use |
|------|--------|--------|-----|
| [`../7710 (3).slk`](../../7710%20(3).slk) | Own boat (7710) | SYLK / SLK | Primary polar — `polar-manager` |
| [`../off_course.png`](../../off_course.png) | OFF COURSE (NOR 15788) | ORC certificate image | Competitor polar — `polar-certificate-extractor` |
| [`../ORC Certificate for Off Course.pdf`](../../ORC%20Certificate%20for%20Off%20Course.pdf) | OFF COURSE | ORC certificate PDF | Handicaps + polar — `handicap-manager` |
| [`../Seilingsbestemmelser_Færderseilasen26_2.pdf`](../../Seilingsbestemmelser_F%C3%A6rderseilasen26_2.pdf) | Færderseilasen 2026 | SI PDF §11 | Course routes (narrative) — `course-parser` |
| [`../Seilingsbestemmelser Høstcup 2025 ENDELIG.pdf`](../../Seilingsbestemmelser%20H%C3%B8stcup%202025%20ENDELIG.pdf) | Høstcup 2025 | SI Vedlegg 1–2, §7 | **Bane A/B**, class flags, start-boat signals — `course-parser` + `course-flag-detector` |

Configured in:

- [`config/vessel.yaml`](../config/vessel.yaml)
- [`config/competitors.yaml`](../config/competitors.yaml)
- [`config/courses.yaml`](../config/courses.yaml) — Færderseilasen
- [`config/courses-hostcup.yaml`](../config/courses-hostcup.yaml) — Høstcup multi-course + flags
- [`config/handicaps.yaml`](../config/handicaps.yaml)

See [spec.md §7.12.3](../spec.md#7123-polar-diagram-management), [§7.13](../spec.md#713-race-courses-waypoints--live-results) (incl. §7.13.2–7.13.3 start-boat flags), and [§7.14](../spec.md#714-handicap-numbers--scoring).
