
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime, select

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class TelemetryRecord(Base):
    __tablename__ = "telemetry"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp_ms = Column(Integer, nullable=False, index=True)
    flight_state = Column(Integer, nullable=False)
    altitude_m = Column(Float, nullable=False)
    velocity_ms = Column(Float, nullable=False)
    quat_w = Column(Float, nullable=False)
    quat_x = Column(Float, nullable=False)
    quat_y = Column(Float, nullable=False)
    quat_z = Column(Float, nullable=False)
    gps_lat = Column(Float, nullable=False)
    gps_lon = Column(Float, nullable=False)
    checksum_xor = Column(Integer, nullable=False)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<TelemetryRecord(id={self.id}, timestamp={self.timestamp_ms}, state={self.flight_state})>"


class DatabaseManager:
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.session_maker = None
        self.enabled = bool(self.database_url and self.database_url != "")
        
        if self.enabled:
            logger.info(f"Database enabled: {self.database_url.split('@')[0]}@...")
        else:
            logger.info("Database disabled (no DATABASE_URL configured)")
    
    async def initialize(self):
        if not self.enabled:
            return
        
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=10,
                max_overflow=20
            )
            
            # Create session maker
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.enabled = False
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    async def save_telemetry(self, packet_data: dict) -> bool:
        """
        Save telemetry packet to database
        
        Args:
            packet_data: Dictionary with telemetry data
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.enabled or not self.session_maker:
            return False
        
        try:
            async with self.session_maker() as session:
                record = TelemetryRecord(
                    timestamp_ms=packet_data["timestamp_ms"],
                    flight_state=packet_data["flight_state"],
                    altitude_m=packet_data["altitude_m"],
                    velocity_ms=packet_data["velocity_ms"],
                    quat_w=packet_data["quat_w"],
                    quat_x=packet_data["quat_x"],
                    quat_y=packet_data["quat_y"],
                    quat_z=packet_data["quat_z"],
                    gps_lat=packet_data["gps_lat"],
                    gps_lon=packet_data["gps_lon"],
                    checksum_xor=packet_data["checksum_xor"],
                    received_at=datetime.fromisoformat(packet_data["received_at"]) if packet_data.get("received_at") else datetime.utcnow()
                )
                
                session.add(record)
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save telemetry: {e}")
            return False
    
    async def get_recent_telemetry(self, limit: int = 100) -> List[dict]:
        """
        Get recent telemetry records
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of telemetry dictionaries
        """
        if not self.enabled or not self.session_maker:
            return []
        
        try:
            async with self.session_maker() as session:
                result = await session.execute(
                    select(TelemetryRecord)
                    .order_by(TelemetryRecord.received_at.desc())
                    .limit(limit)
                )
                records = result.scalars().all()
                
                return [
                    {
                        "id": r.id,
                        "timestamp_ms": r.timestamp_ms,
                        "flight_state": r.flight_state,
                        "altitude_m": r.altitude_m,
                        "velocity_ms": r.velocity_ms,
                        "quat_w": r.quat_w,
                        "quat_x": r.quat_x,
                        "quat_y": r.quat_y,
                        "quat_z": r.quat_z,
                        "gps_lat": r.gps_lat,
                        "gps_lon": r.gps_lon,
                        "checksum_xor": r.checksum_xor,
                        "received_at": r.received_at.isoformat()
                    }
                    for r in records
                ]
                
        except Exception as e:
            logger.error(f"Failed to get telemetry: {e}")
            return []
    
    async def get_flight_summary(self) -> Optional[dict]:
        """
        Get flight summary statistics
        
        Returns:
            Dictionary with flight statistics or None
        """
        if not self.enabled or not self.session_maker:
            return None
        
        try:
            async with self.session_maker() as session:
                result = await session.execute(
                    select(TelemetryRecord).order_by(TelemetryRecord.received_at.asc())
                )
                records = result.scalars().all()
                
                if not records:
                    return None
                
                max_altitude = max(r.altitude_m for r in records)
                max_velocity = max(r.velocity_ms for r in records)
                flight_duration = (records[-1].received_at - records[0].received_at).total_seconds()
                
                return {
                    "total_packets": len(records),
                    "max_altitude_m": max_altitude,
                    "max_velocity_ms": max_velocity,
                    "flight_duration_s": flight_duration,
                    "start_time": records[0].received_at.isoformat(),
                    "end_time": records[-1].received_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get flight summary: {e}")
            return None


# Global database manager instance
db_manager = DatabaseManager()
