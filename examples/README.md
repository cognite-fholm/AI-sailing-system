# Reference polar input files

Polar source files live in the **parent** `boat_system` directory (not inside this git repo):

| File | Vessel | Format | Use |
|------|--------|--------|-----|
| [`../7710 (3).slk`](../../7710%20(3).slk) | Own boat (7710) | SYLK / SLK | Primary polar — parsed by `polar-manager` |
| [`../off_course.png`](../../off_course.png) | OFF COURSE (NOR 15788) | ORC certificate image | Competitor — derived polar via `polar-certificate-extractor` |

Configured in:

- [`config/vessel.yaml`](../config/vessel.yaml)
- [`config/competitors.yaml`](../config/competitors.yaml)

See [spec.md §7.12.3](../spec.md#7123-polar-diagram-management) for full format details.
