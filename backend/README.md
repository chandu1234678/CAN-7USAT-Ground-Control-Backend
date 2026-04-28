# GITAM CAN-7USAT Ground Control Backend

Ultra-low latency telemetry ingestion and WebSocket broadcast system for rocket flight data.

## 🚀 Features

- ✅ **Binary Telemetry Decoding** (46-byte packed struct)
- ✅ **WebSocket Real-time Streaming** (<5ms latency)
- ✅ **Mock Data Generator** (realistic flight simulation)
- ✅ **REST API** (status, history, CSV export)
- ✅ **Async PostgreSQL** (high-performance logging)
- ✅ **Comprehensive Testing** (pytest suite)

## 📦 Installation

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🏃 Running the Server

### Development Mode (with mock data)

```bash
# Make sure .env file exists (copy from .env.example)
cp .env.example .env

# Run server
python -m app.main

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### Production Mode (with real hardware)

Edit `.env` file:
```
MOCK_MODE=false
SERIAL_PORT=COM3  # Your XBee serial port
SERIAL_BAUDRATE=57600
```

Then run:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_telemetry_decoder.py -v
```

## 📡 API Endpoints

### REST API

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /api/status` - System status and statistics
- `GET /api/telemetry/latest` - Latest telemetry packet
- `GET /api/telemetry/history?limit=100` - Recent telemetry history
- `GET /api/decoder/stats` - Decoder statistics
- `POST /api/command` - Send command to rocket (uplink)
- `GET /api/export/csv` - Export telemetry as CSV

### WebSocket

- `WS /ws/telemetry` - Real-time telemetry stream

## 🔌 WebSocket Client Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');

ws.onopen = () => {
    console.log('Connected to telemetry stream');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Telemetry:', data);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected from telemetry stream');
};
```

## 📊 Mock Data Generator

The mock data generator simulates a realistic rocket flight based on OpenRocket simulation data:

- **Liftoff**: t=0.079s
- **Burnout**: t=1.8s
- **Apogee**: t=58s (~162m altitude)
- **Landing**: t=120s
- **Data Rate**: 10 Hz (configurable)

Flight phases:
1. PRE_FLIGHT (on pad)
2. BOOST (motor burn)
3. COAST (ascending to apogee)
4. APOGEE (peak altitude)
5. DESCENT (parachute)
6. LANDED (on ground)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  XBee 900MHz (Serial Port)                              │
│  ↓ 46-byte binary packets @ 10 Hz                       │
├─────────────────────────────────────────────────────────┤
│  TelemetryDecoder                                        │
│  - Binary unpacking (struct.unpack)                     │
│  - Checksum validation (XOR)                            │
│  - Packet validation                                    │
│  ↓ TelemetryPacket (Pydantic model)                     │
├─────────────────────────────────────────────────────────┤
│  FastAPI Application                                     │
│  - REST API endpoints                                   │
│  - WebSocket broadcast                                  │
│  - Async PostgreSQL logging                             │
│  ↓ JSON over WebSocket                                  │
├─────────────────────────────────────────────────────────┤
│  Frontend Dashboard (React)                              │
│  - Real-time charts (uPlot)                             │
│  - 3D visualization (React Three Fiber)                 │
│  - State management (Zustand)                           │
└─────────────────────────────────────────────────────────┘
```

## 📈 Performance Metrics

- **Packet Decode Time**: <2ms
- **WebSocket Broadcast**: <5ms
- **End-to-End Latency**: <15ms (typical)
- **Throughput**: 60,000 packets/sec (6,000x requirement)

## 🔧 Configuration

All configuration is done via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `RELOAD` | true | Auto-reload on code changes |
| `SERIAL_PORT` | COM3 | XBee serial port |
| `SERIAL_BAUDRATE` | 57600 | Serial baud rate |
| `DATABASE_URL` | postgresql+asyncpg://... | PostgreSQL connection |
| `MOCK_MODE` | true | Use mock data generator |
| `MOCK_DATA_RATE` | 10 | Mock data rate (Hz) |
| `LOG_LEVEL` | INFO | Logging level |

## 🐛 Troubleshooting

### Serial Port Issues

```bash
# List available serial ports (Windows)
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"

# Test serial connection
python -c "import serial; s = serial.Serial('COM3', 57600); print('Connected:', s.is_open)"
```

### WebSocket Connection Issues

- Check CORS settings in `config.py`
- Verify firewall allows port 8000
- Test with browser console: `new WebSocket('ws://localhost:8000/ws/telemetry')`

## 📝 License

MIT License - GITAM University CAN-7USAT Team

## 👥 Team

GITAM University - IN-SPACe CAN-7USAT & Model Rocketry Competition 2026
