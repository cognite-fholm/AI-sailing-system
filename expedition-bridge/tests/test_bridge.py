from expedition_bridge.bridge import ExpeditionBridge
from expedition_bridge.config import BridgeSettings
from expedition_bridge.expedition.client import MockExpeditionClient
from expedition_bridge.expedition.models import ExpeditionMeta, ExpeditionSnapshot, ExpeditionStartLine
from expedition_bridge.signalk.publisher import CollectingSignalKPublisher


def test_bridge_poll_once_uses_mock_client() -> None:
    snap = ExpeditionSnapshot(
        start=ExpeditionStartLine(dist_to_line_m=10.0),
        meta=ExpeditionMeta(connected=True, api_version="mock"),
    )
    publisher = CollectingSignalKPublisher()
    settings = BridgeSettings(expedition_mock=True, federation_mode="local_only")
    bridge = ExpeditionBridge(
        settings,
        expedition=MockExpeditionClient(snap),
        publisher=publisher,
    )
    delta = bridge.poll_once()
    assert len(publisher.deltas) == 1
    paths = {v.path: v.value for v in delta.updates[0].values}
    assert paths["race.expedition.start.distToLine"] == 10.0


def test_publish_urls_dual() -> None:
    settings = BridgeSettings(
        local_signalk_url="http://127.0.0.1:3000",
        upstream_signalk_url="http://telemetry.local:3000",
        federation_mode="dual_publish",
    )
    assert settings.publish_urls() == [
        "http://127.0.0.1:3000",
        "http://telemetry.local:3000",
    ]
