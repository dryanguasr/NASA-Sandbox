"""Tests for the live Gazebo navigation adapter (system Python with bindings)."""
import math
from collections import deque
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from live_trial import Worker, human_motion, publish_control


@pytest.mark.parametrize('dx,dy,yaw,forward,turn', [
    (0,1,0,0,1.8),
    (0,1,math.pi/2,1,0),
    (-1,0,-math.pi+.04,1,-.12),
])
def test_human_faces_waypoint_before_advancing(dx,dy,yaw,forward,turn):
    assert human_motion(dx,dy,yaw,1)==pytest.approx((forward,turn))


def test_pose_watchdog_uses_absolute_gazebo_time():
    io = SimpleNamespace(now=10.,navigation=lambda name:(7.5,(0.,0.,0.,0.)),command=Mock())
    worker = Worker(task='survey:1',expires=20,waypoints=deque([(0.,5.,0.)]))
    mission = SimpleNamespace(emit=Mock())
    publish_control(io,'drone_1',worker,mission,23.,.1)
    io.command.assert_called_once_with('drone_1')
    mission.emit.assert_called_once_with('navigation_stale_stop',agent='drone_1')


def test_drone_initial_northbound_survey_requests_nonzero_velocity():
    io = SimpleNamespace(now=10.,navigation=lambda name:(10.,(-50.,-46.,23.,0.)),command=Mock())
    worker = Worker(task='survey:-46:18',expires=20,waypoints=deque([(-46.,18.,23.)]))
    mission = SimpleNamespace(agents={'drone_1':SimpleNamespace(kind='drone',speed=4.)})
    publish_control(io,'drone_1',worker,mission,23.,.1)
    _, velocity = io.command.call_args
    assert velocity['y']>3.9 and 0<velocity['x']<.3


def test_velocity_publish_without_subscriber_is_reported():
    from live_trial import LiveIO

    io = LiveIO.__new__(LiveIO)
    io.pubs = {'drone_1':Mock()}
    io.horizontal_commands = {}
    io.pubs['drone_1'].has_connections.return_value = False
    io.pubs['drone_1'].publish.return_value = True
    with pytest.raises(RuntimeError,match='velocity transport unavailable'):
        io.command('drone_1',x=1.)
