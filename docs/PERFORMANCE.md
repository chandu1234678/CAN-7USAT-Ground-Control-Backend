# Performance Report — rckt Ground Control

This document contains reproducible performance evidence, methodology, and
high-quality graphs demonstrating key throughput metrics for the backend
Kalman filter and the telemetry encoder/decoder.

## Executive Summary

- The Kalman filter microbenchmark demonstrates sustained single-threaded
  throughput suitable for real-time telemetry ingestion at 10–200 Hz.
- The telemetry encoder/decoder roundtrip benchmark demonstrates packet
  processing throughput that exceeds typical telemetry ingestion rates,
  enabling efficient backfills and log processing.

## Generated Graphs

Graphs are generated into `docs/images/` by the benchmark script.

- `docs/images/backend_perf.svg` — Kalman filter throughput vs iterations
- `docs/images/decoder_perf.svg` — Encoder/decoder roundtrip throughput

Images (open these in a browser for the best fidelity):

![Kalman throughput](images/backend_perf.svg)

![Encoder/decoder throughput](images/decoder_perf.svg)

## Reproducing the Benchmarks

1. Install Python dependencies for the backend:

```powershell
cd backend
python -m pip install -r requirements.txt
```

2. Run the benchmark harness (writes SVGs to `docs/images`):

```powershell
python backend/benchmarks/run_benchmarks.py
```

3. Open the generated SVG files in a browser or include them in reports.

## Methodology

- Use `time.perf_counter()` for high-resolution wall-clock timings.
- Perform multiple iteration counts to show how throughput behaves at small
  and larger workloads.
- Use matplotlib to create vector (SVG) output for publication-quality
  graphics.

## Next Steps

- Add scheduled CI job to run a lightweight benchmark and upload artifacts
  for historical tracking.
- Record machine profile metadata (CPU, OS, Python build) alongside the
  generated images for traceability.

