"""Observation, planning and task exchange for the live Gazebo experiments."""
from dataclasses import dataclass, field
import heapq
import math

import numpy as np
from scipy.ndimage import binary_dilation

from mission import Agent, Belief, Grid, Task, assign, astar, slopes
from extension_cases import GROUND_SCOUT

LEASE_S = 14.
RESEND_S = 2.
COLORS = {'S1':(0,1,0), 'S2':(0,0,1), 'S3':(1,0,1), 'S4':(0,1,1)}


@dataclass
class Observation:
    stamp: float
    mask: np.ndarray
    heights: np.ndarray
    occupied: np.ndarray
    sites: dict
    source: str = ""
    pose: tuple = ()
    confidence: dict = field(default_factory=dict)


def project(depth, rgb, xy, camera_z, grid, fov, stamp, noise, *, ground_yaw=None):
    """Project actual depth pixels in a nadir camera at world yaw zero."""
    height,width = depth.shape
    v,u = np.indices(depth.shape)
    focal = width/(2*math.tan(fov/2))
    good = np.isfinite(depth) & (depth>.1) & (depth<(75 if ground_yaw is None else 5.5))
    d = depth[good]
    lateral = -(u[good]-(width-1)/2)*d/focal
    down = (v[good]-(height-1)/2)*d/focal
    if ground_yaw is None:
        x,y,z = xy[0]-down,xy[1]+lateral,camera_z-d
    else:
        forward = math.cos(.12)*d-math.sin(.12)*down
        x = xy[0]+math.cos(ground_yaw)*forward-math.sin(ground_yaw)*lateral
        y = xy[1]+math.sin(ground_yaw)*forward+math.cos(ground_yaw)*lateral
        z = camera_z-math.sin(.12)*d-math.cos(.12)*down
    color = rgb[good]
    row = np.floor((grid.half-y)/grid.cell).astype(int)
    col = np.floor((x+grid.half)/grid.cell).astype(int)
    valid = (row>=0)&(row<grid.n)&(col>=0)&(col<grid.n)
    row,col,x,y,z,color = (a[valid] for a in (row,col,x,y,z,color))
    high,low = (145,95) if ground_yaw is None else (200,45)
    signature = color>high
    saturated = np.all((color<low)|(color>high),axis=1)
    red = np.all(signature==(1,0,0),axis=1)&saturated
    occupied = np.zeros((grid.n,grid.n),bool)
    occupied[row[red],col[red]] = True
    sites,confidence = {},{}
    tagged = red.copy()
    for sid,wanted in COLORS.items():
        hits = np.all(signature==wanted,axis=1)&saturated
        tagged |= hits
        if hits.sum()>=(2 if ground_yaw is None else 12):
            point = [float(np.median(x[hits])),float(np.median(y[hits]))]
            sites[sid] = grid.xy(grid.rc(point)).tolist()
            confidence[sid] = min(1.,float(hits.sum())/12.)
    terrain = ~tagged
    counts = np.zeros(occupied.shape,int)
    totals = np.zeros(occupied.shape)
    np.add.at(counts,(row[terrain],col[terrain]),1)
    np.add.at(totals,(row[terrain],col[terrain]),z[terrain])
    mask = (counts>=2) & (ground_yaw is None)
    values = np.full(occupied.shape,np.nan)
    values[mask] = totals[mask]/counts[mask]+noise[mask]
    return Observation(stamp,mask,values,occupied,sites,confidence=confidence)


class Channel:
    """Inject faults only into mission messages, never vehicle control."""
    def __init__(self, mode, seed, emit):
        self.mode,self.emit = mode,emit
        self.random = np.random.default_rng(seed)
        self.pending = []
        self.sequence = 0
        self.cut = None

    def blocked(self, sender, receiver, now):
        return self.cut is not None and self.cut[0] in (sender,receiver) and self.cut[1]<=now<self.cut[2]

    def send(self, sender, receiver, message, now):
        if self.blocked(sender,receiver,now) or (self.mode=='loss' and self.random.random()<.1):
            self.emit('message_dropped',sender=sender,receiver=receiver,message=message[0])
            return
        self.sequence += 1
        heapq.heappush(self.pending,(now+(2 if self.mode=='delay' else 0),
                                     self.sequence,sender,receiver,message))

    def receive(self, now):
        while self.pending and self.pending[0][0]<=now:
            _,_,sender,receiver,message = heapq.heappop(self.pending)
            if not self.blocked(sender,receiver,now):
                yield sender,receiver,message


@dataclass
class Lease:
    token: int
    task: str
    path: list
    expires: float


class Mission:
    """Consumes CTX prior, observed packets and public navigation state only."""
    def __init__(self, prior, homes, pilot, policy, link, seed, emit):
        self.grid = Grid(len(prior),4.)
        self.belief = Belief(prior,np.isfinite(prior),self.grid,3.)
        self.blocked = np.zeros(prior.shape,bool)
        self.pilot,self.policy,self.emit = pilot,policy,emit
        self.channel = Channel(link,seed,emit)
        self.agents = {}
        for name,home in homes.items():
            kind = name.split('_')[0]
            speed,service = {'drone':(4.,1.),'rover':(.85,4.),'human':(1.,6.)}[kind]
            self.agents[name] = Agent(name,kind,np.array(home,float),np.array(home,float),
                                      speed,30.,.20,18.,service)
        self.tasks = {}
        if pilot==1:
            self.tasks['survey:fixed'] = Task('survey:fixed','survey',[38.,-2.],0.)
            self.tasks['inspect:goal'] = Task('inspect:goal','inspect',[46.,-2.],0.)
        else:
            for x in (-46,-14,18,46):
                for y in (-46,-14,18,46):
                    key = f'survey:{x}:{y}'
                    self.tasks[key] = Task(key,'survey',[x,y],0.)
        self.leases = {}
        self.seen = {}
        self.counter = 0
        self.last_tick = -RESEND_S
        self.cut_finished = False
        self.recovery_s = None
        self.reassignments = 0
        self.rejected = 0
        self.completed = False

    def route(self, xy, goal):
        allowed = ~binary_dilation(self.blocked,iterations=1)
        return astar(self.grid,self.belief.mean,allowed,xy,goal)

    def observation(self, packet, now):
        self.belief.update(packet.mask,packet.heights,.2,1)
        newly_blocked = packet.occupied & ~self.blocked
        self.blocked |= packet.occupied
        if newly_blocked.any():
            self.emit('obstacle_observed',sensor_stamp_s=packet.stamp,cells=int(newly_blocked.sum()))
            if self.pilot==1 and 'rover_1' in self.leases:
                lease = self.leases['rover_1']
                if lease.task=='inspect:goal':
                    agent = self.agents['rover_1']
                    goal = self.tasks[lease.task].xy
                    route = self.route(agent.xy,goal)
                    old_path = lease.path
                    self.counter += 1
                    self.leases[agent.id] = Lease(self.counter,lease.task,
                                                   route[0] if route else [],now+LEASE_S)
                    self.emit('replan',agent=agent.id,sensor_stamp_s=packet.stamp,
                              path=[p.tolist() for p in self.leases[agent.id].path],
                              replaced_cells=len(old_path),route_available=route is not None)
                    self.send_lease(agent.id,now)
        if self.pilot==1:
            return
        for site,xy in packet.sites.items():
            self.reveal(site,xy,now,packet.source,packet.stamp,packet.pose,packet.confidence.get(site))

    def reveal(self,site,xy,now,source,sensor_stamp,pose=(),confidence=None):
        if site in self.seen:
            return
        self.seen[site] = xy
        task = 'inspect:'+site
        self.tasks[task] = Task(task,'inspect',xy,now,site=site)
        self.emit('site_detected',site=site,xy=xy,sensor_stamp_s=sensor_stamp,
                  observer=source,observer_pose=pose,confidence=confidence)

    def ready_to_return(self):
        return len(self.seen)==4 and all(t.state=='done' for t in self.tasks.values() if t.kind!='return')

    def assignable_tasks(self):
        return self.tasks

    def send_lease(self, name, now):
        lease = self.leases[name]
        waypoints = tuple((float(x),float(y),self.grid.height(self.belief.mean,(x,y))+.08)
                          for x,y in lease.path)
        self.channel.send('coordinator',name,('lease',lease.token,lease.task,
                                              waypoints,
                                              now+LEASE_S),now)

    def finish(self, name, task_id, token, now):
        lease = self.leases.get(name)
        if not lease or (lease.task,lease.token)!=(task_id,token) or now>=lease.expires:
            self.rejected += 1
            self.emit('confirmation_rejected',agent=name,task=task_id,token=token)
            return
        task = self.tasks[task_id]
        task.state,task.completed_s = 'done',now
        del self.leases[name]
        agent = self.agents[name]
        agent.task = None
        agent.returned = task.kind=='return'
        self.emit('task_completed',agent=name,task=task_id,token=token)
        if task.kind=='inspect' and self.pilot!=1:
            key = 'sample:'+task.site
            self.tasks[key] = Task(key,'sample',task.xy,now,site=task.site,dependency=task.id)
            self.emit('sample_enabled',task=key,dependency=task.id)
        self.channel.send('coordinator',name,('clear',token),now)

    def receive(self, name, message, now):
        kind,*args = message
        if kind=='observation':
            self.observation(args[0],now)
        elif kind=='status':
            if self.channel.cut and name==self.channel.cut[0] and now>=self.channel.cut[2] and self.recovery_s is None:
                self.recovery_s = now-self.channel.cut[2]
                self.emit('link_status_recovered',agent=name,recovery_s=self.recovery_s)
            xy,token = args
            agent = self.agents[name]
            agent.xy = np.array(xy)
            lease = self.leases.get(name)
            if lease and lease.token==token:
                lease.expires = now+LEASE_S
        elif kind=='complete':
            self.finish(name,*args,now)

    def tick(self, now):
        if self.pilot==1 and self.tasks['inspect:goal'].state=='done' and self.tasks['survey:fixed'].state=='done':
            self.completed = True
            return
        if self.channel.cut and now>=self.channel.cut[2] and not self.cut_finished:
            self.cut_finished = True
            self.emit('link_restored',agent=self.channel.cut[0])
        if now-self.last_tick<RESEND_S:
            return
        self.last_tick = now
        for name,lease in list(self.leases.items()):
            if now>=lease.expires:
                del self.leases[name]
                self.tasks[lease.task].state = 'open'
                self.agents[name].task = None
                self.reassignments += 1
                self.emit('lease_expired',agent=name,task=lease.task,token=lease.token)
        if self.pilot!=1:
            if self.ready_to_return():
                for a in self.agents.values():
                    key = 'return:'+a.id
                    self.tasks.setdefault(key,Task(key,'return',a.home.tolist(),now))
            self.completed = all(a.returned for a in self.agents.values())
        eligible = [a for a in self.agents.values() if not self.channel.blocked('coordinator',a.id,now)]
        if self.pilot==1:
            proposals = []
            for a,task_id in ((self.agents['drone_1'],'survey:fixed'),
                              (self.agents['rover_1'],'inspect:goal')):
                task = self.tasks[task_id]
                if task.state=='open':
                    path = [np.array(task.xy)] if a.kind=='drone' else self.route(a.xy,task.xy)
                    if path is not None:
                        proposals.append((a,task,path if a.kind=='drone' else path[0],0))
        else:
            proposals = assign(eligible,self.assignable_tasks(),self.belief,
                               {'ground_sigma_gate_m':1.,'information_bonus_s':65.},self.policy)
        for agent,task,path,_ in proposals:
            self.counter += 1
            task.state,task.assigned_to = 'assigned',agent.id
            agent.task = task.id
            self.leases[agent.id] = Lease(self.counter,task.id,path,now+LEASE_S)
            self.emit('assigned',agent=agent.id,task=task.id,token=self.counter,
                      path=[p.tolist() for p in path])
            if self.channel.mode=='cut' and self.channel.cut is None and task.kind=='inspect':
                self.channel.cut = (agent.id,now+3.,now+63.)
                self.emit('link_cut_scheduled',agent=agent.id,start_s=now+3.,end_s=now+63.)
        for name in self.leases:
            self.send_lease(name,now)

class ScarpBelief(Belief):
    def __init__(self, old, occupied):
        super().__init__(old.mean,old.valid,old.grid,3.)
        self.occupied = occupied

    def safe(self, slope_limit):
        allowed = ~binary_dilation(self.occupied,iterations=1)
        allowed[[0,-1],:] = False
        allowed[:,[0,-1]] = False
        # Limit an individual step in addition to the local mean slope.
        jump = np.zeros_like(self.mean)
        for axis in (0,1):
            diff = np.abs(np.diff(self.mean,axis=axis))
            if axis==0:
                jump[:-1] = np.maximum(jump[:-1],diff)
                jump[1:] = np.maximum(jump[1:],diff)
            else:
                jump[:,:-1] = np.maximum(jump[:,:-1],diff)
                jump[:,1:] = np.maximum(jump[:,1:],diff)
        acceptable = (slopes(self.mean,self.grid.cell)<=slope_limit) & (jump<=self.grid.cell*math.tan(math.radians(slope_limit)))
        return allowed & (~self.observed | acceptable)

    def traversable(self,slope_limit,sigma_gate):
        return super().traversable(slope_limit,sigma_gate) & self.safe(slope_limit)


class ExtensionMission(Mission):
    """Only sensor observations enter the planner; no scenario geometry is loaded here."""
    def __init__(self,prior,homes,pilot,policy,link,seed,emit):
        super().__init__(prior,homes,pilot,policy,link,seed,emit)
        if pilot==5:
            self.belief = ScarpBelief(self.belief,self.blocked)
            for agent in self.agents.values():
                if agent.kind=='human':
                    agent.slope_limit = 22.
        else:
            key = 'ground_survey:rover_1'
            self.tasks[key] = Task(key,'ground_survey',list(GROUND_SCOUT),0.)

    def assignable_tasks(self):
        # Reserve the shared departure corridor for the ground scout until it clears it.
        scout = self.tasks.get('ground_survey:rover_1')
        if scout and scout.state!='done':
            return {key:task for key,task in self.tasks.items() if task.kind in ('survey','ground_survey')}
        return super().assignable_tasks()

    def ready_to_return(self):
        if self.pilot!=5:
            return super().ready_to_return()
        if len(self.seen)!=1 or any(task.state!='done' for task in self.tasks.values()
                                   if task.kind=='survey'):
            return False
        for task in self.tasks.values():
            if task.kind not in ('inspect','sample') or task.state!='open':
                continue
            kind = 'rover' if task.kind=='inspect' else 'human'
            candidates = [agent for agent in self.agents.values() if agent.kind==kind]
            if all(astar(self.grid,self.belief.mean,self.belief.safe(a.slope_limit),a.xy,task.xy) is None
                   for a in candidates):
                task.state = 'inaccessible'
                self.emit('ground_inaccessible',task=task.id,xy=task.xy,role=kind)
        return all(task.state in ('done','inaccessible') for task in self.tasks.values() if task.kind!='return')
