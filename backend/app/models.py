"""
Data models for telemetry packets and database schemas
"""

from enum import IntEnum
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class FlightState(IntEnum):
    """Flight state machine states"""
    PRE_FLIGHT = 0
    BOOST = 1
    COAST = 2
    APOGEE = 3
    DESCENT = 4
    LANDED = 5


class TelemetryPacket(BaseModel):
    """
    46-byte telemetry packet structure
    Matches the embedded C++ struct exactly
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sync_byte": 170,
            "timestamp_ms": 1234,
            "flight_state": 2,
            "altitude_m": 156.7,
            "velocity_ms": 45.2,
            "quat_w": 1.0,
            "quat_x": 0.0,
            "quat_y": 0.0,
            "quat_z": 0.0,
            "gps_lat": 26.74,
            "gps_lon": 83.887,
            "checksum_xor": 123
        }
    })
    
    sync_byte: int = Field(default=0xAA, ge=0, le=255, description="Sync byte (0xAA)")
    timestamp_ms: int = Field(..., ge=0, description="Milliseconds since boot")
    flight_state: FlightState = Field(..., description="Current flight state")
    altitude_m: float = Field(..., description="Barometric altitude AGL (meters)")
    velocity_ms: float = Field(..., description="Vertical velocity (m/s)")
    quat_w: float = Field(..., description="Quaternion W component")
    quat_x: float = Field(..., description="Quaternion X component")
    quat_y: float = Field(..., description="Quaternion Y component")
    quat_z: float = Field(..., description="Quaternion Z component")
    gps_lat: float = Field(..., description="GPS Latitude (degrees)")
    gps_lon: float = Field(..., description="GPS Longitude (degrees)")
    checksum_xor: int = Field(..., ge=0, le=255, description="XOR checksum")
    
    # Metadata (not in binary packet)
    received_at: Optional[datetime] = Field(default=None, description="Server receive timestamp")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "sync_byte": self.sync_byte,
            "timestamp_ms": self.timestamp_ms,
            "flight_state": self.flight_state.value,
            "flight_state_name": self.flight_state.name,
            "altitude_m": self.altitude_m,
            "velocity_ms": self.velocity_ms,
            "quat_w": self.quat_w,
            "quat_x": self.quat_x,
            "quat_y": self.quat_y,
            "quat_z": self.quat_z,
            "gps_lat": self.gps_lat,
            "gps_lon": self.gps_lon,
            "checksum_xor": self.checksum_xor,
            "received_at": self.received_at.isoformat() if self.received_at else None
        }


class SystemStatus(BaseModel):
    """System health and diagnostics"""
    connected: bool = Field(..., description="Serial connection status")
    packets_received: int = Field(default=0, description="Total packets received")
    packets_dropped: int = Field(default=0, description="Corrupted packets dropped")
    last_packet_time: Optional[datetime] = Field(default=None, description="Last packet timestamp")
    websocket_clients: int = Field(default=0, description="Connected WebSocket clients")
    uptime_seconds: float = Field(default=0.0, description="Server uptime")


class CommandRequest(BaseModel):
    """Command to send to rocket (uplink)"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "command": "ARM",
            "parameters": {"timeout": 300}
        }
    })
    
    command: str = Field(..., description="Command name")
    parameters: Optional[dict] = Field(default=None, description="Command parameters")
