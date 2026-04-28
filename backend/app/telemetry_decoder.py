"""
Binary telemetry packet decoder
Decodes 46-byte packed struct from Teensy 4.1
"""

import struct
import logging
from datetime import datetime
from .models import TelemetryPacket, FlightState

logger = logging.getLogger(__name__)


class TelemetryDecoder:
    """
    Decodes binary telemetry packets from the flight computer
    
    Packet Structure (46 bytes):
    - sync_byte (uint8_t): 0xAA
    - timestamp_ms (uint32_t): Milliseconds since boot
    - flight_state (uint8_t): 0-5 (PRE_FLIGHT to LANDED)
    - altitude_m (float): Barometric altitude AGL
    - velocity_ms (float): Vertical velocity
    - quat_w, quat_x, quat_y, quat_z (float): Quaternion components
    - gps_lat, gps_lon (float): GPS coordinates
    - checksum_xor (uint8_t): XOR of all bytes
    """
    
    PACKET_SIZE = 46
    SYNC_BYTE = 0xAA
    
    # Struct format: little-endian (<)
    # B = uint8_t, I = uint32_t, f = float, x = padding byte
    # Padding added to match C struct alignment (4-byte boundaries)
    # B(1) + xxx(3) + I(4) + B(1) + xxx(3) + 8×f(32) + B(1) + x(1) = 46 bytes
    STRUCT_FORMAT = '<B 3x I B 3x f f f f f f f f B x'
    
    def __init__(self):
        self.packets_decoded = 0
        self.packets_dropped = 0
    
    def decode(self, raw_bytes: bytes) -> TelemetryPacket | None:
        """
        Decode binary packet into TelemetryPacket model
        
        Args:
            raw_bytes: 46-byte binary packet
            
        Returns:
            TelemetryPacket if valid, None if corrupted
        """
        # Validate packet size
        if len(raw_bytes) != self.PACKET_SIZE:
            logger.warning(f"Invalid packet size: {len(raw_bytes)} (expected {self.PACKET_SIZE})")
            self.packets_dropped += 1
            return None
        
        try:
            # Unpack binary data
            unpacked = struct.unpack(self.STRUCT_FORMAT, raw_bytes)
            
            sync_byte = unpacked[0]
            timestamp_ms = unpacked[1]
            flight_state = unpacked[2]
            altitude_m = unpacked[3]
            velocity_ms = unpacked[4]
            quat_w = unpacked[5]
            quat_x = unpacked[6]
            quat_y = unpacked[7]
            quat_z = unpacked[8]
            gps_lat = unpacked[9]
            gps_lon = unpacked[10]
            checksum_xor = unpacked[11]
            
            # Validate sync byte
            if sync_byte != self.SYNC_BYTE:
                logger.warning(f"Invalid sync byte: 0x{sync_byte:02X} (expected 0x{self.SYNC_BYTE:02X})")
                self.packets_dropped += 1
                return None
            
            # Validate checksum (XOR of first 44 bytes, checksum is at byte 44)
            calculated_checksum = self._calculate_checksum(raw_bytes[:44])
            if calculated_checksum != checksum_xor:
                logger.warning(
                    f"Checksum mismatch: calculated=0x{calculated_checksum:02X}, "
                    f"received=0x{checksum_xor:02X}"
                )
                self.packets_dropped += 1
                return None
            
            # Validate flight state
            if flight_state not in range(6):
                logger.warning(f"Invalid flight state: {flight_state}")
                self.packets_dropped += 1
                return None
            
            # Create TelemetryPacket
            packet = TelemetryPacket(
                sync_byte=sync_byte,
                timestamp_ms=timestamp_ms,
                flight_state=FlightState(flight_state),
                altitude_m=altitude_m,
                velocity_ms=velocity_ms,
                quat_w=quat_w,
                quat_x=quat_x,
                quat_y=quat_y,
                quat_z=quat_z,
                gps_lat=gps_lat,
                gps_lon=gps_lon,
                checksum_xor=checksum_xor,
                received_at=datetime.utcnow()
            )
            
            self.packets_decoded += 1
            return packet
            
        except struct.error as e:
            logger.error(f"Struct unpacking error: {e}")
            self.packets_dropped += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected decoding error: {e}")
            self.packets_dropped += 1
            return None
    
    def encode(self, packet: TelemetryPacket) -> bytes:
        """
        Encode TelemetryPacket into binary format
        Useful for testing and mock data generation
        
        Args:
            packet: TelemetryPacket to encode
            
        Returns:
            46-byte binary packet
        """
        # Pack all fields with padding for alignment
        # Note: We calculate checksum on ALL bytes including padding
        data_without_checksum = struct.pack(
            '<B 3x I B 3x f f f f f f f f',
            packet.sync_byte,
            packet.timestamp_ms,
            packet.flight_state.value,
            packet.altitude_m,
            packet.velocity_ms,
            packet.quat_w,
            packet.quat_x,
            packet.quat_y,
            packet.quat_z,
            packet.gps_lat,
            packet.gps_lon
        )
        
        # Calculate checksum on all bytes including padding
        checksum = self._calculate_checksum(data_without_checksum)
        
        # Pack complete packet with checksum and final padding
        complete_packet = data_without_checksum + struct.pack('B x', checksum)
        
        return complete_packet
    
    @staticmethod
    def _calculate_checksum(data: bytes) -> int:
        """
        Calculate XOR checksum of byte array
        
        Args:
            data: Bytes to checksum
            
        Returns:
            XOR checksum (0-255)
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum
    
    def get_stats(self) -> dict:
        """Get decoder statistics"""
        total = self.packets_decoded + self.packets_dropped
        success_rate = (self.packets_decoded / total * 100) if total > 0 else 0.0
        
        return {
            "packets_decoded": self.packets_decoded,
            "packets_dropped": self.packets_dropped,
            "total_packets": total,
            "success_rate": round(success_rate, 2)
        }
