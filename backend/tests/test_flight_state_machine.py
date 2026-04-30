"""Unit tests for flight state machine transitions and safety gates."""

from datetime import datetime, timedelta

from app.flight_state_machine import FlightEvent, FlightState, FlightStateMachine


def test_does_not_liftoff_when_not_armed():
    fsm = FlightStateMachine()
    now = datetime.utcnow()

    state = fsm.update(
        altitude=20.0,
        velocity=10.0,
        acceleration=30.0,
        tilt_angle=0.0,
        timestamp=now,
    )

    assert state == FlightState.PRE_FLIGHT
    assert not fsm.armed


def test_tilt_lockout_blocks_liftoff():
    fsm = FlightStateMachine(max_tilt_angle=30.0)
    now = datetime.utcnow()
    fsm.arm(now)

    # First update activates lockout.
    fsm.update(
        altitude=0.0,
        velocity=0.0,
        acceleration=0.0,
        tilt_angle=40.0,
        timestamp=now,
    )

    state = fsm.update(
        altitude=20.0,
        velocity=10.0,
        acceleration=30.0,
        tilt_angle=0.0,
        timestamp=now + timedelta(milliseconds=100),
    )

    assert fsm.tilt_lockout
    assert state == FlightState.PRE_FLIGHT


def test_nominal_flight_transitions_to_landed_and_deploys():
    fsm = FlightStateMachine(main_deploy_altitude=120.0)
    start = datetime.utcnow()
    fsm.arm(start)

    # Liftoff
    state = fsm.update(
        altitude=10.0,
        velocity=30.0,
        acceleration=25.0,
        tilt_angle=0.0,
        timestamp=start + timedelta(seconds=1),
    )
    assert state == FlightState.BOOST

    # Burnout -> coast
    state = fsm.update(
        altitude=80.0,
        velocity=70.0,
        acceleration=2.0,
        tilt_angle=2.0,
        timestamp=start + timedelta(seconds=2),
    )
    assert state == FlightState.COAST

    # Near-zero velocity and decreasing altitude samples to confirm apogee.
    for i, alt in enumerate([160.0, 159.5, 159.0, 158.5], start=3):
        state = fsm.update(
            altitude=alt,
            velocity=0.0,
            acceleration=0.0,
            tilt_angle=3.0,
            timestamp=start + timedelta(seconds=i),
        )

    assert state == FlightState.APOGEE
    assert fsm.main_deployed

    # Descent transition
    state = fsm.update(
        altitude=150.0,
        velocity=-8.0,
        acceleration=0.0,
        tilt_angle=5.0,
        timestamp=start + timedelta(seconds=8),
    )
    assert state == FlightState.DESCENT

    # Secondary deployment and landing confirmation.
    fsm.update(
        altitude=110.0,
        velocity=-1.0,
        acceleration=0.0,
        tilt_angle=5.0,
        timestamp=start + timedelta(seconds=9),
    )
    landed_state = fsm.update(
        altitude=0.0,
        velocity=0.5,
        acceleration=0.0,
        tilt_angle=5.0,
        timestamp=start + timedelta(seconds=13),
    )

    assert fsm.secondary_deployed
    assert landed_state == FlightState.LANDED

    events = [event for _, event, _ in fsm.event_log]
    assert FlightEvent.LIFTOFF in events
    assert FlightEvent.APOGEE_DETECTED in events
    assert FlightEvent.TOUCHDOWN in events
