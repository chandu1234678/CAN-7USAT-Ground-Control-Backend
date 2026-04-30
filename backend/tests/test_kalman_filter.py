"""Unit tests for Kalman filter."""

import pytest

from app.kalman_filter import KalmanFilter


def test_initial_state_and_stats():
    kf = KalmanFilter(initial_altitude=10.0, initial_velocity=2.5)

    altitude, velocity = kf.get_state()
    stats = kf.get_stats()

    assert altitude == 10.0
    assert velocity == 2.5
    assert stats["update_count"] == 0
    assert stats["altitude_m"] == 10.0
    assert stats["velocity_ms"] == 2.5


def test_predict_gravity_compensated_motion():
    kf = KalmanFilter(initial_altitude=0.0, initial_velocity=0.0)

    # Acceleration equals gravity, so net vertical acceleration should be ~0.
    kf.predict(dt=1.0, acceleration=9.81)

    altitude, velocity = kf.get_state()
    assert abs(altitude) < 1e-9
    assert abs(velocity) < 1e-9


def test_predict_with_upward_acceleration():
    kf = KalmanFilter(initial_altitude=0.0, initial_velocity=0.0)

    # Net acceleration = 10 m/s^2 after gravity compensation.
    kf.predict(dt=1.0, acceleration=19.81)

    altitude, velocity = kf.get_state()
    assert altitude == pytest.approx(5.0, rel=1e-9, abs=1e-9)
    assert velocity == pytest.approx(10.0, rel=1e-9, abs=1e-9)


def test_update_altitude_changes_estimate_and_count():
    kf = KalmanFilter(initial_altitude=0.0, initial_velocity=0.0)

    before_alt = kf.get_altitude()
    kf.update_altitude(measured_altitude=100.0)
    after_alt = kf.get_altitude()

    assert after_alt > before_alt
    assert after_alt < 100.0
    assert kf.get_stats()["update_count"] == 1


def test_covariance_is_copied_and_reset_restores_state():
    kf = KalmanFilter(initial_altitude=12.0, initial_velocity=-1.0)

    cov = kf.get_covariance()
    cov[0, 0] = 999.0

    internal_cov = kf.get_covariance()
    assert internal_cov[0, 0] != 999.0

    kf.update_altitude(20.0)
    kf.reset(altitude=3.0, velocity=4.0)

    altitude, velocity = kf.get_state()
    assert altitude == 3.0
    assert velocity == 4.0
    assert kf.get_stats()["update_count"] == 0
