# expedition-bridge

Pydantic wrapper that polls **Expedition** via [Expedition-Python](https://pypi.org/project/Expedition-Python/) and publishes **`race.expedition.*`** to Signal K.

**Runs on the nav laptop (Windows)**, not on the Pi. See [ADR-0034](../adr/0034-expedition-laptop-signalk-federation.md) and [docs/SIGNALK_RACE_EXTENSION.md](../docs/SIGNALK_RACE_EXTENSION.md).

## Quick start (laptop)

```powershell
pip install -r requirements.txt
# Expedition must be running; ExpDLL.dll discoverable via registry

$env:EXPEDITION_BRIDGE_FEDERATION_MODE = "dual_publish"
$env:EXPEDITION_BRIDGE_UPSTREAM_SIGNALK_URL = "http://telemetry.local:3000"
python -m expedition_bridge.bridge
```

## Mock mode (dev / CI without Windows)

```powershell
$env:EXPEDITION_BRIDGE_EXPEDITION_MOCK = "true"
python -m expedition_bridge.bridge
```

## Tests

```bash
pip install -r requirements.txt
pytest expedition-bridge/tests -v
```

## Architecture

```
Expedition (UI) ←→ ExpDLL ←→ expedition-bridge (Pydantic)
                                    ↓ PUT race.expedition.*
                    laptop SK (127.0.0.1:3000) + Pi SK (telemetry.local)
```

Instruments stay on **Pi SLA-1** Signal K. This bridge only adds Expedition tactical paths.
