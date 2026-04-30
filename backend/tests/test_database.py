"""Async database manager tests using temporary SQLite database."""

from datetime import datetime

import pytest

from app.database import DatabaseManager


@pytest.mark.asyncio
async def test_database_initialize_save_and_query(tmp_path):
    db_path = tmp_path / "telemetry_test.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    manager = DatabaseManager(database_url=db_url)

    await manager.initialize()

    packet = {
        "timestamp_ms": 1000,
        "flight_state": 2,
        "altitude_m": 123.4,
        "velocity_ms": 45.6,
        "quat_w": 1.0,
        "quat_x": 0.0,
        "quat_y": 0.0,
        "quat_z": 0.0,
        "gps_lat": 26.74,
        "gps_lon": 83.887,
        "checksum_xor": 42,
        "received_at": datetime.utcnow().isoformat(),
    }

    saved = await manager.save_telemetry(packet)
    assert saved is True

    recent = await manager.get_recent_telemetry(limit=10)
    assert len(recent) == 1
    assert recent[0]["timestamp_ms"] == 1000
    assert recent[0]["altitude_m"] == pytest.approx(123.4)

    summary = await manager.get_flight_summary()
    assert summary is not None
    assert summary["total_packets"] == 1
    assert summary["max_altitude_m"] == pytest.approx(123.4)

    await manager.close()


@pytest.mark.asyncio
async def test_database_disabled_returns_safe_defaults():
    manager = DatabaseManager(database_url="")

    await manager.initialize()

    assert manager.enabled is False
    assert await manager.save_telemetry({}) is False
    assert await manager.get_recent_telemetry() == []
    assert await manager.get_flight_summary() is None

    await manager.close()
