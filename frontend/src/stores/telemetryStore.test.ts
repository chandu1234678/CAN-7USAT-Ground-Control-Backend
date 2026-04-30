import { useTelemetryStore } from './telemetryStore';
import { beforeEach, describe, expect, it } from 'vitest';

const makePacket = (overrides: Partial<ReturnType<typeof basePacket>> = {}) => ({
  ...basePacket(),
  ...overrides,
});

const basePacket = () => ({
  sync_byte: 0xaa,
  timestamp_ms: 1000,
  flight_state: 2,
  flight_state_name: 'COAST',
  altitude_m: 10,
  velocity_ms: 5,
  quat_w: 1,
  quat_x: 0,
  quat_y: 0,
  quat_z: 0,
  gps_lat: 26.74,
  gps_lon: 83.887,
  checksum_xor: 123,
  received_at: new Date().toISOString(),
});

describe('telemetryStore', () => {
  beforeEach(() => {
    useTelemetryStore.setState({
      ws: null,
      connected: false,
      connecting: false,
      latestPacket: null,
      systemStatus: null,
      altitudeHistory: [],
      velocityHistory: [],
      packetsReceived: 0,
      maxAltitude: 0,
      maxVelocity: 0,
    });
  });

  it('updates packet, history, and max values', () => {
    const state = useTelemetryStore.getState();

    state.updatePacket(makePacket({ timestamp_ms: 1000, altitude_m: 10, velocity_ms: 5 }));
    state.updatePacket(makePacket({ timestamp_ms: 2000, altitude_m: 20, velocity_ms: -8 }));

    const updated = useTelemetryStore.getState();
    expect(updated.latestPacket?.timestamp_ms).toBe(2000);
    expect(updated.packetsReceived).toBe(2);
    expect(updated.altitudeHistory).toHaveLength(2);
    expect(updated.velocityHistory).toHaveLength(2);
    expect(updated.maxAltitude).toBe(20);
    expect(updated.maxVelocity).toBe(8);
  });

  it('updates system status', () => {
    const state = useTelemetryStore.getState();

    state.updateStatus({
      connected: true,
      packets_received: 10,
      packets_dropped: 1,
      last_packet_time: new Date().toISOString(),
      websocket_clients: 3,
      uptime_seconds: 5,
    });

    expect(useTelemetryStore.getState().systemStatus?.connected).toBe(true);
  });
});
