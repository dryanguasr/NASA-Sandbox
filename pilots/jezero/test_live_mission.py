"""Regression tests for data boundaries and live mission protocol."""
import inspect

import numpy as np

from live_mission import Channel, Grid, Lease, Mission, Observation, Task, project


def test_nadir_depth_and_masks():
    grid = Grid(16,4.)
    depth = np.full((40,40),20.)
    rgb = np.full((40,40,3),(170,130,105),np.uint8)
    rgb[18:22,18:22] = (255,0,0)
    rgb[10:14,28:32] = (0,255,0)
    depth[0:7] = np.inf
    frame = project(depth,rgb,(0,0),25,grid,1.45,8,np.zeros((16,16)))
    assert frame.stamp==8
    assert 0<frame.mask.sum()<16**2
    assert np.all(frame.heights[frame.mask]==5)
    assert np.isnan(frame.heights[~frame.mask]).all()
    assert frame.occupied.any()
    assert frame.sites['S1'][0]>0 and frame.sites['S1'][1]<0


def test_planner_has_no_reference_input_and_sample_requires_inspection():
    assert 'reference' not in inspect.signature(Mission).parameters
    homes = {'drone_1':(-50,-46),'rover_1':(-50,-42),'human_1':(-50,-50)}
    m = Mission(np.zeros((32,32)),homes,2,'information_hungarian','ideal',7,lambda *a,**k: None)
    mask = np.zeros((32,32),bool)
    m.observation(Observation(1,mask,np.full(mask.shape,np.nan),mask,{'S1':[-26,-14]}),1)
    assert 'inspect:S1' in m.tasks and 'sample:S1' not in m.tasks
    m.leases['rover_1'] = Lease(5,'inspect:S1',[],40)
    m.finish('rover_1','inspect:S1',4,8)
    assert 'sample:S1' not in m.tasks
    m.finish('rover_1','inspect:S1',5,8)
    assert m.tasks['sample:S1'].dependency=='inspect:S1'


def test_channel_delay_and_bidirectional_cut():
    c = Channel('delay',7,lambda *a,**k: None)
    c.send('a','b',('status',),4)
    assert not list(c.receive(5.99))
    assert list(c.receive(6))==[('a','b',('status',))]
    c.cut = ('b',7,67)
    c.send('a','b',('lease',),7)
    c.send('b','a',('status',),8)
    assert not list(c.receive(67))
    c.send('b','a',('status',),67)
    assert list(c.receive(69))==[('b','a',('status',))]


def test_expired_lease_reopens_task_and_rejects_stale_completion():
    homes = {'rover_1':(-50,-42),'rover_2':(-42,-42)}
    events = []
    m = Mission(np.zeros((32,32)),homes,2,'information_hungarian','cut',7,
                lambda kind,**data: events.append((kind,data)))
    task = Task('inspect:S1','inspect',[-26,-14],0,site='S1',state='assigned')
    m.tasks[task.id] = task
    m.agents['rover_1'].task = task.id
    m.leases['rover_1'] = Lease(3,task.id,[],14)
    m.channel.cut = ('rover_1',1,61)
    m.tick(15)
    assert task.state=='open' and 'rover_1' not in m.leases
    m.leases['rover_2'] = Lease(4,task.id,[],40)
    m.finish('rover_1',task.id,3,16)
    assert 'sample:S1' not in m.tasks
    assert any(kind=='confirmation_rejected' for kind,_ in events)


def test_observed_barrier_can_make_route_unavailable():
    m = Mission(np.zeros((32,32)),{'rover_1':(-50,-2)},1,
                'information_hungarian','ideal',7,lambda *a,**k: None)
    assert m.route((-50,-2),(46,-2)) is not None
    m.blocked[:,12] = True
    assert m.route((-50,-2),(46,-2)) is None
