"""
FastAPI Ground Control Station
Ultra-low latency telemetry ingestion and WebSocket broadcast
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .models import TelemetryPacket, SystemStatus, CommandRequest
from .telemetry_decoder import TelemetryDecoder
from .mock_data_generator import MockDataGenerator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.packets_sent = 0
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        dead_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                self.packets_sent += 1
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                dead_connections.append(connection)
        
        # Remove dead connections
        for connection in dead_connections:
            self.active_connections.remove(connection)


# Global state
manager = ConnectionManager()
decoder = TelemetryDecoder()
mock_generator = None
telemetry_task = None

# Statistics
server_start_time = datetime.utcnow()
latest_packet: TelemetryPacket | None = None
packet_history: List[TelemetryPacket] = []
MAX_HISTORY = 1000  # Keep last 1000 packets in memory


async def process_telemetry_packet(packet_bytes: bytes):
    global latest_packet
    
    # Decode packet
    packet = decoder.decode(packet_bytes)
    
    if packet is None:
        logger.warning("Dropped corrupted packet")
        return
    
    # Update latest packet
    latest_packet = packet
    
    # Add to history (circular buffer)
    packet_history.append(packet)
    if len(packet_history) > MAX_HISTORY:
        packet_history.pop(0)
    
    # Broadcast to WebSocket clients
    await manager.broadcast(packet.to_dict())
    
    # Log every 10th packet to avoid spam
    if decoder.packets_decoded % 10 == 0:
        logger.debug(
            f"Packet #{decoder.packets_decoded}: "
            f"State={packet.flight_state.name}, "
            f"Alt={packet.altitude_m:.1f}m, "
            f"Vel={packet.velocity_ms:.1f}m/s"
        )


async def start_mock_telemetry():
    global mock_generator, telemetry_task
    
    if settings.mock_mode:
        logger.info("Starting mock telemetry generator...")
        mock_generator = MockDataGenerator(data_rate_hz=settings.mock_data_rate)
        telemetry_task = asyncio.create_task(
            mock_generator.start(process_telemetry_packet)
        )
    else:
        logger.info("Mock mode disabled. Waiting for real serial data...")
        # TODO: Implement real serial port reading with pyserial-asyncio


async def stop_mock_telemetry():
    global mock_generator, telemetry_task
    
    if mock_generator:
        mock_generator.stop()
    
    if telemetry_task:
        telemetry_task.cancel()
        try:
            await telemetry_task
        except asyncio.CancelledError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 60)
    logger.info("GITAM CAN-7USAT Ground Control Station")
    logger.info("=" * 60)
    logger.info(f"Server: {settings.host}:{settings.port}")
    logger.info(f"Mock Mode: {settings.mock_mode}")
    logger.info(f"Data Rate: {settings.mock_data_rate} Hz")
    logger.info("=" * 60)
    
    await start_mock_telemetry()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await stop_mock_telemetry()


# Create FastAPI app
app = FastAPI(
    title="GITAM CAN-7USAT Ground Control",
    description="Ultra-low latency telemetry ingestion and WebSocket broadcast",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - redirect to test page"""
    return FileResponse(Path(__file__).parent.parent / "static" / "websocket_test.html")


@app.get("/test")
async def test_page():
    """WebSocket test page"""
    return FileResponse(Path(__file__).parent.parent / "static" / "websocket_test.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Get system status and statistics"""
    uptime = (datetime.utcnow() - server_start_time).total_seconds()
    
    return SystemStatus(
        connected=settings.mock_mode or False,  # TODO: Check real serial connection
        packets_received=decoder.packets_decoded,
        packets_dropped=decoder.packets_dropped,
        last_packet_time=latest_packet.received_at if latest_packet else None,
        websocket_clients=len(manager.active_connections),
        uptime_seconds=uptime
    )


@app.get("/api/telemetry/latest")
async def get_latest_telemetry():
    """Get the most recent telemetry packet"""
    if latest_packet is None:
        raise HTTPException(status_code=404, detail="No telemetry data available")
    
    return latest_packet.to_dict()


@app.get("/api/telemetry/history")
async def get_telemetry_history(limit: int = 100):
    """
    Get recent telemetry history
    
    Args:
        limit: Maximum number of packets to return (default: 100, max: 1000)
    """
    limit = min(limit, MAX_HISTORY)
    recent_packets = packet_history[-limit:]
    
    return {
        "count": len(recent_packets),
        "packets": [p.to_dict() for p in recent_packets]
    }


@app.get("/api/decoder/stats")
async def get_decoder_stats():
    """Get telemetry decoder statistics"""
    return decoder.get_stats()


@app.post("/api/command")
async def send_command(command: CommandRequest):
    """
    Send command to rocket (uplink)
    
    Note: This is a placeholder. Actual implementation requires
    bidirectional XBee communication.
    """
    logger.info(f"Command received: {command.command} with params {command.parameters}")
    
    # TODO: Implement actual command uplink via XBee
    
    return {
        "status": "queued",
        "command": command.command,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/export/csv")
async def export_csv():
    """
    Export telemetry data as CSV
    
    Returns CSV file with all telemetry history
    """
    if not packet_history:
        raise HTTPException(status_code=404, detail="No telemetry data to export")
    
    # Generate CSV content
    csv_lines = [
        "timestamp_ms,flight_state,altitude_m,velocity_ms,"
        "quat_w,quat_x,quat_y,quat_z,gps_lat,gps_lon,received_at"
    ]
    
    for packet in packet_history:
        csv_lines.append(
            f"{packet.timestamp_ms},{packet.flight_state.value},"
            f"{packet.altitude_m},{packet.velocity_ms},"
            f"{packet.quat_w},{packet.quat_x},{packet.quat_y},{packet.quat_z},"
            f"{packet.gps_lat},{packet.gps_lon},"
            f"{packet.received_at.isoformat() if packet.received_at else ''}"
        )
    
    csv_content = "\n".join(csv_lines)
    
    return JSONResponse(
        content={"csv": csv_content, "rows": len(packet_history)},
        headers={
            "Content-Disposition": f"attachment; filename=telemetry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry streaming
    
    Clients connect here to receive live telemetry packets
    """
    await manager.connect(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to telemetry stream",
            "mock_mode": settings.mock_mode,
            "data_rate_hz": settings.mock_data_rate
        })
        
        # Send latest packet if available
        if latest_packet:
            await websocket.send_json(latest_packet.to_dict())
        
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for client messages (e.g., commands, pings)
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")
            
            # Echo back (for ping/pong)
            await websocket.send_json({"echo": data})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
