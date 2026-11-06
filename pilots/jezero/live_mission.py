"""Observation, planning and task exchange for the live Gazebo experiments."""
from dataclasses import dataclass
import heapq
import math

import numpy as np
from scipy.ndimage import binary_dilation

from mission import Agent, Belief, Grid, Task, assign, astar

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


def project(depth, rgb, xy, camera_z, grid, fov, stamp, noise):
    """Project actual depth pixels in a nadir camera at world yaw zero."""
    height,width = depth.shape
    v,u = np.indices(depth.shape)
    focal = width/(2*math.tan(fov/2))
    good = np.isfinite(depth) & (depth>.1) & (depth<75)
    d = depth[good]
    x = xy[0]-(v[good]-(height-1)/2)*d/focal
    y = xy[1]-(u[good]-(width-1)/2)*d/focal
    z = camera_z-d
    color = rgb[good]
    row = np.floor((grid.half-y)/grid.cell).astype(int)
    col = np.floor((x+grid.half)/grid.cell).astype(int)
    valid = (row>=0)&(row<grid.n)&(col>=0)&(col<grid.n)
    row,col,x,y,z,color = (a[valid] for a in (row,col,x,y,z,color))
    signature = color>145
    saturated = np.all((color<95)|(color>145),axis=1)
    red = np.all(signature==(1,0,0),axis=1)&saturated
    occupied = np.zeros((grid.n,grid.n),bool)
    occupied[row[red],col[red]] = True
    sites = {}
    tagged = red.copy()
    for sid,wanted in COLORS.items():
        hits = np.all(signature==wanted,axis=1)&saturated
        tagged |= hits
        if hits.sum()>=2:
            point = [float(np.median(x[hits])),float(np.median(y[hits]))]
            sites[sid] = grid.xy(grid.rc(point)).tolist()
    terrain = ~tagged
    counts = np.zeros(occupied.shape,int)
    totals = np.zeros(occupied.shape)
    np.add.at(counts,(row[terrain],col[terrain]),1)
    np.add.at(totals,(row[terrain],col[terrain]),z[terrain])
    mask = counts>=2
    values = np.full(occupied.shape,np.nan)
    values[mask] = totals[mask]/counts[mask]+noise[mask]
    return Observation(stamp,mask,values,occupied,sites)


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
            if site not in self.seen:
                self.seen[site] = xy
                task = 'inspect:'+site
                self.tasks[task] = Task(task,'inspect',xy,now,site=site)
                self.emit('site_detected',site=site,xy=xy,sensor_stamp_s=packet.stamp)

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
            if len(self.seen)==4 and all(t.state=='done' for t in self.tasks.values() if t.kind!='return'):
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
            proposals = assign(eligible,self.tasks,self.belief,
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
