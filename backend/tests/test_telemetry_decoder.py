"""
Tests for telemetry decoder
"""

import pytest
from app.telemetry_decoder import TelemetryDecoder
from app.models import TelemetryPacket, FlightState


class TestTelemetryDecoder:
    """Test suite for TelemetryDecoder"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.decoder = TelemetryDecoder()
    
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding are inverse operations"""
        # Create a test packet
        original_packet = TelemetryPacket(
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
            checksum_xor=0  # Will be calculated
        )
        
        # Encode to binary
        binary_data = self.decoder.encode(original_packet)
        
        # Verify packet size
        assert len(binary_data) == TelemetryDecoder.PACKET_SIZE
        
        # Decode back
        decoded_packet = self.decoder.decode(binary_data)
        
        # Verify decoding succeeded
        assert decoded_packet is not None
        
        # Verify all fields match
        assert decoded_packet.sync_byte == original_packet.sync_byte
        assert decoded_packet.timestamp_ms == original_packet.timestamp_ms
        assert decoded_packet.flight_state == original_packet.flight_state
        assert abs(decoded_packet.altitude_m - original_packet.altitude_m) < 0.01
        assert abs(decoded_packet.velocity_ms - original_packet.velocity_ms) < 0.01
        assert abs(decoded_packet.quat_w - original_packet.quat_w) < 0.0001
        assert abs(decoded_packet.gps_lat - original_packet.gps_lat) < 0.00001
        assert abs(decoded_packet.gps_lon - original_packet.gps_lon) < 0.00001
    
    def test_invalid_packet_size(self):
        """Test that invalid packet size is rejected"""
        # Too short
        short_packet = b'\xAA' * 10
        result = self.decoder.decode(short_packet)
        assert result is None
        assert self.decoder.packets_dropped == 1
        
        # Too long
        long_packet = b'\xAA' * 100
        result = self.decoder.decode(long_packet)
        assert result is None
        assert self.decoder.packets_dropped == 2
    
    def test_invalid_sync_byte(self):
        """Test that invalid sync byte is rejected"""
        # Create valid packet
        packet = TelemetryPacket(
            sync_byte=0xAA,
            timestamp_ms=1000,
            flight_state=FlightState.PRE_FLIGHT,
            altitude_m=0.0,
            velocity_ms=0.0,
            quat_w=1.0,
            quat_x=0.0,
            quat_y=0.0,
            quat_z=0.0,
            gps_lat=26.74,
            gps_lon=83.887,
            checksum_xor=0
        )
        
        binary_data = bytearray(self.decoder.encode(packet))
        
        # Corrupt sync byte
        binary_data[0] = 0xFF
        
        # Try to decode
        result = self.decoder.decode(bytes(binary_data))
        assert result is None
        assert self.decoder.packets_dropped == 1
    
    def test_checksum_validation(self):
        """Test that checksum validation works"""
        # Create valid packet
        packet = TelemetryPacket(
            sync_byte=0xAA,
            timestamp_ms=5000,
            flight_state=FlightState.BOOST,
            altitude_m=50.0,
            velocity_ms=80.0,
            quat_w=0.9,
            quat_x=0.1,
            quat_y=0.0,
            quat_z=0.0,
            gps_lat=26.74,
            gps_lon=83.887,
            checksum_xor=0
        )
        
        binary_data = bytearray(self.decoder.encode(packet))
        
        # Corrupt checksum (byte 44, not the last byte which is padding)
        binary_data[44] ^= 0xFF
        
        # Try to decode
        result = self.decoder.decode(bytes(binary_data))
        assert result is None
        assert self.decoder.packets_dropped == 1
    
    def test_decoder_stats(self):
        """Test decoder statistics tracking"""
        # Create and decode valid packets
        for i in range(10):
            packet = TelemetryPacket(
                sync_byte=0xAA,
                timestamp_ms=i * 100,
                flight_state=FlightState.PRE_FLIGHT,
                altitude_m=0.0,
                velocity_ms=0.0,
                quat_w=1.0,
                quat_x=0.0,
                quat_y=0.0,
                quat_z=0.0,
                gps_lat=26.74,
                gps_lon=83.887,
                checksum_xor=0
            )
            binary_data = self.decoder.encode(packet)
            self.decoder.decode(binary_data)
        
        # Create invalid packets
        for i in range(3):
            self.decoder.decode(b'\xFF' * 46)
        
        # Check stats
        stats = self.decoder.get_stats()
        assert stats["packets_decoded"] == 10
        assert stats["packets_dropped"] == 3
        assert stats["total_packets"] == 13
        assert abs(stats["success_rate"] - 76.92) < 0.1
