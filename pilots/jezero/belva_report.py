"""Audit and package the Belva Gazebo run."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET

import numpy as np

from extension_report import rows
from live_world import ROOT
from mission import Grid, load_data, slopes
from select_belva import line_cells, passable


def return_tracking(path, trace):
    """Distances from sampled Gazebo poses to the assigned horizontal polyline."""
    start = np.asarray(path[:-1])
    segments = np.diff(path,axis=0)
    offset = np.asarray(trace)[:,None,:]-start
    progress = (offset*segments).sum(axis=2)/np.square(segments).sum(axis=1)
    return np.linalg.norm(offset-np.clip(progress,0,1)[:,:,None]*segments,axis=2).min(axis=1)


def audit(run):
    result = json.loads((run/'result.json').read_text())
    events = rows(run/'events.jsonl')
    states = rows(run/'states.jsonl')
    dem, _, valid, meta = load_data(ROOT/'data/jezero_live/belva')
    assert valid.all() and result['terrain_sha256']==meta['terrain_sha256']
    grid = Grid(32,4)
    mesh = run/'models/jezero_terrain/meshes/terrain.obj'
    vertices = np.array([list(map(float,line.split()[1:])) for line in mesh.read_text().splitlines()
                         if line.startswith('v ')])
    expected = np.array([(*grid.xy(rc),dem[rc]-meta['origin_z_m']) for rc in np.ndindex(dem.shape)])
    error = float(np.max(np.abs(vertices-expected)))
    assert error<1e-6
    world = ET.parse(run/'live.sdf').getroot().find('world')
    markers = {model.get('name'):model for model in world.findall('model')
               if model.get('name','').startswith('fictional_')}
    assert set(markers)=={'fictional_site_S1','fictional_site_S2'}
    assert all(model.find('.//collision') is None for model in markers.values())
    assert not any(model.get('name','').startswith('experimental_') for model in world.findall('model'))
    assert result['status']=='complete', result
    assert sum(e['event']=='individual_control' and e['passed'] for e in events)==6
    assert events[-1]['event']=='zero_velocity_sent' and len(events[-1]['agents'])==6
    assert result['returns']==6 and max(result['final_home_error_m'].values())<=2

    def event(kind, key, value):
        return next(e for e in events if e['event']==kind and e.get(key)==value)

    discoveries = {site:event('site_detected','site',site) for site in ('S1','S2')}
    assert all(e['t_s']>0 and e['observer'].startswith('drone_') for e in discoveries.values())
    routes = {}
    for task, limit in [('inspect:S1',18),('sample:S1',22)]:
        assigned = event('assigned','task',task)
        start = next(s for s in reversed(states) if s['t_s']<=assigned['t_s'])['poses'][assigned['agent']][:2]
        path = [start,*assigned['path']]
        direct = math.dist(start,path[-1])
        length = sum(math.dist(a,b) for a,b in zip(path,path[1:]))
        safe = passable(dem,limit)
        blocked = sum(not safe[cell] for cell in line_cells(grid,start,path[-1]))
        assert length>direct and blocked>0, (task,direct,length,blocked)
        completed = event('task_completed','task',task)
        trace = [start,*(s['poses'][assigned['agent']][:2] for s in states
                         if assigned['t_s']<s['t_s']<completed['t_s']),completed['observed_xy_m']]
        travelled = sum(math.dist(a,b) for a,b in zip(trace,trace[1:]))
        routes[task] = dict(agent=assigned['agent'], direct_m=direct, planned_m=length,
                            observed_m=travelled, blocked_direct_cells=blocked, assigned_s=assigned['t_s'],
                            completed_s=completed['t_s'])
    enabled = event('sample_enabled','task','sample:S1')
    assert discoveries['S1']['t_s']<=routes['inspect:S1']['assigned_s']
    assert routes['inspect:S1']['completed_s']<=enabled['t_s']<=routes['sample:S1']['assigned_s']
    inaccessible = event('ground_inaccessible','task','inspect:S2')
    assert discoveries['S2']['t_s']<=inaccessible['t_s']
    assert not any(e.get('task')=='sample:S2' for e in events)
    returns = {}
    for agent in result['final_home_error_m']:
        assigned = event('assigned','task','return:'+agent)
        completed = event('task_completed','task','return:'+agent)
        home_error = math.dist(completed['observed_xy_m'],assigned['path'][-1])
        assert home_error<=2
        returns[agent] = dict(assigned_s=assigned['t_s'],completed_s=completed['t_s'],
                              completion_home_error_m=home_error)
    agent = routes['inspect:S1']['agent']
    assigned = event('assigned','task','return:'+agent)
    samples = [s for s in states if assigned['t_s']<=s['t_s']<=returns[agent]['completed_s']]
    track = return_tracking(assigned['path'],[s['poses'][agent][:2] for s in samples])
    reverse = sum(s['rover_control'][agent]['direction']==-1 for s in samples)
    inspection = routes['inspect:S1']
    approach_reverse = sum(s['rover_control'][agent]['direction']==-1 for s in states
                           if inspection['assigned_s']<=s['t_s']<=inspection['completed_s'])
    departure = next(s for s in reversed(states) if s['t_s']<=assigned['t_s'])
    after_ten = min(samples,key=lambda s:abs(s['t_s']-assigned['t_s']-10.))
    east_progress = after_ten['poses'][agent][0]-departure['poses'][agent][0]
    assert approach_reverse+reverse>0 and east_progress>2 and max(track)<=2, (
        agent,approach_reverse,reverse,east_progress,max(track))
    result.update(discoveries=discoveries, route_comparison=routes, verified_returns=returns,
                  inspection_rover_return=dict(agent=agent,reverse_samples=reverse,
                                               approach_reverse_samples=approach_reverse,
                                               initial_heading_deg=math.degrees(departure['poses'][agent][3]),
                                               east_progress_approx_10_s_m=east_progress,
                                               cross_track_max_m=float(max(track))),
                  inaccessible_s=inaccessible['t_s'], mesh_max_error_m=error,
                  elevation_range_m=[float(dem.min()),float(dem.max())],
                  maximum_slope_deg=float(slopes(dem,4).max()))
    return result


def package(run, out):
    result = audit(run)
    out.mkdir(parents=True,exist_ok=True)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copyfile(run/'live.mp4',out/'belva.mp4')
    subprocess.run(['ffmpeg','-v','error','-y','-filter_complex_threads','1',
                    '-i',str(out/'belva.mp4'),'-filter_complex',
                    'fps=7,scale=720:-2:flags=lanczos,split[a][b];'
                    '[a]palettegen[p];[b][p]paletteuse=dither=bayer',
                    '-loop','0',str(out/'belva.gif')],check=True)
    with tarfile.open(out/'telemetry.tar.gz','w:gz') as archive:
        for name in ('result.json','events.jsonl','states.jsonl','gazebo.log','live.sdf','spawn.jsonl',
                     'provenance.json','models/jezero_terrain/meshes/terrain.obj'):
            archive.add(run/name,arcname=name)
    for name in ('belva.mp4','belva.gif'):
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out/name),'-f','null','-'],check=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('out',type=Path)
    args = parser.parse_args()
    package(args.run,args.out)
