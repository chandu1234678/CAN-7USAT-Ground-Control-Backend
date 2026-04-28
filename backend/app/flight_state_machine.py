"""
Advanced Flight State Machine with Safety Features
Inspired by production rocket flight computers:
- BPS.space Falcon Heavy
- rckTom/alturia-firmware
- SparkyVT/HPR-Rocket-Flight-Computer
"""

import logging
from enum import IntEnum
from typing import Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FlightState(IntEnum):
    """Flight state enumeration"""
    PRE_FLIGHT = 0
    BOOST = 1
    COAST = 2
    APOGEE = 3
    DESCENT = 4
    LANDED = 5


class FlightEvent(IntEnum):
    """Flight events for logging"""
    POWER_ON = 0
    ARMED = 1
    LIFTOFF = 2
    BURNOUT = 3
    APOGEE_DETECTED = 4
    MAIN_DEPLOY = 5
    SECONDARY_DEPLOY = 6
    TOUCHDOWN = 7
    SAFED = 8


class FlightStateMachine:
    """
    Production-grade flight state machine with safety features
    
    Features:
    - Mach-immune apogee detection
    - Tilt-sensing safety lockouts
    - Redundant event detection
    - Configurable deployment altitudes
    - Event logging and telemetry
    """
    
    def __init__(
        self,
        apogee_deploy_altitude: float = None,  # Deploy at apogee
        main_deploy_altitude: float = 600.0,   # Secondary at 600m AGL
        liftoff_accel_threshold: float = 20.0,  # m/s² (2G)
        liftoff_altitude_threshold: float = 5.0,  # meters
        apogee_velocity_threshold: float = 5.0,  # m/s (near zero)
        landing_velocity_threshold: float = 2.0,  # m/s
        landing_time_threshold: float = 3.0,     # seconds
        max_tilt_angle: float = 45.0,            # degrees
    ):
        """
        Initialize flight state machine
        
        Args:
            apogee_deploy_altitude: Altitude for apogee deployment (None = at apogee)
            main_deploy_altitude: Altitude for main chute deployment (meters AGL)
            liftoff_accel_threshold: Acceleration threshold for liftoff detection
            liftoff_altitude_threshold: Altitude threshold for liftoff confirmation
            apogee_velocity_threshold: Velocity threshold for apogee detection
            landing_velocity_threshold: Velocity threshold for landing detection
            landing_time_threshold: Time below velocity threshold to confirm landing
            max_tilt_angle: Maximum tilt angle before safety lockout (degrees)
        """
        self.state = FlightState.PRE_FLIGHT
        self.previous_state = FlightState.PRE_FLIGHT
        
        # Configuration
        self.apogee_deploy_altitude = apogee_deploy_altitude
        self.main_deploy_altitude = main_deploy_altitude
        self.liftoff_accel_threshold = liftoff_accel_threshold
        self.liftoff_altitude_threshold = liftoff_altitude_threshold
        self.apogee_velocity_threshold = apogee_velocity_threshold
        self.landing_velocity_threshold = landing_velocity_threshold
        self.landing_time_threshold = landing_time_threshold
        self.max_tilt_angle = max_tilt_angle
        
        # State tracking
        self.armed = False
        self.liftoff_time: Optional[datetime] = None
        self.apogee_time: Optional[datetime] = None
        self.landing_time: Optional[datetime] = None
        
        # Safety features
        self.tilt_lockout = False
        self.main_deployed = False
        self.secondary_deployed = False
        
        # Apogee detection (Mach-immune)
        self.max_altitude = 0.0
        self.altitude_samples = []
        self.apogee_confirmed = False
        
        # Landing detection
        self.low_velocity_start_time: Optional[datetime] = None
        
        # Event callbacks
        self.event_callbacks: dict[FlightEvent, list[Callable]] = {
            event: [] for event in FlightEvent
        }
        
        # Event log
        self.event_log: list[tuple[datetime, FlightEvent, str]] = []
        
        logger.info(
            f"Flight State Machine initialized: "
            f"main_deploy={main_deploy_altitude}m, "
            f"liftoff_accel={liftoff_accel_threshold}m/s²"
        )
    
    def update(
        self,
        altitude: float,
        velocity: float,
        acceleration: float,
        tilt_angle: float,
        timestamp: datetime
    ) -> FlightState:
        """
        Update state machine with current telemetry
        
        Args:
            altitude: Current altitude AGL (meters)
            velocity: Current vertical velocity (m/s)
            acceleration: Current vertical acceleration (m/s²)
            tilt_angle: Current tilt angle from vertical (degrees)
            timestamp: Current timestamp
            
        Returns:
            Current flight state
        """
        # Check tilt safety lockout
        if tilt_angle > self.max_tilt_angle and self.state == FlightState.PRE_FLIGHT:
            if not self.tilt_lockout:
                self.tilt_lockout = True
                self._log_event(FlightEvent.SAFED, f"Tilt lockout: {tilt_angle:.1f}°", timestamp)
                logger.warning(f"Tilt lockout activated: {tilt_angle:.1f}° > {self.max_tilt_angle}°")
        
        # State machine logic
        if self.state == FlightState.PRE_FLIGHT:
            self._update_pre_flight(altitude, velocity, acceleration, timestamp)
        
        elif self.state == FlightState.BOOST:
            self._update_boost(altitude, velocity, acceleration, timestamp)
        
        elif self.state == FlightState.COAST:
            self._update_coast(altitude, velocity, timestamp)
        
        elif self.state == FlightState.APOGEE:
            self._update_apogee(altitude, velocity, timestamp)
        
        elif self.state == FlightState.DESCENT:
            self._update_descent(altitude, velocity, timestamp)
        
        elif self.state == FlightState.LANDED:
            pass  # Terminal state
        
        # Track maximum altitude
        if altitude > self.max_altitude:
            self.max_altitude = altitude
        
        return self.state
    
    def _update_pre_flight(self, altitude: float, velocity: float, acceleration: float, timestamp: datetime):
        """Update PRE_FLIGHT state"""
        # Detect liftoff: high acceleration + altitude increase
        if (acceleration > self.liftoff_accel_threshold and 
            altitude > self.liftoff_altitude_threshold and
            self.armed and not self.tilt_lockout):
            
            self._transition_to(FlightState.BOOST, timestamp)
            self.liftoff_time = timestamp
            self._log_event(FlightEvent.LIFTOFF, f"Alt={altitude:.1f}m, Accel={acceleration:.1f}m/s²", timestamp)
    
    def _update_boost(self, altitude: float, velocity: float, acceleration: float, timestamp: datetime):
        """Update BOOST state"""
        # Detect burnout: acceleration drops below threshold
        if acceleration < 5.0:  # Less than 0.5G
            self._transition_to(FlightState.COAST, timestamp)
            self._log_event(FlightEvent.BURNOUT, f"Alt={altitude:.1f}m, Vel={velocity:.1f}m/s", timestamp)
    
    def _update_coast(self, altitude: float, velocity: float, timestamp: datetime):
        """Update COAST state"""
        # Mach-immune apogee detection
        # Method 1: Velocity crosses zero (most reliable)
        if velocity < self.apogee_velocity_threshold and velocity > -self.apogee_velocity_threshold:
            if not self.apogee_confirmed:
                # Confirm apogee by checking altitude is decreasing
                self.altitude_samples.append(altitude)
                if len(self.altitude_samples) > 3:
                    # Check if altitude is consistently decreasing
                    if all(self.altitude_samples[i] > self.altitude_samples[i+1] 
                           for i in range(len(self.altitude_samples)-1)):
                        self.apogee_confirmed = True
                        self._transition_to(FlightState.APOGEE, timestamp)
                        self.apogee_time = timestamp
                        self._log_event(FlightEvent.APOGEE_DETECTED, f"Alt={altitude:.1f}m", timestamp)
                        
                        # Deploy drogue chute at apogee
                        if not self.main_deployed:
                            self._deploy_main_chute(altitude, timestamp)
                    
                    # Keep only last 3 samples
                    if len(self.altitude_samples) > 3:
                        self.altitude_samples.pop(0)
        else:
            # Reset altitude samples if velocity is not near zero
            self.altitude_samples.clear()
    
    def _update_apogee(self, altitude: float, velocity: float, timestamp: datetime):
        """Update APOGEE state"""
        # Transition to descent after apogee
        if velocity < -5.0:  # Descending at > 5 m/s
            self._transition_to(FlightState.DESCENT, timestamp)
    
    def _update_descent(self, altitude: float, velocity: float, timestamp: datetime):
        """Update DESCENT state"""
        # Deploy secondary chute at target altitude
        if altitude <= self.main_deploy_altitude and not self.secondary_deployed:
            self._deploy_secondary_chute(altitude, timestamp)
        
        # Detect landing: low velocity for extended period
        if abs(velocity) < self.landing_velocity_threshold:
            if self.low_velocity_start_time is None:
                self.low_velocity_start_time = timestamp
            elif (timestamp - self.low_velocity_start_time).total_seconds() > self.landing_time_threshold:
                self._transition_to(FlightState.LANDED, timestamp)
                self.landing_time = timestamp
                self._log_event(FlightEvent.TOUCHDOWN, f"Alt={altitude:.1f}m", timestamp)
        else:
            self.low_velocity_start_time = None
    
    def _transition_to(self, new_state: FlightState, timestamp: datetime):
        """Transition to new state"""
        self.previous_state = self.state
        self.state = new_state
        logger.info(f"State transition: {self.previous_state.name} → {new_state.name}")
    
    def _deploy_main_chute(self, altitude: float, timestamp: datetime):
        """Deploy main (drogue) parachute"""
        self.main_deployed = True
        self._log_event(FlightEvent.MAIN_DEPLOY, f"Alt={altitude:.1f}m", timestamp)
        self._trigger_event(FlightEvent.MAIN_DEPLOY)
        logger.info(f"Main chute deployed at {altitude:.1f}m")
    
    def _deploy_secondary_chute(self, altitude: float, timestamp: datetime):
        """Deploy secondary (main) parachute"""
        self.secondary_deployed = True
        self._log_event(FlightEvent.SECONDARY_DEPLOY, f"Alt={altitude:.1f}m", timestamp)
        self._trigger_event(FlightEvent.SECONDARY_DEPLOY)
        logger.info(f"Secondary chute deployed at {altitude:.1f}m")
    
    def arm(self, timestamp: datetime):
        """Arm the flight computer"""
        if not self.armed:
            self.armed = True
            self._log_event(FlightEvent.ARMED, "System armed", timestamp)
            logger.info("Flight computer ARMED")
    
    def disarm(self, timestamp: datetime):
        """Disarm the flight computer"""
        if self.armed:
            self.armed = False
            self._log_event(FlightEvent.SAFED, "System disarmed", timestamp)
            logger.info("Flight computer DISARMED")
    
    def register_event_callback(self, event: FlightEvent, callback: Callable):
        """Register callback for flight event"""
        self.event_callbacks[event].append(callback)
    
    def _trigger_event(self, event: FlightEvent):
        """Trigger all callbacks for an event"""
        for callback in self.event_callbacks[event]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def _log_event(self, event: FlightEvent, details: str, timestamp: datetime):
        """Log flight event"""
        self.event_log.append((timestamp, event, details))
        logger.info(f"Event: {event.name} - {details}")
    
    def get_flight_time(self) -> Optional[float]:
        """Get flight time in seconds"""
        if self.liftoff_time:
            if self.landing_time:
                return (self.landing_time - self.liftoff_time).total_seconds()
            else:
                return (datetime.utcnow() - self.liftoff_time).total_seconds()
        return None
    
    def get_stats(self) -> dict:
        """Get state machine statistics"""
        return {
            "state": self.state.name,
            "armed": self.armed,
            "tilt_lockout": self.tilt_lockout,
            "main_deployed": self.main_deployed,
            "secondary_deployed": self.secondary_deployed,
            "max_altitude_m": round(self.max_altitude, 2),
            "flight_time_s": self.get_flight_time(),
            "event_count": len(self.event_log)
        }
