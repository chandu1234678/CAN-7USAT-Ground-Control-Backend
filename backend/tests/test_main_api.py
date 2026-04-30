"""Integration tests for FastAPI endpoints and WebSocket telemetry stream."""

from datetime import datetime

from fastapi.testclient import TestClient

from app.models import FlightState, TelemetryPacket


def _make_packet() -> TelemetryPacket:
    return TelemetryPacket(
        sync_byte=0xAA,
        timestamp_ms=1234,
        flight_state=FlightState.COAST,
        altitude_m=156.7,
        velocity_ms=45.2,
        quat_w=1.0,
        quat_x=0.0,
        quat_y=0.0,
        quat_z=0.0,
        gps_lat=26.74,
        gps_lon=83.887,
        checksum_xor=123,
        received_at=datetime.utcnow(),
    )


def _reset_runtime_state(main_module) -> None:
    main_module.packet_history.clear()
    main_module.latest_packet = None
    main_module.decoder.packets_decoded = 0
    main_module.decoder.packets_dropped = 0


def test_health_and_status_endpoints():
    from app import main as main_module

    main_module.settings.mock_mode = False
    _reset_runtime_state(main_module)

    with TestClient(main_module.app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        status = client.get("/api/status")
        assert status.status_code == 200
        body = status.json()
        assert body["packets_received"] == 0
        assert body["packets_dropped"] == 0


def test_latest_history_decoder_and_export_endpoints():
    from app import main as main_module

    main_module.settings.mock_mode = False
    _reset_runtime_state(main_module)

    packet = _make_packet()
    main_module.latest_packet = packet
    main_module.packet_history.append(packet)

    with TestClient(main_module.app) as client:
        latest = client.get("/api/telemetry/latest")
        assert latest.status_code == 200
        assert latest.json()["timestamp_ms"] == 1234

        history = client.get("/api/telemetry/history", params={"limit": 1})
        assert history.status_code == 200
        assert history.json()["count"] == 1

        stats = client.get("/api/decoder/stats")
        assert stats.status_code == 200
        assert "packets_decoded" in stats.json()

        export = client.get("/api/export/csv")
        assert export.status_code == 200
        export_body = export.json()
        assert export_body["rows"] == 1
        assert "timestamp_ms" in export_body["csv"]


def test_command_endpoint_and_not_found_latest():
    from app import main as main_module

    main_module.settings.mock_mode = False
    _reset_runtime_state(main_module)

    with TestClient(main_module.app) as client:
        missing = client.get("/api/telemetry/latest")
        assert missing.status_code == 404

        cmd = client.post("/api/command", json={"command": "ARM", "parameters": {"mode": "test"}})
        assert cmd.status_code == 200
        assert cmd.json()["status"] == "queued"


def test_websocket_connected_and_echo_flow():
    from app import main as main_module

    main_module.settings.mock_mode = False
    _reset_runtime_state(main_module)
    main_module.latest_packet = _make_packet()

    with TestClient(main_module.app) as client:
        with client.websocket_connect("/ws/telemetry") as ws:
            first = ws.receive_json()
            assert first["type"] == "connected"

            second = ws.receive_json()
            assert second["timestamp_ms"] == 1234

            ws.send_text("ping")
            echo = ws.receive_json()
            assert echo["echo"] == "ping"
