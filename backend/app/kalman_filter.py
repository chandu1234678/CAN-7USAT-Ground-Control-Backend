"""
Kalman Filter for sensor fusion (Barometer + Accelerometer)
Inspired by BPS.space and alturia-firmware implementations
Provides optimal altitude and velocity estimation
"""

import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class KalmanFilter:
    """
    1D Kalman Filter for altitude and velocity estimation
    Fuses barometric altitude with accelerometer data
    
    State vector: [altitude, velocity]
    Measurements: [barometric_altitude, acceleration]
    
    Based on implementations from:
    - BPS.space Falcon Heavy flight computer
    - rckTom/alturia-firmware
    - CATS (Control and Telemetry Systems)
    """
    
    def __init__(
        self,
        process_noise: float = 0.1,
        measurement_noise_altitude: float = 0.5,
        measurement_noise_accel: float = 1.0,
        initial_altitude: float = 0.0,
        initial_velocity: float = 0.0
    ):
        """
        Initialize Kalman Filter
        
        Args:
            process_noise: Process noise covariance (Q)
            measurement_noise_altitude: Barometer measurement noise (R)
            measurement_noise_accel: Accelerometer measurement noise (R)
            initial_altitude: Initial altitude estimate (meters)
            initial_velocity: Initial velocity estimate (m/s)
        """
        # State vector [altitude, velocity]
        self.x = np.array([[initial_altitude], [initial_velocity]])
        
        # State covariance matrix
        self.P = np.array([[1.0, 0.0],
                          [0.0, 1.0]])
        
        # Process noise covariance
        self.Q = np.array([[process_noise, 0.0],
                          [0.0, process_noise]])
        
        # Measurement noise covariance
        self.R_altitude = measurement_noise_altitude ** 2
        self.R_accel = measurement_noise_accel ** 2
        
        # Gravity constant
        self.g = 9.81  # m/s²
        
        # Statistics
        self.update_count = 0
        
        logger.info(
            f"Kalman Filter initialized: "
            f"Q={process_noise}, R_alt={measurement_noise_altitude}, "
            f"R_accel={measurement_noise_accel}"
        )
    
    def predict(self, dt: float, acceleration: float):
        """
        Prediction step: Update state based on acceleration
        
        Args:
            dt: Time step (seconds)
            acceleration: Measured acceleration (m/s²)
        """
        # Remove gravity from acceleration
        accel_vertical = acceleration - self.g
        
        # State transition matrix (constant acceleration model)
        # x_k+1 = F * x_k + B * u_k
        # altitude_k+1 = altitude_k + velocity_k * dt + 0.5 * accel * dt²
        # velocity_k+1 = velocity_k + accel * dt
        F = np.array([[1.0, dt],
                     [0.0, 1.0]])
        
        B = np.array([[0.5 * dt * dt],
                     [dt]])
        
        # Predict state
        self.x = F @ self.x + B * accel_vertical
        
        # Predict covariance
        self.P = F @ self.P @ F.T + self.Q
    
    def update_altitude(self, measured_altitude: float):
        """
        Update step: Correct state with barometric altitude measurement
        
        Args:
            measured_altitude: Barometric altitude (meters)
        """
        # Measurement matrix (we measure altitude directly)
        H = np.array([[1.0, 0.0]])
        
        # Innovation (measurement residual)
        y = measured_altitude - (H @ self.x)[0, 0]
        
        # Innovation covariance
        S = (H @ self.P @ H.T)[0, 0] + self.R_altitude
        
        # Kalman gain
        K = (self.P @ H.T) / S
        
        # Update state
        self.x = self.x + K * y
        
        # Update covariance
        I = np.eye(2)
        self.P = (I - K @ H) @ self.P
        
        self.update_count += 1
    
    def update_acceleration(self, measured_accel: float, dt: float):
        """
        Update step: Correct state with accelerometer measurement
        
        Args:
            measured_accel: Measured acceleration (m/s²)
            dt: Time step (seconds)
        """
        # Measurement matrix (we measure velocity change)
        # velocity_change = accel * dt
        H = np.array([[0.0, 1.0]])
        
        # Remove gravity
        accel_vertical = measured_accel - self.g
        
        # Expected velocity change
        expected_velocity_change = accel_vertical * dt
        
        # Innovation
        y = expected_velocity_change - (H @ self.x)[0, 0] * dt
        
        # Innovation covariance
        S = (H @ self.P @ H.T)[0, 0] * dt * dt + self.R_accel
        
        # Kalman gain
        K = (self.P @ H.T) / S
        
        # Update state
        self.x = self.x + K * y
        
        # Update covariance
        I = np.eye(2)
        self.P = (I - K @ H) @ self.P
    
    def get_state(self) -> Tuple[float, float]:
        """
        Get current state estimate
        
        Returns:
            (altitude, velocity) in meters and m/s
        """
        return float(self.x[0, 0]), float(self.x[1, 0])
    
    def get_altitude(self) -> float:
        """Get estimated altitude"""
        return float(self.x[0, 0])
    
    def get_velocity(self) -> float:
        """Get estimated velocity"""
        return float(self.x[1, 0])
    
    def get_covariance(self) -> np.ndarray:
        """Get state covariance matrix"""
        return self.P.copy()
    
    def reset(self, altitude: float = 0.0, velocity: float = 0.0):
        """
        Reset filter to initial state
        
        Args:
            altitude: Initial altitude (meters)
            velocity: Initial velocity (m/s)
        """
        self.x = np.array([[altitude], [velocity]])
        self.P = np.array([[1.0, 0.0],
                          [0.0, 1.0]])
        self.update_count = 0
        logger.info(f"Kalman Filter reset: alt={altitude}m, vel={velocity}m/s")
    
    def get_stats(self) -> dict:
        """Get filter statistics"""
        altitude, velocity = self.get_state()
        return {
            "altitude_m": round(altitude, 2),
            "velocity_ms": round(velocity, 2),
            "altitude_variance": round(self.P[0, 0], 4),
            "velocity_variance": round(self.P[1, 1], 4),
            "update_count": self.update_count
        }
