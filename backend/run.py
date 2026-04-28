"""
Simple runner script for the Ground Control Backend
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 GITAM CAN-7USAT Ground Control Station")
    print("=" * 70)
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"WebSocket: ws://{settings.host}:{settings.port}/ws/telemetry")
    print(f"Mock Mode: {settings.mock_mode}")
    print(f"Data Rate: {settings.mock_data_rate} Hz")
    print("=" * 70)
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
