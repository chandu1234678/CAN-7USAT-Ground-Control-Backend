"""
Mock telemetry data generator for testing without hardware
Simulates realistic flight profile based on rckt_kushinagar.csv
"""

import asyncio
import math
import logging
from datetime import datetime
from .models import TelemetryPacket, FlightState
from .telemetry_decoder import TelemetryDecoder

logger = logging.getLogger(__name__)


class MockDataGenerator:
    """
    Generates realistic telemetry data simulating a rocket flight
    Based on OpenRocket simulation data from rckt_kushinagar.csv
    """
    
    def __init__(self, data_rate_hz: int = 10):
        """
        Initialize mock data generator
        
        Args:
            data_rate_hz: Telemetry generation rate in Hz
        """
        self.data_rate_hz = data_rate_hz
        self.interval_sec = 1.0 / data_rate_hz
        
        self.decoder = TelemetryDecoder()
        self.running = False
        self.start_time = None
        
        # Flight profile parameters (from rckt_kushinagar.csv)
        self.LIFTOFF_TIME = 0.079  # seconds
        self.BURNOUT_TIME = 1.8    # seconds
        self.APOGEE_TIME = 58.0    # seconds (estimated)
        self.LANDING_TIME = 120.0  # seconds (estimated)
        
        self.MAX_ALTITUDE = 162.0  # meters (from simulation)
        self.MAX_VELOCITY = 92.0   # m/s (from simulation)
        
        # GPS coordinates (Kushinagar launch site)
        self.BASE_LAT = 26.74
        self.BASE_LON = 83.887
        
        logger.info(f"Mock data generator initialized at {data_rate_hz} Hz")
    
    async def generate_packet(self, elapsed_time: float) -> bytes:
        """
        Generate a single telemetry packet for given flight time
        
        Args:
            elapsed_time: Time since launch in seconds
            
        Returns:
            46-byte binary telemetry packet
        """
        # Determine flight state
        flight_state = self._get_flight_state(elapsed_time)
        
        # Calculate altitude (parabolic trajectory)
        altitude = self._calculate_altitude(elapsed_time)
        
        # Calculate velocity (derivative of altitude)
        velocity = self._calculate_velocity(elapsed_time)
        
        # Calculate quaternion (simulate rotation)
        quat_w, quat_x, quat_y, quat_z = self._calculate_quaternion(elapsed_time)
        
        # Calculate GPS drift (simulate wind)
        gps_lat, gps_lon = self._calculate_gps(elapsed_time, altitude)
        
        # Create packet
        packet = TelemetryPacket(
            sync_byte=0xAA,
            timestamp_ms=int(elapsed_time * 1000),
            flight_state=flight_state,
            altitude_m=round(altitude, 2),
            velocity_ms=round(velocity, 2),
            quat_w=round(quat_w, 4),
            quat_x=round(quat_x, 4),
            quat_y=round(quat_y, 4),
            quat_z=round(quat_z, 4),
            gps_lat=round(gps_lat, 6),
            gps_lon=round(gps_lon, 6),
            checksum_xor=0,  # Will be calculated by encoder
            received_at=datetime.utcnow()
        )
        
        # Encode to binary
        binary_packet = self.decoder.encode(packet)
        
        return binary_packet
    
    def _get_flight_state(self, t: float) -> FlightState:
        """Determine flight state based on elapsed time"""
        if t < self.LIFTOFF_TIME:
            return FlightState.PRE_FLIGHT
        elif t < self.BURNOUT_TIME:
            return FlightState.BOOST
        elif t < self.APOGEE_TIME:
            return FlightState.COAST
        elif t < self.APOGEE_TIME + 1.0:
            return FlightState.APOGEE
        elif t < self.LANDING_TIME:
            return FlightState.DESCENT
        else:
            return FlightState.LANDED
    
    def _calculate_altitude(self, t: float) -> float:
        """
        Calculate altitude using realistic flight profile
        Boost phase: quadratic acceleration
        Coast phase: parabolic trajectory
        Descent phase: exponential decay (parachute)
        """
        if t < self.LIFTOFF_TIME:
            return 0.0
        
        elif t < self.BURNOUT_TIME:
            # Boost phase: quadratic acceleration
            # From simulation: reaches ~80m at burnout
            progress = (t - self.LIFTOFF_TIME) / (self.BURNOUT_TIME - self.LIFTOFF_TIME)
            return 80.0 * progress ** 2
        
        elif t < self.APOGEE_TIME:
            # Coast phase: parabolic trajectory to apogee
            # From simulation: apogee at ~162m
            t_coast = t - self.BURNOUT_TIME
            t_coast_total = self.APOGEE_TIME - self.BURNOUT_TIME
            progress = t_coast / t_coast_total
            
            # Parabolic curve: starts at 80m, peaks at 162m
            h0 = 80.0
            h_max = self.MAX_ALTITUDE
            altitude = h0 + (h_max - h0) * (1 - (1 - progress) ** 2)
            return altitude
        
        elif t < self.LANDING_TIME:
            # Descent phase: exponential decay with parachute
            t_descent = t - self.APOGEE_TIME
            t_descent_total = self.LANDING_TIME - self.APOGEE_TIME
            
            # Exponential decay from apogee to ground
            altitude = self.MAX_ALTITUDE * math.exp(-2.5 * t_descent / t_descent_total)
            return max(0.0, altitude)
        
        else:
            # Landed
            return 0.0
    
    def _calculate_velocity(self, t: float) -> float:
        """
        Calculate vertical velocity (derivative of altitude)
        Positive = ascending, Negative = descending
        """
        dt = 0.01  # Small time step for numerical derivative
        alt_now = self._calculate_altitude(t)
        alt_next = self._calculate_altitude(t + dt)
        velocity = (alt_next - alt_now) / dt
        
        return velocity
    
    def _calculate_quaternion(self, t: float) -> tuple[float, float, float, float]:
        """
        Calculate quaternion representing rocket orientation
        Simulates pitch-over maneuver and spin stabilization
        """
        if t < self.LIFTOFF_TIME:
            # Vertical on pad
            return (1.0, 0.0, 0.0, 0.0)
        
        elif t < self.BURNOUT_TIME:
            # Slight pitch-over during boost
            pitch_angle = math.radians(5.0 * (t - self.LIFTOFF_TIME) / self.BURNOUT_TIME)
            quat_w = math.cos(pitch_angle / 2)
            quat_x = math.sin(pitch_angle / 2)
            quat_y = 0.0
            quat_z = 0.0
            return (quat_w, quat_x, quat_y, quat_z)
        
        else:
            # Coast/descent: slow rotation
            roll_angle = math.radians(10.0 * (t - self.BURNOUT_TIME))
            pitch_angle = math.radians(5.0)
            
            # Simplified quaternion (roll + pitch)
            quat_w = math.cos(roll_angle / 2) * math.cos(pitch_angle / 2)
            quat_x = math.sin(pitch_angle / 2)
            quat_y = 0.0
            quat_z = math.sin(roll_angle / 2) * math.cos(pitch_angle / 2)
            
            return (quat_w, quat_x, quat_y, quat_z)
    
    def _calculate_gps(self, t: float, altitude: float) -> tuple[float, float]:
        """
        Calculate GPS coordinates with simulated wind drift
        """
        if t < self.LIFTOFF_TIME:
            return (self.BASE_LAT, self.BASE_LON)
        
        # Simulate wind drift (1 m/s eastward)
        wind_speed_ms = 1.0
        drift_distance_m = wind_speed_ms * (t - self.LIFTOFF_TIME)
        
        # Convert meters to degrees (approximate)
        # 1 degree latitude ≈ 111,000 meters
        # 1 degree longitude ≈ 111,000 * cos(latitude) meters
        lat_offset = 0.0  # No north/south drift
        lon_offset = drift_distance_m / (111000.0 * math.cos(math.radians(self.BASE_LAT)))
        
        gps_lat = self.BASE_LAT + lat_offset
        gps_lon = self.BASE_LON + lon_offset
        
        return (gps_lat, gps_lon)
    
    async def start(self, callback):
        """
        Start generating mock telemetry data
        
        Args:
            callback: Async function to call with each packet (bytes)
        """
        self.running = True
        loop = asyncio.get_running_loop()
        self.start_time = loop.time()
        
        logger.info("Mock data generator started")
        
        try:
            while self.running:
                # Calculate elapsed time
                current_time = loop.time()
                elapsed_time = current_time - self.start_time
                
                # Generate packet
                packet_bytes = await self.generate_packet(elapsed_time)
                
                # Send to callback
                await callback(packet_bytes)
                
                # Wait for next interval
                await asyncio.sleep(self.interval_sec)
                
        except asyncio.CancelledError:
            logger.info("Mock data generator cancelled")
            self.running = False
        except Exception as exc:
            logger.error(f"Mock data generator error: {exc}")
            self.running = False
    
    def stop(self):
        """Stop generating mock data"""
        self.running = False
        logger.info("Mock data generator stopped")
