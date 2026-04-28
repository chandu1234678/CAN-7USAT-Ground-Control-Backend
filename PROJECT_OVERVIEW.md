# GITAM CAN-7USAT & Model Rocketry Competition 2026
## Mission-Critical Flight Avionics & Ground Control System

---

## 📋 MISSION PARAMETERS (from rckt_kushinagar.csv)

### Flight Profile Analysis
- **Target Altitude**: 1000m (Competition requirement)
- **Simulated Apogee**: ~162m (from OpenRocket baseline)
- **Max Velocity**: ~92 m/s
- **Flight Duration**: ~58 seconds (to apogee)
- **Launch Location**: Kushinagar (26.74°N, 83.887°E, 83.5m ASL)
- **Rocket Mass**: 11.01 kg (wet), 8.17 kg (dry)
- **Motor**: Solid propellant, ~2.9kg, burn time ~1.8s

### Critical Events Timeline
1. **IGNITION**: t=0s
2. **LIFTOFF**: t=0.079s
3. **LAUNCHROD CLEAR**: t=0.431s
4. **APOGEE**: ~t=58s (primary chute deployment)
5. **SECONDARY TRIGGER**: 600m AGL (mandatory)
6. **LANDING**: Variable

---

## 🎯 COMPETITION REQUIREMENTS (IN-SPACe CAN-7USAT 2026)

### Mandatory Systems
1. **NavIC GNSS Receiver** (Indian Regional Navigation Satellite System)
2. **Dual Barometric Altimeters** (redundancy for altitude triggers)
3. **6-Axis IMU/Gyroscope** (attitude determination)
4. **SD Card Data Logger** (mandatory onboard backup)
5. **900MHz XBee Telemetry** (real-time downlink)
6. **Dual Parachute Recovery System**
   - Primary: Deploy at apogee
   - Secondary: Deploy at exactly 600m AGL

### Telemetry Requirements
- **Minimum Transmission Rate**: 1 Hz
- **Data Integrity**: Checksum validation mandatory
- **Packet Structure**: Binary (46-byte packed struct)

---

## 🏗️ SYSTEM ARCHITECTURE

### 1. EMBEDDED FLIGHT SOFTWARE
**Platform**: Teensy 4.1 (ARM Cortex-M7 @ 600MHz)  
**RTOS**: FreeRTOS  
**Language**: C++

#### Core Requirements
- ✅ **Non-blocking architecture** (NO `delay()` functions)
- ✅ **Hardware interrupt-driven sensor polling**
- ✅ **State machine**: PRE_FLIGHT → BOOST → COAST → APOGEE → DESCENT → LANDED
- ✅ **Autonomous event triggers**:
  - Primary chute at apogee detection (velocity crosses zero)
  - Secondary chute at 600m AGL (barometric)
- ✅ **SD card high-frequency logging** (100Hz+)
- ✅ **Binary telemetry serialization** (46-byte packet)

#### 46-Byte Telemetry Packet Structure
```c
__attribute__((packed)) struct TelemetryPacket {
    uint8_t  sync_byte;      // 0xAA
    uint32_t timestamp_ms;   // Milliseconds since boot
    uint8_t  flight_state;   // 0=PRE, 1=BOOST, 2=COAST, 3=APOGEE, 4=DESCENT, 5=LANDED
    float    altitude_m;     // Barometric altitude AGL
    float    velocity_ms;    // Vertical velocity
    float    quat_w;         // Quaternion W (from IMU)
    float    quat_x;         // Quaternion X
    float    quat_y;         // Quaternion Y
    float    quat_z;         // Quaternion Z
    float    gps_lat;        // NavIC latitude
    float    gps_lon;        // NavIC longitude
    uint8_t  checksum_xor;   // XOR of all bytes
};
// Total: 1 + 4 + 1 + 4*9 + 1 = 46 bytes
```

---

### 2. GROUND CONTROL BACKEND
**Platform**: Python 3.11+  
**Framework**: FastAPI  
**Database**: PostgreSQL (async)

#### Core Components
- ✅ **Serial Ingestion**: `pyserial-asyncio` (non-blocking XBee read)
- ✅ **Binary Decoder**: `struct.unpack('<B I B f f f f f f f f B', raw_bytes)`
- ✅ **Checksum Validation**: XOR verification, drop corrupted packets
- ✅ **WebSocket Broadcast**: Real-time push to dashboard (sub-millisecond latency)
- ✅ **Async Database**: `asyncpg` for PostgreSQL writes
- ✅ **ML Anomaly Detection**: PyTorch inference comparing live data vs. `rckt_kushinagar.csv`

#### API Endpoints
```python
GET  /api/telemetry/latest      # Last packet
GET  /api/telemetry/stream      # WebSocket connection
GET  /api/flight/state          # Current flight state
POST /api/command/arm           # Uplink command (if implemented)
GET  /api/export/csv            # Download flight log
```

---

### 3. REAL-TIME DASHBOARD
**Platform**: React 18 + Vite  
**State Management**: Zustand (high-frequency updates)  
**Visualization**: uPlot (Canvas-based, 60 FPS)  
**3D Rendering**: React Three Fiber (IMU quaternion → 3D rocket mesh)

#### Dashboard Features
1. **Live Telemetry Plots**
   - Altitude vs. Time
   - Velocity vs. Time
   - Acceleration vs. Time
2. **3D Rocket Visualization**
   - Real-time orientation from IMU quaternions
   - Pitch, Roll, Yaw indicators
3. **State Machine Display**
   - Visual alerts for flight phases
   - Event triggers (chute deployments)
4. **System Diagnostics**
   - Battery voltage
   - XBee RSSI (signal strength)
   - Pyro continuity checks
5. **Command Uplink Panel**
   - Vehicle Arm/Disarm
   - Manual chute deploy (emergency)
   - Abort sequence

---

## 📁 PROJECT STRUCTURE

```
rckt/
├── embedded/                    # Teensy 4.1 Flight Computer
│   ├── src/
│   │   ├── main.cpp            # FreeRTOS task initialization
│   │   ├── state_machine.cpp   # Flight state logic
│   │   ├── sensors/
│   │   │   ├── navic_gps.cpp   # NavIC GNSS driver
│   │   │   ├── barometer.cpp   # Dual altimeter (BMP388)
│   │   │   └── imu.cpp         # 6-axis IMU (MPU6050/BNO085)
│   │   ├── telemetry.cpp       # 46-byte packet serialization
│   │   ├── sd_logger.cpp       # High-speed SD card writes
│   │   └── recovery.cpp        # Parachute deployment logic
│   └── platformio.ini          # PlatformIO config
│
├── backend/                     # Python FastAPI Ground Station
│   ├── main.py                 # FastAPI app entry
│   ├── serial_ingest.py        # XBee serial reader (async)
│   ├── telemetry_decoder.py    # Binary packet parser
│   ├── websocket_server.py     # Real-time broadcast
│   ├── database.py             # PostgreSQL async ORM
│   ├── ml_anomaly.py           # PyTorch inference
│   └── requirements.txt
│
├── dashboard/                   # React + Vite Frontend
│   ├── src/
│   │   ├── App.tsx             # Main dashboard layout
│   │   ├── stores/
│   │   │   └── telemetryStore.ts  # Zustand state
│   │   ├── components/
│   │   │   ├── AltitudePlot.tsx   # uPlot altitude chart
│   │   │   ├── VelocityPlot.tsx   # uPlot velocity chart
│   │   │   ├── Rocket3D.tsx       # React Three Fiber 3D model
│   │   │   ├── StateIndicator.tsx # Flight state display
│   │   │   └── Diagnostics.tsx    # System health panel
│   │   └── hooks/
│   │       └── useWebSocket.ts    # WebSocket connection
│   ├── package.json
│   └── vite.config.ts
│
├── docs/
│   ├── GITAM_CAN7USAT_Proposal_2026.pdf
│   ├── GITAM_IN-SPACe_Proposal-docx.pdf
│   ├── Rocketry proposal.pdf
│   └── rckt_kushinagar.csv     # OpenRocket simulation baseline
│
└── README.md
```

---

## 🚀 DEVELOPMENT ROADMAP

### Phase 1: Embedded Flight Computer (Week 1-2)
- [ ] FreeRTOS task structure
- [ ] Sensor drivers (NavIC, Barometer, IMU)
- [ ] State machine implementation
- [ ] SD card logger
- [ ] Telemetry packet serialization
- [ ] XBee transmission

### Phase 2: Ground Control Backend (Week 2-3)
- [ ] FastAPI server setup
- [ ] Serial ingestion (pyserial-asyncio)
- [ ] Binary packet decoder
- [ ] PostgreSQL schema + async writes
- [ ] WebSocket broadcast
- [ ] ML anomaly detection hook

### Phase 3: Dashboard Frontend (Week 3-4)
- [ ] React + Vite project setup
- [ ] Zustand store for telemetry
- [ ] WebSocket connection hook
- [ ] uPlot altitude/velocity charts
- [ ] React Three Fiber 3D rocket
- [ ] State indicator + diagnostics

### Phase 4: Integration & Testing (Week 4-5)
- [ ] End-to-end system test
- [ ] Latency benchmarking (<10ms target)
- [ ] Packet loss handling
- [ ] Failsafe testing (sensor failures)
- [ ] Ground station UI/UX refinement

### Phase 5: Field Testing (Week 5-6)
- [ ] Static fire test (motor ignition)
- [ ] Tethered flight test (10m altitude)
- [ ] Full flight test (100m altitude)
- [ ] Competition readiness review

---

## 🔧 HARDWARE SPECIFICATIONS

### Flight Computer Stack
- **MCU**: Teensy 4.1 (ARM Cortex-M7 @ 600MHz, 1MB RAM, 8MB Flash)
- **GPS**: NavIC-compatible receiver (e.g., Quectel L89)
- **Barometer**: Dual BMP388 (±0.5m accuracy)
- **IMU**: BNO085 (9-DOF with sensor fusion) or MPU6050
- **Telemetry**: XBee Pro S2C (900MHz, 1.6km range)
- **Storage**: MicroSD card (32GB, Class 10)
- **Power**: 2S LiPo (7.4V, 2200mAh)
- **Pyro Channels**: 2x MOSFET-driven e-matches

### Ground Station Hardware
- **Antenna**: XBee Pro S2C with 5dBi omni antenna
- **Computer**: Laptop (Windows/Linux) with USB-Serial adapter
- **Display**: 1920x1080 minimum for dashboard

---

## 📊 KEY PERFORMANCE INDICATORS

### Embedded System
- **Sensor Polling Rate**: 100 Hz (IMU), 10 Hz (GPS), 50 Hz (Barometer)
- **SD Card Write Rate**: 100 Hz (all sensors)
- **Telemetry Transmission**: 10 Hz (XBee)
- **State Machine Latency**: <5ms (event detection to action)

### Ground Station
- **Packet Decode Time**: <1ms
- **WebSocket Latency**: <5ms (backend → frontend)
- **Dashboard Render Rate**: 60 FPS (uPlot + React Three Fiber)
- **Database Write Rate**: Async, non-blocking

---

## ⚠️ SAFETY & COMPLIANCE

1. **Redundancy**: Dual barometers, dual pyro channels
2. **Failsafes**: Automatic chute deployment on loss of signal (>5s)
3. **Range Safety**: Geofence limits (abort if >2km lateral)
4. **Frequency Compliance**: 900MHz ISM band (license-free in India)
5. **Airspace Clearance**: DGCA notification for >300m flights

---

## 📞 CONTACT & TEAM

**Institution**: GITAM University  
**Competition**: IN-SPACe CAN-7USAT & Model Rocketry 2026  
**Location**: Kushinagar Launch Site (26.74°N, 83.887°E)

---

**STATUS**: Architecture Initialized ✅  
**NEXT STEP**: Generate first module (embedded/backend/dashboard)
