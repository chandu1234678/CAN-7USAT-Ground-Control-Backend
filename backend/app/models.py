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
    
    sync_byte: int = Field(default=0xAA, ge=0, le=255)
    timestamp_ms: int = Field(..., ge=0)
    flight_state: FlightState
    altitude_m: float
    velocity_ms: float
    quat_w: float
    quat_x: float
    quat_y: float
    quat_z: float
    gps_lat: float
    gps_lon: float
    checksum_xor: int = Field(..., ge=0, le=255)
    received_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
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
    connected: bool
    packets_received: int = 0
    packets_dropped: int = 0
    last_packet_time: Optional[datetime] = None
    websocket_clients: int = 0
    uptime_seconds: float = 0.0


class CommandRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"command": "ARM", "parameters": {"timeout": 300}}
    })
    command: str
    parameters: Optional[dict] = None
