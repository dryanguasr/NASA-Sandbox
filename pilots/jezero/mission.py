"""Belief-space mission pilot, independent of Gazebo rendering.

Truth access is confined to SimulatedWorld and evaluation. Allocation and paths
receive only Belief and discovered tasks. Ideal global instantaneous fusion.
Not a reimplementation or convergence proof of Heterogeneous DisCoverage.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import argparse
import csv
import hashlib
import heapq
import json
import math
import platform
import time

import numpy as np
from scipy.ndimage import median_filter, binary_erosion
from scipy.optimize import linear_sum_assignment


@dataclass(frozen=True)
class Grid:
    n: int
    cell: float

    @property
    def half(self):
        return self.n * self.cell / 2

    def rc(self, xy):
        x, y = xy
        r, c = int(math.floor((self.half-y)/self.cell)), int(math.floor((x+self.half)/self.cell))
        if not (0 <= r < self.n and 0 <= c < self.n):
            raise ValueError(f"Point outside raster: {xy}")
        return r, c

    def xy(self, rc):
        r, c = rc
        return np.array([-self.half+(c+.5)*self.cell, self.half-(r+.5)*self.cell])

    def height(self, z, xy):
        """Bilinear height between raster cell centres, no extrapolation beyond edges."""
        c = float(np.clip((xy[0]+self.half)/self.cell-.5, 0, self.n-1))
        r = float(np.clip((self.half-xy[1])/self.cell-.5, 0, self.n-1))
        r0,c0=int(r),int(c); r1,c1=min(r0+1,self.n-1),min(c0+1,self.n-1)
        fr,fc=r-r0,c-c0
        return float((1-fr)*((1-fc)*z[r0,c0]+fc*z[r0,c1])+fr*((1-fc)*z[r1,c0]+fc*z[r1,c1]))

    def disk(self, xy, radius):
        yy, xx = np.mgrid[:self.n, :self.n]
        x = -self.half+(xx+.5)*self.cell
        y = self.half-(yy+.5)*self.cell
        return (x-xy[0])**2+(y-xy[1])**2 <= radius**2


def slopes(height, cell):
    dy, dx = np.gradient(height, cell)
    return np.degrees(np.arctan(np.hypot(dx, dy)))


class Belief:
    """Public planner state. Conditional variances are assumed sensor-model values."""
    def __init__(self, prior, valid, grid, sigma):
        self.mean = np.array(prior, dtype=float, copy=True)
        self.var = np.full(prior.shape, sigma**2, dtype=float)
        self.valid = np.array(valid, dtype=bool, copy=True)
        self.observed = np.zeros(prior.shape, dtype=bool)
        self.source = np.zeros(prior.shape, dtype=np.uint8)  # 0=CTX; 1=drone; 2=rover; 3=human; 4=base
        self.grid = grid
        self.version = 0

    def update(self, mask, values, sigma, source):
        # A cell is assimilated only when a strictly better sensor tier arrives.
        # Repeated frames from one tier are correlated; never count them as fresh evidence.
        use = mask & self.valid & (self.var > sigma**2 * 1.01)
        if not np.any(use):
            return 0
        old = self.var[use]
        if not np.all(np.isfinite(values[use])):
            raise ValueError("Sensor mask contains invalid measurements")
        # Replace a lower-quality observation instead of falsely fusing correlated tiers.
        gain = np.where(self.observed[use], 1.0, old/(old+sigma**2))
        self.mean[use] += gain*(values[use]-self.mean[use])
        # Floor prevents collapse through repeated looks; this is conservative relative to KF.
        self.var[use] = sigma**2
        self.observed[use] = True
        self.source[use] = source
        self.version += 1
        return int(use.sum())

    def traversable(self, slope_limit, sigma_gate):
        # Median filter reduces independent synthetic pixel noise before differentiation.
        slope = slopes(median_filter(self.mean, size=3, mode="nearest"), self.grid.cell)
        neighbourhood = binary_erosion(self.observed & self.valid, structure=np.ones((5,5)), border_value=0)
        return neighbourhood & (self.var <= sigma_gate**2) & (slope <= slope_limit)

    def information_gain(self, xy, radius, sigma):
        m = self.grid.disk(xy, radius) & self.valid
        if not m.any():
            return 0.0
        # Expected conditional Gaussian entropy reduction, nats per footprint cell.
        return float(np.maximum(0, .5*np.log(self.var[m]/sigma**2)).mean())


class SimulatedWorld:
    """Private reference DEM and injected targets; used by sensor/evaluator only."""
    def __init__(self, reference, valid, grid, sites, seed):
        self._height = np.array(reference, dtype=float, copy=True)
        self._valid = valid
        self.grid = grid
        self._sites = {s['id']: grid.xy(grid.rc(s['xy_m'])) for s in sites}
        # Fixed field makes policies see the same synthetic measurement at each cell.
        self._noise = np.random.default_rng(seed).normal(size=reference.shape)

    def observe(self, xy, radius, sigma):
        mask = self.grid.disk(xy, radius) & self._valid
        values = np.full(self._height.shape, np.nan)
        values[mask] = self._height[mask] + sigma*self._noise[mask]
        detections = {sid: pos.copy() for sid,pos in self._sites.items() if mask[self.grid.rc(pos)]}
        return mask, values, detections

    def evaluate(self, belief):
        d = (belief.mean-self._height)[self._valid]
        return float(np.sqrt(np.mean(d*d)))

    def elevation(self, xy):
        return self.grid.height(self._height,xy)


@dataclass
class Task:
    id: str
    kind: str
    xy: list[float]
    created_s: float
    site: str | None = None
    state: str = "open"
    assigned_to: str | None = None
    completed_s: float | None = None
    dependency: str | None = None


@dataclass
class Agent:
    id: str
    kind: str
    xy: np.ndarray
    home: np.ndarray
    speed: float
    radius: float
    sigma: float
    slope_limit: float
    service: float
    task: str | None = None
    path: list = field(default_factory=list)
    dwell: float = 0
    distance: float = 0
    done: list = field(default_factory=list)
    returned: bool = False
    heading: float = 0.


def astar(grid, mean, allowed, start_xy, goal_xy):
    """8-connected metric path with no diagonal corner cutting. No truth argument."""
    start, goal = grid.rc(start_xy), grid.rc(goal_xy)
    if not allowed[start] or not allowed[goal]:
        return None
    heuristic = lambda rc: math.hypot(rc[0]-goal[0], rc[1]-goal[1])*grid.cell
    queue = [(heuristic(start), 0., start)]
    costs, parents = {start: 0.}, {}
    while queue:
        _, cost, here = heapq.heappop(queue)
        if cost != costs.get(here):
            continue
        if here == goal:
            route = [here]
            while here != start:
                here = parents[here]
                route.append(here)
            route.reverse()
            path = [grid.xy(rc) for rc in route]
            # Start is a continuous position on a previously checked edge.
            if np.linalg.norm(path[0]-start_xy) < 1e-9:
                path = path[1:]
            if not path:
                path = [np.array(goal_xy, dtype=float)]
            return path, costs[goal] + float(np.linalg.norm(grid.xy(start)-start_xy))
        r,c = here
        for dr,dc in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
            nxt = r+dr,c+dc
            if not (0 <= nxt[0] < grid.n and 0 <= nxt[1] < grid.n and allowed[nxt]):
                continue
            if dr and dc and not (allowed[r+dr,c] and allowed[r,c+dc]):
                continue
            length = math.sqrt((grid.cell*math.hypot(dr,dc))**2 + (mean[nxt]-mean[r,c])**2)
            new = cost+length
            if new < costs.get(nxt, math.inf):
                costs[nxt], parents[nxt] = new, here
                heapq.heappush(queue, (new+heuristic(nxt), new, nxt))
    return None


def compatible(agent, task):
    if task.kind == 'return':
        return task.id == 'return:'+agent.id
    return (agent.kind, task.kind) in {('drone','survey'), ('rover','inspect'), ('human','sample')}


def assign(agents, tasks, belief, config, policy):
    """Return feasible simultaneous assignments; reserve current work until finished."""
    idle = [a for a in agents if a.task is None and not a.returned]
    available = [t for t in tasks.values() if t.state == 'open']
    if not idle or not available:
        return []
    impossible, dummy = 1e12, 1e8
    matrix = np.full((len(idle),len(available)+len(idle)), dummy)
    paths, allowed_by_kind = {}, {}
    for i, a in enumerate(idle):
        if a.kind != 'drone':
            key = a.slope_limit
            if key not in allowed_by_kind:
                allowed_by_kind[key] = belief.traversable(key, config['ground_sigma_gate_m'])
        for j,t in enumerate(available):
            matrix[i,j] = impossible
            if not compatible(a,t):
                continue
            if a.kind == 'drone':
                path = [np.array(t.xy)]
                length = float(np.linalg.norm(a.xy-t.xy))
            else:
                found = astar(belief.grid, belief.mean, allowed_by_kind[a.slope_limit], a.xy,t.xy)
                if found is None:
                    continue
                path, length = found
            cost = length/a.speed + (0 if t.kind == 'return' else a.service)
            if t.kind == 'survey' and policy == 'information_hungarian':
                cost -= config['information_bonus_s']*belief.information_gain(t.xy,a.radius,a.sigma)
            matrix[i,j], paths[i,j] = cost,path
    if policy == 'information_hungarian':
        rows,cols = linear_sum_assignment(matrix)
        pairs = list(zip(rows.tolist(),cols.tolist()))
    elif policy == 'nearest_greedy':
        # Deterministic greedy baseline, no information bonus or simultaneous optimal matching.
        pairs, used = [], set()
        for i in range(len(idle)):
            options = [(matrix[i,j],j) for j in range(len(available)) if j not in used]
            if options:
                val,j = min(options)
                if val < dummy:
                    pairs.append((i,j)); used.add(j)
    else:
        raise ValueError(f"Unknown policy: {policy}")
    return [(idle[i],available[j],paths[i,j],float(matrix[i,j])) for i,j in pairs
            if j < len(available) and matrix[i,j] < dummy]


def load_data(folder):
    folder = Path(folder)
    meta = json.loads((folder/'metadata.json').read_text())
    path = folder/'terrain.npz'
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta['terrain_sha256']:
        raise ValueError('Data checksum mismatch')
    if meta['dataset_type'] != 'USGS_MRO_REAL_RASTER_CROPS':
        raise ValueError('Real-data pilot requires an explicitly identified USGS import')
    with np.load(path,allow_pickle=False) as data:
        ref, prior, valid = data['reference'].copy(),data['prior'].copy(),data['valid'].astype(bool)
    if ref.shape != prior.shape or ref.ndim != 2 or ref.shape[0] != ref.shape[1]:
        raise ValueError('Expected aligned square grids')
    valid &= np.isfinite(ref) & np.isfinite(prior)
    if not valid.all():
        raise ValueError('This first pilot requires a fully covered crop; no implicit no-data filling')
    return ref,prior,valid,meta


def run(reference, prior, valid, metadata, config, policy='information_hungarian'):
    if metadata['cell_m']<=0 or not 1<=config['survey_grid_n']<=32:
        raise ValueError('Invalid metric grid or survey partition')
    if config['initial_sigma_m']<=0 or config['snapshot_interval_s']<=0:
        raise ValueError('Positive sigma and snapshot interval required')
    for spec in config['agents']:
        if min(spec['speed_m_s'],spec['sensor_radius_m'],spec['sensor_sigma_m'])<=0:
            raise ValueError('Speeds and sensor parameters must be positive')
    grid = Grid(len(prior), metadata['cell_m'])
    belief = Belief(prior,valid,grid,config['initial_sigma_m'])
    world = SimulatedWorld(reference,valid,grid,config['injected_sites'],config['seed'])
    agents = []
    for a in config['agents']:
        pos = grid.xy(grid.rc(a['start_xy_m']))
        agents.append(Agent(a['id'],a['kind'],pos.copy(),pos.copy(),a['speed_m_s'],a['sensor_radius_m'],
                            a['sensor_sigma_m'],a['max_slope_deg'],a['service_s']))
    if sorted(a.id for a in agents) != ['drone_1','drone_2','human_1','human_2','rover_1','rover_2']:
        raise ValueError('This pilot requires the six named agents')
    if not config['global_instant_communication']:
        raise ValueError('Connectivity constraints are intentionally not implemented')
    tasks, events, frames, metrics, trajectory = {}, [], [], [], []
    seen, now, last_frame, returning = set(), 0., -math.inf, False
    dt = config['dt_s']
    if dt <= 0:
        raise ValueError('dt_s must be positive')
    initial_rmse = world.evaluate(belief)
    def emit(event_type, at=None, **fields):
        events.append(dict(time_s=float(now if at is None else at),event=event_type,**fields))
    ng = config['survey_grid_n']
    for r in range(ng):
        for c in range(ng):
            xy = [-grid.half+(c+.5)*grid.n*grid.cell/ng, grid.half-(r+.5)*grid.n*grid.cell/ng]
            xy = grid.xy(grid.rc(xy)).tolist()
            tid = f'survey:{r}:{c}'
            tasks[tid] = Task(tid,'survey',xy,0.)
    # An explicit initial habitat survey is shared. It is a scenario assumption, not orbital knowledge.
    base = np.mean([a.home for a in agents],axis=0)
    mask,values,_ = world.observe(base,config['initial_base_survey_radius_m'],.25)
    belief.update(mask,values,.25,4)
    emit('initial_base_survey',cells=int(mask.sum()))
    last_assignment_version = -1
    ground_unknown_steps = 0
    slope_max_actual = {'human':0.,'rover':0.}
    reference_slopes = slopes(reference,grid.cell)  # evaluator only
    wall_start = time.monotonic()
    while now <= config['max_time_s']:
        # Shared sensor updates occur before planning. No range/connectivity gating.
        for a in agents:
            mask,values,detections = world.observe(a.xy,a.radius,a.sigma)
            belief.update(mask,values,a.sigma,{'drone':1,'rover':2,'human':3}[a.kind])
            for sid,xy in detections.items():
                if sid not in seen:
                    seen.add(sid)
                    tid='inspect:'+sid
                    tasks[tid]=Task(tid,'inspect',xy.tolist(),now,site=sid)
                    emit('site_detected',site=sid,agent=a.id,xy_m=xy.tolist(),injected=True)
                    emit('task_created',task=tid,kind='inspect',site=sid)
        # Suppress redundant survey goals only if their own tile is almost fully observed.
        for t in tasks.values():
            if t.kind=='survey' and t.state=='open':
                _,r,c=t.id.split(':'); r,c=int(r),int(c)
                ys=slice(round(r*grid.n/ng),round((r+1)*grid.n/ng))
                xs=slice(round(c*grid.n/ng),round((c+1)*grid.n/ng))
                if belief.observed[ys,xs].mean() >= .99:
                    t.state='superseded'; t.completed_s=now
                    emit('survey_superseded',task=t.id)
        active_work = [t for t in tasks.values() if t.kind!='return' and t.state in ('open','assigned')]
        if not active_work and not returning:
            returning=True
            for a in agents:
                tid='return:'+a.id
                tasks[tid]=Task(tid,'return',a.home.tolist(),now)
            emit('return_phase')
        # Reassign on belief changes, task completion, or at 20-s decision intervals.
        if belief.version != last_assignment_version or now % 20 < dt:
            for a,t,path,cost in assign(agents,tasks,belief,config,policy):
                t.state,t.assigned_to='assigned',a.id
                a.task,a.path=t.id,[np.asarray(x,dtype=float) for x in path]
                a.dwell=0 if t.kind=='return' else (config['survey_dwell_s'] if t.kind=='survey' else a.service)
                emit('assigned',task=t.id,kind=t.kind,agent=a.id,score_s=round(cost,5),waypoints=len(path))
            last_assignment_version=belief.version
        positions={a.id:[float(a.xy[0]),float(a.xy[1]),world.elevation(a.xy)-metadata['origin_z_m']+(40 if a.kind=='drone' else .12), a.heading] for a in agents}
        trajectory.append({'time_s':now,'positions':positions,'tasks':{a.id:a.task for a in agents}})
        if now-last_frame >= config['snapshot_interval_s'] or all(a.returned for a in agents):
            frame={'time_s':now,'positions':positions,'tasks':{a.id:a.task for a in agents},
                   'seen_sites':sorted(seen),'completed_samples':sum(t.kind=='sample' and t.state=='done' for t in tasks.values()),
                   'coverage':float(belief.observed[valid].mean())}
            frames.append((frame,belief.mean.copy(),belief.var.copy(),belief.observed.copy()))
            metrics.append({'time_s':now,'coverage':frame['coverage'],'rmse_m':world.evaluate(belief),
                            'mean_sigma_m':float(np.sqrt(belief.var[valid]).mean()),'completed_samples':frame['completed_samples']})
            last_frame=now
        if all(a.returned for a in agents):
            break
        allowed_cache={}
        for a in agents:
            if a.task is None:
                continue
            t=tasks[a.task]
            if a.kind!='drone':
                if a.slope_limit not in allowed_cache:
                    allowed_cache[a.slope_limit]=belief.traversable(a.slope_limit,config['ground_sigma_gate_m'])
                legal=allowed_cache[a.slope_limit]
                if a.path and not legal[grid.rc(a.path[0])]:
                    t.state,t.assigned_to='open',None
                    a.task,a.path=None,[]
                    emit('path_replan',agent=a.id,task=t.id)
                    last_assignment_version=-1
                    continue
            # Ground speed is along the estimated 3D path, aerial speed is horizontal.
            # No vehicle dynamics or inter-agent body collision model is claimed.
            remaining=dt
            while a.path and remaining > 1e-9:
                nxt=a.path[0]
                if a.kind!='drone' and not legal[grid.rc(nxt)]:
                    break
                delta=nxt-a.xy
                horizontal=float(np.linalg.norm(delta))
                dz = 0 if a.kind=='drone' else grid.height(belief.mean,nxt)-grid.height(belief.mean,a.xy)
                distance=math.hypot(horizontal,dz)
                move=min(distance,a.speed*remaining)
                if distance > 1e-10:
                    a.xy += delta*move/distance
                    a.heading=math.atan2(delta[1],delta[0])
                a.distance+=move
                remaining-=move/a.speed
                if distance <= move+1e-8:
                    a.path.pop(0)
                else:
                    break
            if a.kind!='drone':
                rc=grid.rc(a.xy)
                if not belief.observed[rc]:
                    ground_unknown_steps += 1
                slope_max_actual[a.kind]=max(slope_max_actual[a.kind],float(reference_slopes[rc]))
            if not a.path:
                a.dwell-=remaining
                if a.dwell<=1e-8:
                    t.state,t.completed_s='done',now+dt
                    a.done.append(t.id);a.task=None
                    emit('completed',at=now+dt,task=t.id,kind=t.kind,agent=a.id)
                    last_assignment_version=-1
                    if t.kind=='inspect':
                        tid='sample:'+t.site
                        tasks[tid]=Task(tid,'sample',t.xy,now+dt,site=t.site,dependency=t.id)
                        emit('task_created',at=now+dt,task=tid,kind='sample',site=t.site,dependency=t.id)
                    if t.kind=='return':
                        a.returned=True
        now += dt
    summary={
        'schema_version':1,'policy':policy,'seed':config['seed'],
        'engine':'2.5D mission-level simulation; NOT a Gazebo dynamics run',
        'communication':'global, instantaneous, lossless',
        'success':all(a.returned for a in agents) and sum(t.kind=='sample' and t.state=='done' for t in tasks.values())==len(config['injected_sites']), 'duration_s':min(now,config['max_time_s']),
        'initial_rmse_m':initial_rmse,'final_rmse_m':world.evaluate(belief),
        'observed_fraction':float(belief.observed[valid].mean()),
        'conditional_sigma_initial_m':config['initial_sigma_m'],
        'conditional_sigma_final_mean_m':float(np.sqrt(belief.var[valid]).mean()),
        'discovered_sites':len(seen),'injected_sites_total':len(config['injected_sites']),
        'inspections_completed':sum(t.kind=='inspect' and t.state=='done' for t in tasks.values()),
        'samples_completed':sum(t.kind=='sample' and t.state=='done' for t in tasks.values()),
        'ground_steps_in_unobserved_cells':ground_unknown_steps,
        'actual_slope_max_deg_on_sampled_positions':slope_max_actual,
        'agents':{a.id:{'kind':a.kind,'distance_m':round(a.distance,4),'tasks_completed':a.done,'returned':a.returned} for a in agents},
        'unfinished_tasks':[t.id for t in tasks.values() if t.state in ('open','assigned')],
        'runtime_wall_s':time.monotonic()-wall_start,
        'terrain_sha256':metadata['terrain_sha256'],
        'mission_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'map_source_fraction':{name:float((belief.source[valid]==code).mean()) for code,name in [(0,'orbital_only'),(1,'drone'),(2,'rover'),(3,'human'),(4,'initial_base_survey')]},
        'versions':{'python':platform.python_version(),'numpy':np.__version__},
        'limitations':[
            'Sensor readings are simulated height observations of a held-out orbital DEM, not photogrammetry.',
            'Injected targets and sampling outcomes are fictional and explicitly labelled.',
            'Independent per-cell belief approximation; sigma is conditional simulation uncertainty, not NASA accuracy.',
            'No rotor dynamics, human biomechanics, energy/EVA budget, soil traction or inter-agent collision checking.',
            'Kinematic human/rover speed limits are hypothetical, not spacecraft or certified EVA specifications.',
            'Assignment is Hungarian over current feasible tasks with an information term; not global mission optimality or full DisCoverage.',
        ]}
    return {'summary':summary,'events':sorted(events,key=lambda e:e['time_s']),'frames':frames,'trajectory':trajectory,'metrics':metrics,'tasks':tasks,'belief':belief}


def save(result, folder, config):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for name,value in [('summary',result['summary']),('scenario_used',config),
                       ('tasks',[asdict(t) for t in result['tasks'].values()])]:
        (folder/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    (folder/'events.jsonl').write_text(''.join(json.dumps(e,allow_nan=False)+'\n' for e in result['events']))
    (folder/'trajectory.jsonl').write_text(''.join(json.dumps(f,allow_nan=False)+'\n' for f in result['trajectory']))
    with (folder/'metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result['metrics'][0]));w.writeheader();w.writerows(result['metrics'])
    b=result['belief']
    np.savez_compressed(folder/'belief_final.npz',mean=b.mean,var=b.var,observed=b.observed,source=b.source)
    np.savez_compressed(folder/'belief_frames.npz',mean=np.array([x[1] for x in result['frames']]),
                        var=np.array([x[2] for x in result['frames']]),observed=np.array([x[3] for x in result['frames']]))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/jezero')
    p.add_argument('--config',default=str(Path(__file__).with_name('scenario.json')))
    p.add_argument('--out',default='evidence/jezero')
    p.add_argument('--policy',choices=['information_hungarian','nearest_greedy'],default='information_hungarian')
    p.add_argument('--seed',type=int)
    a=p.parse_args();config=json.loads(Path(a.config).read_text())
    if a.seed is not None:config['seed']=a.seed
    result=run(*load_data(a.data),config,a.policy)
    save(result,a.out,config)
    print(json.dumps(result['summary'],indent=2))
    if not result['summary']['success']:
        raise SystemExit(2)


if __name__=='__main__':
    main()
