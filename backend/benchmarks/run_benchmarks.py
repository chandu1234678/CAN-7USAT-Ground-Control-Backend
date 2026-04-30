"""Benchmark harness for Kalman filter and decoder."""

from pathlib import Path
import sys

# Ensure backend package root is on sys.path so `import app.*` works when this
# script is invoked directly from the repo root or other working directories.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import time
import math
import numpy as np
import matplotlib.pyplot as plt

from app.kalman_filter import KalmanFilter
from app.telemetry_decoder import TelemetryDecoder
from app.models import TelemetryPacket, FlightState
from datetime import datetime

OUT_DIR = Path(__file__).resolve().parents[1].parent / 'docs' / 'images'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Kalman benchmark
def bench_kalman():
    kf = KalmanFilter(initial_altitude=0.0, initial_velocity=0.0)
    # Work sizes
    sizes = [1000, 5000, 10000, 20000, 50000]
    ops_per_sec = []

    for n in sizes:
        start = time.perf_counter()
        for i in range(n):
            # small dt steps with slight varying accel
            kf.predict(dt=0.01, acceleration=9.81 + 0.5 * math.sin(i * 0.001))
            if i % 10 == 0:
                kf.update_altitude(measured_altitude=0.1 * math.sin(i * 0.01))
        elapsed = time.perf_counter() - start
        ops = n
        ops_per_sec.append(ops / elapsed)
        # Reset state to keep runs comparable
        kf.reset(0.0, 0.0)

    plt.figure(figsize=(8,4))
    plt.plot(sizes, ops_per_sec, marker='o')
    plt.xlabel('Iterations')
    plt.ylabel('Operations per second')
    plt.title('Kalman Filter Throughput')
    plt.grid(True)
    out = OUT_DIR / 'backend_perf.svg'
    plt.tight_layout()
    plt.savefig(out, format='svg')
    print(f'Wrote {out}')

# Decoder benchmark
def bench_decoder():
    dec = TelemetryDecoder()
    pkt = TelemetryPacket(
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
        checksum_xor=0,
        received_at=datetime.utcnow(),
    )

    sizes = [1000, 5000, 10000, 20000]
    rps = []
    for n in sizes:
        start = time.perf_counter()
        for i in range(n):
            b = dec.encode(pkt)
            p = dec.decode(b)
            if p is None:
                raise RuntimeError('decode failed')
        elapsed = time.perf_counter() - start
        rps.append(n / elapsed)

    plt.figure(figsize=(8,4))
    plt.plot(sizes, rps, marker='o', color='C1')
    plt.xlabel('Roundtrip iterations')
    plt.ylabel('Roundtrips per second')
    plt.title('Telemetry Encode/Decode Throughput')
    plt.grid(True)
    out = OUT_DIR / 'decoder_perf.svg'
    plt.tight_layout()
    plt.savefig(out, format='svg')
    print(f'Wrote {out}')


if __name__ == '__main__':
    print('Running Kalman benchmark...')
    bench_kalman()
    print('Running decoder benchmark...')
    bench_decoder()
    print('Benchmarks complete.')
