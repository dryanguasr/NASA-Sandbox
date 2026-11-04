"""Unit checks plus an integration run on the actual imported Jezero crop."""
from pathlib import Path
import copy
import json
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).parent))
from mission import Agent, Belief, Grid, SimulatedWorld, Task, assign, astar, compatible, load_data, run

ROOT=Path(__file__).resolve().parents[2]


def agent(kind='rover', name='rover_1'):
    return Agent(name,kind,np.array([-1.,-1.]),np.array([-1.,-1.]),1.,4.,.5,20.,10.)


def test_coordinates_roundtrip_and_bounds():
    g=Grid(8,2)
    for rc in [(0,0),(7,7),(2,5)]:
        assert g.rc(g.xy(rc))==rc
    with pytest.raises(ValueError):g.rc((g.half,0))


def test_sensor_does_not_expose_hidden_reference_or_sites():
    g=Grid(16,2);z=np.arange(256).reshape(16,16)
    w=SimulatedWorld(z,np.ones_like(z,bool),g,[{'id':'hidden','xy_m':[12,12]}],7)
    mask,y,sites=w.observe([-12,-12],3,.5)
    assert np.isnan(y[~mask]).all()
    assert np.isfinite(y[mask]).all()
    assert sites=={}


def test_repeat_observations_do_not_create_false_information():
    g=Grid(8,2);b=Belief(np.zeros((8,8)),np.ones((8,8),bool),g,3)
    m=g.disk((0,0),5);values=np.ones((8,8))
    assert b.update(m,values,.5,1)>0
    var=b.var.copy();mean=b.mean.copy()
    assert b.update(m,values,.5,1)==0
    np.testing.assert_array_equal(var,b.var);np.testing.assert_array_equal(mean,b.mean)
    b.update(m,values*.8,.25,3)
    assert (b.var[m]==.25**2).all()


def test_fusion_ignores_everything_outside_observation_mask():
    g=Grid(8,2);b=Belief(np.zeros((8,8)),np.ones((8,8),bool),g,3)
    m=g.disk((0,0),3);values=np.full((8,8),np.nan);values[m]=2
    b.update(m,values,.5,1)
    assert (b.mean[~m]==0).all() and not b.observed[~m].any()


def test_astar_does_not_cross_unknown_barrier_or_cut_corners():
    g=Grid(8,1);z=np.zeros((8,8));allowed=np.ones((8,8),bool)
    allowed[:,4]=False
    assert astar(g,z,allowed,g.xy((4,1)),g.xy((4,6))) is None
    allowed=np.zeros((8,8),bool);allowed[2,2]=True;allowed[3,3]=True
    assert astar(g,z,allowed,g.xy((2,2)),g.xy((3,3))) is None


def test_astar_valid_path_stays_in_allowed_cells():
    g=Grid(8,1);z=np.zeros((8,8));allowed=np.ones((8,8),bool)
    allowed[3:6,3]=False
    path,d=astar(g,z,allowed,g.xy((2,2)),g.xy((6,6)))
    assert all(allowed[g.rc(x)] for x in path) and d>0


def test_known_orbital_map_is_not_certified_local_terrain():
    g=Grid(8,1);b=Belief(np.zeros((8,8)),np.ones((8,8),bool),g,3)
    assert not b.traversable(20,1).any()
    b.update(np.ones((8,8),bool),np.zeros((8,8)),.5,1)
    assert b.traversable(20,1)[3,3]


def test_type_and_return_compatibility():
    a=agent()
    assert compatible(a,Task('inspect:X','inspect',[0,0],0))
    assert not compatible(a,Task('sample:X','sample',[0,0],0))
    assert compatible(a,Task('return:rover_1','return',[0,0],0))
    assert not compatible(a,Task('return:rover_2','return',[0,0],0))


def test_assignment_has_no_duplicates_and_respects_types():
    g=Grid(16,2);b=Belief(np.zeros((16,16)),np.ones((16,16),bool),g,3)
    b.update(np.ones((16,16),bool),np.zeros((16,16)),.5,1)
    robots=[agent(),agent('human','human_1')]
    tasks={t.id:t for t in [Task('i','inspect',[3,3],0),Task('s','sample',[3,3],0)]}
    pairs=assign(robots,tasks,b,{'ground_sigma_gate_m':1,'information_bonus_s':90},'information_hungarian')
    assert len(pairs)==2
    assert len({t.id for _,t,_,_ in pairs})==2
    assert all(compatible(a,t) for a,t,_,_ in pairs)


def test_planning_public_belief_has_no_truth_attribute():
    b=Belief(np.zeros((8,8)),np.ones((8,8),bool),Grid(8,1),3)
    assert not hasattr(b,'reference') and not hasattr(b,'_height')


@pytest.fixture(scope='module')
def actual():
    folder=ROOT/'data/jezero'
    if not (folder/'terrain.npz').exists():
        pytest.skip('Run import_data.py first; real-data integration is not replaced by synthetic data')
    config=json.loads((Path(__file__).parent/'scenario.json').read_text())
    result=run(*load_data(folder),config)
    return result,config


def test_actual_import_provenance(actual):
    _,_,_,m=load_data(ROOT/'data/jezero')
    assert m['sources']['reference']['instrument']=='MRO/HiRISE'
    assert m['sources']['prior']['instrument']=='MRO/CTX'
    assert m['mars_sphere_radius_m']==3396190


def test_actual_mission_completes_and_map_improves(actual):
    r,_=actual;s=r['summary']
    assert s['success'] and s['samples_completed']==4 and s['inspections_completed']==4
    assert s['observed_fraction']>.995
    assert s['final_rmse_m']<s['initial_rmse_m']
    assert s['ground_steps_in_unobserved_cells']==0
    assert all(a['returned'] and len(a['tasks_completed'])>=2 for a in s['agents'].values())


def test_samples_are_not_created_before_rover_inspection(actual):
    r,_=actual
    for t in r['tasks'].values():
        if t.kind=='sample':
            assert t.created_s>=r['tasks'][t.dependency].completed_s
    completed={e['task']:e['time_s'] for e in r['events'] if e['event']=='completed'}
    for e in r['events']:
        if e['event']=='assigned' and e['kind']=='sample':
            assert e['time_s']>=completed['inspect:'+r['tasks'][e['task']].site]


def test_no_kinematic_speed_violations(actual):
    r,c=actual;speed={a['id']:a['speed_m_s'] for a in c['agents']}
    for before,after in zip(r['trajectory'],r['trajectory'][1:]):
        dt=after['time_s']-before['time_s']
        for aid in speed:
            distance=np.linalg.norm(np.asarray(after['positions'][aid][:2])-before['positions'][aid][:2])
            assert distance<=dt*speed[aid]+1e-6


def test_uncertainty_never_increases_in_this_static_perfect_comms_model(actual):
    r,_=actual
    for a,b in zip(r['frames'],r['frames'][1:]):
        assert np.all(b[2]<=a[2]+1e-12)
        assert np.all(b[3]>=a[3])


def test_both_policies_use_identical_sensor_field():
    g=Grid(16,2);z=np.zeros((16,16));v=np.ones_like(z,bool)
    a=SimulatedWorld(z,v,g,[],11);b=SimulatedWorld(z,v,g,[],11)
    np.testing.assert_array_equal(a.observe((0,0),10,.5)[1],b.observe((0,0),10,.5)[1])
