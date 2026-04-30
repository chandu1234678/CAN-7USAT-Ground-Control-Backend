"""Unit tests for mock telemetry generator."""

import pytest

from app.models import FlightState
from app.mock_data_generator import MockDataGenerator


def test_flight_state_boundaries():
    generator = MockDataGenerator(data_rate_hz=10)

    assert generator._get_flight_state(0.0) == FlightState.PRE_FLIGHT
    assert generator._get_flight_state(generator.LIFTOFF_TIME + 0.01) == FlightState.BOOST
    assert generator._get_flight_state(generator.BURNOUT_TIME + 0.01) == FlightState.COAST
    assert generator._get_flight_state(generator.APOGEE_TIME + 0.2) == FlightState.APOGEE
    assert generator._get_flight_state(generator.APOGEE_TIME + 2.0) == FlightState.DESCENT
    assert generator._get_flight_state(generator.LANDING_TIME + 1.0) == FlightState.LANDED


def test_altitude_profile_shape():
    generator = MockDataGenerator(data_rate_hz=10)

    alt_pre = generator._calculate_altitude(0.0)
    alt_boost = generator._calculate_altitude(generator.BURNOUT_TIME * 0.9)
    alt_apogee = generator._calculate_altitude(generator.APOGEE_TIME)
    alt_late = generator._calculate_altitude(generator.LANDING_TIME + 1.0)

    assert alt_pre == 0.0
    assert alt_boost > 0.0
    assert alt_apogee >= alt_boost
    assert alt_late == 0.0


def test_gps_drift_increases_longitude_over_time():
    generator = MockDataGenerator(data_rate_hz=10)

    _, lon_early = generator._calculate_gps(generator.LIFTOFF_TIME + 1.0, 10.0)
    _, lon_late = generator._calculate_gps(generator.LIFTOFF_TIME + 10.0, 10.0)

    assert lon_late > lon_early


@pytest.mark.asyncio
async def test_generate_packet_produces_valid_binary_packet():
    generator = MockDataGenerator(data_rate_hz=10)

    raw_packet = await generator.generate_packet(elapsed_time=2.0)

    assert isinstance(raw_packet, bytes)
    assert len(raw_packet) == generator.decoder.PACKET_SIZE

    decoded = generator.decoder.decode(raw_packet)
    assert decoded is not None
    assert decoded.sync_byte == 0xAA
    assert decoded.timestamp_ms == 2000
