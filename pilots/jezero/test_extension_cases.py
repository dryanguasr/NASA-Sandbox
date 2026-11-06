"""Regression checks for the nonconvex mask and local discoveries."""
import numpy as np

from live_mission import ExtensionMission, Grid, project
from mission import astar


def test_disconnected_scarp_can_be_classified_without_hidden_terrain():
    m = ExtensionMission(np.zeros((32,32)),{'rover_1':(-50,-42),'human_1':(-50,-50)},
                         5,'information_hungarian','ideal',7,lambda *a,**k: None)
    m.reveal('S1',[30,-22],1,'drone_1',1)
    for task in m.tasks.values():
        if task.kind=='survey':
            task.state = 'done'
    m.blocked[8:,16] = True
    assert astar(m.grid,m.belief.mean,m.belief.safe(18),(-50,-42),(30,-22)) is not None
    assert not m.ready_to_return()
    m.blocked[:,16] = True
    assert m.ready_to_return()
    assert m.tasks['inspect:S1'].state=='inaccessible'


def test_ground_detection_is_local_rotated_and_filters_sparse_color():
    grid = Grid(32,4.)
    depth = np.full((80,80),4.)
    rgb = np.full((80,80,3),110,np.uint8)
    rgb[38:42,38:42] = (0,255,255)
    rgb[35,40] = (0,255,0)
    packet = project(depth,rgb,(0,0),1.4,grid,1.32,5,np.zeros((32,32)),ground_yaw=np.pi/2)
    assert packet.sites=={'S4':[2.0,2.0]}
    assert not packet.mask.any()
    assert packet.confidence['S4']==1
    depth[:] = 11.
    assert not project(depth,rgb,(0,0),1.4,grid,1.32,6,np.zeros((32,32)),ground_yaw=0).sites


def test_science_tasks_start_empty_for_discovery():
    m = ExtensionMission(np.zeros((32,32)),{'rover_1':(-50,-42)},
                         6,'information_hungarian','ideal',7,lambda *a,**k: None)
    assert all(t.kind in ('survey','ground_survey') for t in m.tasks.values())
    m.reveal('S4',[-26,-42],8,'rover_1',8)
    m.reveal('S4',[-22,-42],9,'drone_1',9)
    assert m.tasks['inspect:S4'].xy==[-26,-42]
    assert 'sample:S4' not in m.tasks
    assert 'inspect:S4' not in m.assignable_tasks()
    m.tasks['ground_survey:rover_1'].state = 'done'
    assert 'inspect:S4' in m.assignable_tasks()
