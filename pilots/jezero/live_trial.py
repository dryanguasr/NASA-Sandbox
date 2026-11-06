"""Run a live Jezero trial. Gazebo pose commands are never used to move agents."""
from collections import deque
from dataclasses import dataclass, field
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.contacts_pb2 import Contacts
from gz.msgs10.image_pb2 import Image as GzImage
from gz.msgs10.imu_pb2 import IMU
from gz.msgs10.odometry_pb2 import Odometry
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.twist_pb2 import Twist
from gz.transport13 import Node
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from live_mission import Mission, project
from live_world import BASE, BLOCK_XY, FOV, LAYOUTS, build, prepare
from mission import load_data

ROOT_TOPIC = '/world/jezero_live'
CTRL_DT = .10
STALE_S = 2.
VIDEO_W, VIDEO_H = 1176,600


def stamp(header):
    return header.stamp.sec+header.stamp.nsec*1e-9


def heading(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))


def xyz_yaw(pose):
    yaw = heading(pose.orientation)
    p = pose.position
    return (p.x,p.y,p.z,yaw)


@dataclass
class Worker:
    token: int = 0
    task: str = ''
    expires: float = 0.
    waypoints: deque = field(default_factory=deque)
    arrived: float | None = None
    goal: tuple | None = None
    last_complete: float = -100.
    expired_logged: bool = False
    odom_missing: bool = False

    def accept(self, message):
        kind,*args = message
        if kind=='clear':
            if args[0]==self.token:
                self.task = ''
                self.waypoints.clear()
            return
        token,task,path,expires = args
        if token<self.token or (token==self.token and not self.task):
            return
        if token>self.token:
            self.token,self.task,self.waypoints = token,task,deque(path)
            self.arrived = None
            self.expired_logged = False
            self.last_complete = -100.
            self.goal = path[-1][:2] if path else None
        self.expires = max(self.expires,expires)


class LiveIO:
    def __init__(self, homes, video, seed):
        self.node = Node()
        self.homes = homes
        self.now = 0.
        self.poses = {}
        self.history = {}
        self.odom = {}
        self.heading = {}
        self.wheel_previous = {}
        self.integrated = {}
        self.last_fix = {}
        self.fix_rng = np.random.default_rng(seed+600)
        self.suppress_wheel = False
        self.images = {}
        self.callbacks = []
        self.obstacle_contacts = 0
        self.node.subscribe(Contacts,"/live/obstacle/contacts",self.contacts)
        self.pubs = {name:self.node.advertise(f'/model/{name}/cmd_vel',Twist) for name in homes}
        self.node.subscribe(Clock,ROOT_TOPIC+'/clock',self.clock)
        self.node.subscribe(Pose_V,ROOT_TOPIC+'/pose/info',self.pose)
        for name in homes:
            if name.startswith('rover'):
                self.subscribe(Odometry,f'/model/{name}/odometry',self.wheel,name)
                self.subscribe(IMU,f'/live/{name}/imu',self.imu,name)
            if name.startswith('drone'):
                for key in ('depth_camera','camera'):
                    self.subscribe(GzImage,f'/live/{name}/{key}',self.image,(name,key))
            if video:
                self.subscribe(GzImage,f'/live/{name}/side',self.image,(name,'side'))
        if video:
            self.subscribe(GzImage,'/live/overview',self.image,('overview','video'))

    def contacts(self,msg):
        self.obstacle_contacts += len(msg.contact)

    def subscribe(self, kind, topic, cb, name):
        callback = lambda msg: cb(name,msg)
        self.callbacks.append(callback)
        self.node.subscribe(kind,topic,callback)

    def clock(self,msg):
        self.now = msg.sim.sec+msg.sim.nsec*1e-9

    def pose(self,msg):
        t = stamp(msg.header) or self.now
        for p in msg.pose:
            if p.name in self.homes:
                pose = xyz_yaw(p)
                self.poses[p.name] = (t,pose)
                history = self.history.setdefault(p.name,deque(maxlen=150))
                history.append((t,pose))

    def imu(self,name,msg):
        self.heading[name] = (stamp(msg.header) or self.now,heading(msg.orientation))

    def wheel(self,name,msg):
        pose = xyz_yaw(msg.pose)
        previous = self.wheel_previous.get(name,pose)
        self.wheel_previous[name] = pose
        imu = self.heading.get(name)
        t = stamp(msg.header) or self.now
        if imu is None or abs(t-imu[0])>.3:
            return
        # Wheel odometry supplies distance; simulated IMU supplies yaw.
        x,y = self.integrated.get(name,self.homes[name])
        dx,dy = pose[0]-previous[0],pose[1]-previous[1]
        distance = dx*math.cos(pose[3])+dy*math.sin(pose[3])
        yaw = imu[1]
        local_fix = self.poses.get(name)
        if t-self.last_fix.get(name,-10.)>=2 and local_fix and abs(t-local_fix[0])<.15:
            # Explicit idealized local positioning, distinct from raw evaluator poses.
            # Wheel odometry and IMU are still required for the controller watchdog.
            px,py = local_fix[1][:2]
            ox,oy = self.fix_rng.normal(0,.035,2)
            x,y,distance = px+ox,py+oy,0.
            self.last_fix[name] = t
        self.integrated[name] = (x+distance*math.cos(yaw),y+distance*math.sin(yaw))
        self.odom[name] = (t,(*self.integrated[name],pose[2],yaw))

    def image(self,key,msg):
        value = (stamp(msg.header),msg.width,msg.height,msg.step,bytes(msg.data))
        self.images[key] = value

    def navigation(self,name):
        if not name.startswith('rover'):
            return self.poses.get(name)
        return None if self.suppress_wheel else self.odom.get(name)

    def command(self,name,x=0.,y=0.,z=0.,yaw=0.):
        msg = Twist()
        msg.linear.x,msg.linear.y,msg.linear.z,msg.angular.z = x,y,z,yaw
        self.pubs[name].publish(msg)

    def observations(self, mission, previous, noise):
        for name in self.homes:
            depth = self.images.get((name,'depth_camera'))
            rgb = self.images.get((name,'camera'))
            if depth is None or rgb is None or depth[0]<=previous.get(name,-1):
                continue
            t,w,h,step,data = depth
            if abs(t-rgb[0])>.025 or step!=4*w or rgb[3]!=3*w or (w,h)!=rgb[1:3]:
                continue
            history = list(self.history.get(name,()))
            if not history:
                continue
            pt,pose = min(history,key=lambda item:abs(t-item[0]))
            if abs(t-pt)>.12:
                continue
            previous[name] = t
            yield name,project(np.frombuffer(data,'<f4').reshape(h,w),
                               np.frombuffer(rgb[4],np.uint8).reshape(h,w,3),
                               pose[:2],pose[2]-.25,mission.grid,FOV,t,noise)


def publish_control(io,name,worker,mission,altitude,now):
    nav = io.navigation(name)
    if nav is None or now-nav[0]>STALE_S:
        if not worker.odom_missing:
            mission.emit('navigation_stale_stop',agent=name)
            worker.odom_missing = True
        io.command(name)
        return
    worker.odom_missing = False
    if not worker.task or now>=worker.expires:
        if worker.task and not worker.expired_logged:
            mission.emit('local_lease_stop',agent=name,task=worker.task,token=worker.token)
            worker.expired_logged = True
        io.command(name)
        return
    x,y,z,yaw = nav[1]
    agent = mission.agents[name]
    # Stop at each waypoint within a bounded tracking tolerance.
    while worker.waypoints and math.dist((x,y),worker.waypoints[0][:2])<.70:
        worker.waypoints.popleft()
    if not worker.waypoints:
        io.command(name)
        if worker.arrived is None:
            worker.arrived = now
        if now-worker.arrived>=agent.service and now-worker.last_complete>=2:
            if worker.goal is not None and math.dist((x,y),worker.goal)<1.2:
                mission.channel.send(name,'coordinator',('complete',worker.task,worker.token),now)
                worker.last_complete = now
        return
    goal = worker.waypoints[0]
    dx,dy = goal[0]-x,goal[1]-y
    distance = math.hypot(dx,dy)
    speed = min(agent.speed,max(.25,distance))
    if agent.kind=='rover':
        heading = math.atan2(dy,dx)-yaw
        error = math.atan2(math.sin(heading),math.cos(heading))
        io.command(name,x=speed*max(0.,math.cos(error)) if abs(error)<.50 else 0.,
                   yaw=float(np.clip(2*error,-1.4,1.4)))
    else:
        target_z = altitude if agent.kind=='drone' else goal[2]
        io.command(name,x=speed*dx/distance,y=speed*dy/distance,z=float(np.clip(target_z-z,-.6,.6)))


class Video:
    def __init__(self, out, label):
        self.path = out/'live.mp4'
        self.label = label
        self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
        self.encoder = subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24',
                         '-s',f'{VIDEO_W}x{VIDEO_H}','-r','15','-i','-','-an','-c:v','libx264',
                         '-threads','2','-preset','veryfast','-crf','22','-pix_fmt','yuv420p',
                         '-movflags','+faststart',str(self.path)],stdin=subprocess.PIPE)
        self.frames = 0

    def draw(self, io, workers, t, coverage, event):
        keys = [('overview','video'),*((name,'side') for name in workers)]
        frames = {key:io.images.get(key) for key in keys}
        if any(frame is None for frame in frames.values()):
            return
        image = Image.new('RGB',(VIDEO_W,VIDEO_H),'#111923')
        draw = ImageDraw.Draw(image)
        def label(x,y,value):
            draw.text((x,y),value,font=self.font,fill='white')
        def paste(key,x,y):
            _,w,h,step,data = frames[key]
            if step==w*3:
                image.paste(Image.frombytes('RGB',(w,h),data),(x,y))
        paste(('overview','video'),300,12)
        draw.rectangle((300,12,876,40),fill='#111923')
        label(312,16,f'JEZERO | {self.label} | t={t:05.1f} s')
        draw.rectangle((300,557,876,587),fill='#111923')
        label(312,563,f'Cobertura {coverage:.1%} · {event}')
        kinds = {'drone':0,'rover':1,'human':2}
        colors = {'drone':'cyan','rover':'orange','human':'lightgreen'}
        for name, worker in workers.items():
            kind,i = name.split('_')
            x,y = (6 if i=='1' else 882),kinds[kind]*200+5
            paste((name,'side'),x,y+20)
            label(x+4,y,f'{name} · cuadrícula 4 m')
            label(x+4,y+183,worker.task or 'en espera')
            if name in io.poses:
                px,py,pz,_ = io.poses[name][1]
                scale = 576/(2*math.tan(1.24/2)*(102-pz))
                ax,ay = 588+px*scale,300-py*scale
                draw.ellipse((ax-5,ay-5,ax+5,ay+5),fill=colors[kind],outline='black')
        self.encoder.stdin.write(image.tobytes())
        self.frames += 1

    def close(self):
        self.encoder.stdin.close()
        if self.encoder.wait(timeout=25):
            raise RuntimeError('ffmpeg failed')


def trial(args):
    out = Path(args.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    data = prepare(args.zone)
    ref,prior,_,meta = load_data(data)
    world,homes,altitude = build(data,out,args.pilot,args.layout,args.video,args.rate)
    os.environ['GZ_PARTITION'] = f'jezero_live_{os.getpid()}'
    env = dict(os.environ,GZ_SIM_RESOURCE_PATH=str(out/'models'),LIBGL_ALWAYS_SOFTWARE='1',
               LP_NUM_THREADS='3',OMP_NUM_THREADS='1')
    io = LiveIO(homes,args.video,args.seed)
    workers = {name:Worker() for name in homes}
    t = 0.
    origin_clock = 0.
    last_event = 'inicio'
    completed_visits = {}
    event_file = (out/'events.jsonl').open('w',encoding='utf-8')
    def emit(kind,**payload):
        nonlocal last_event
        if kind=='task_completed' and payload['agent'] in io.poses:
            name,task = payload['agent'],payload['task']
            actual = io.poses[name][1][:2]
            payload['observed_xy_m'] = actual
            if args.pilot!=1 and task.startswith(('inspect:S','sample:S')):
                target = LAYOUTS[args.layout][int(task[-1])-1]
                completed_visits[task] = math.dist(actual,target)
        if 'sensor_stamp_s' in payload:
            payload['sensor_stamp_s'] -= origin_clock
        if kind in ('obstacle_observed','replan','site_detected','task_completed','local_lease_stop','link_restored'):
            last_event = kind
        event_file.write(json.dumps({'t_s':round(t,3),'event':kind,**payload})+'\n')
        event_file.flush()
    origin = meta['origin_z_m']
    mission = Mission(prior-origin,homes,args.pilot,args.policy,args.link,args.seed,emit)
    initial_rmse = float(np.sqrt(np.mean((prior-ref)**2)))
    noise = np.random.default_rng(args.seed).normal(0,.10,prior.shape)
    command = ['gz','sim','-s','-r','--headless-rendering','-v','2',str(world)]
    report = dict(vars(args),command=command,terrain_sha256=meta['terrain_sha256'],
                  gazebo=subprocess.check_output(['gz','sim','--versions'],text=True).strip())
    video = Video(out,f'P{args.pilot} {args.policy} {args.link}') if args.video else None
    previous_frames = {}
    distances = {name:0. for name in homes}
    previous = {}
    metric_time = last_status = video_time = -10.
    t80 = None
    inserted = False
    min_distance = math.inf
    sensor_frames = 0
    track_errors = []
    path_errors = []
    visits = {}
    odom_loss_start = odom_loss_end = None
    status = 'failed'
    error = None
    with (out/'gazebo.log').open('w') as log,(out/'states.jsonl').open('w') as states:
        server = subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,
                                  start_new_session=True)
        try:
            deadline = time.monotonic()+40
            required = [name for name in homes if name.startswith('drone')]
            while not (all(io.navigation(name) is not None for name in homes) and
                       all((name,'depth_camera') in io.images and (name,'camera') in io.images for name in required)):
                if time.monotonic()>deadline or server.poll() is not None:
                    raise RuntimeError(f'Topics unavailable: {io.node.topic_list()}')
                time.sleep(.04)
            start = origin_clock = io.now
            if args.smoke:
                for name in homes:
                    begin = io.poses[name][1][:2]
                    until = io.now+.7
                    while io.now<until:
                        if server.poll() is not None or time.monotonic()>deadline:
                            raise RuntimeError('Individual control test timed out')
                        io.command(name,x=.35)
                        time.sleep(.02)
                    io.command(name)
                    distance = math.dist(begin,io.poses[name][1][:2])
                    emit('individual_control',agent=name,displacement_m=distance,passed=distance>.025)
                    if distance<=.025:
                        raise RuntimeError(f'{name} did not respond to its individual command')
                start = origin_clock = io.now
            next_control = start
            deadline = time.monotonic()+max(120,args.max_time*2)
            while not mission.completed:
                t = io.now-start
                if t>=args.max_time:
                    status = 'timeout'
                    break
                if server.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError('Gazebo stopped or wall deadline exceeded')
                if io.now<next_control:
                    time.sleep(.004)
                    continue
                next_control = io.now+CTRL_DT
                io.suppress_wheel = args.drop_odom and 12<=t<19
                if args.drop_odom and 'rover_1' in io.poses:
                    if 13<=t<19 and odom_loss_start is None:
                        odom_loss_start = io.poses['rover_1'][1][:2]
                    if 18<=t<19:
                        odom_loss_end = io.poses['rover_1'][1][:2]
                if t-last_status>=1:
                    last_status = t
                    for name,worker in workers.items():
                        nav = io.navigation(name)
                        if nav is not None and io.now-nav[0]<=STALE_S:
                            mission.channel.send(name,'coordinator',('status',nav[1][:2],worker.token),t)
                for name,packet in io.observations(mission,previous_frames,noise):
                    sensor_frames += 1
                    mission.channel.send(name,'coordinator',('observation',packet),t)
                for sender,receiver,msg in mission.channel.receive(t):
                    if receiver=='coordinator':
                        mission.receive(sender,msg,t)
                    else:
                        workers[receiver].accept(msg)
                mission.tick(t)
                if args.pilot==1 and args.obstacle and not inserted and 'rover_1' in mission.leases:
                    initial_path = mission.leases['rover_1'].path
                    if not any(math.dist(p,BLOCK_XY)<3 for p in initial_path):
                        raise RuntimeError('Initial route does not cross obstacle fixture')
                    request = f'sdf_filename: "{(out/"obstacle.sdf").as_posix()}"'
                    result = subprocess.run(['gz','service','-s',ROOT_TOPIC+'/create/blocking',
                                 '--reqtype','gz.msgs.EntityFactory','--reptype','gz.msgs.Boolean',
                                 '--timeout','5000','--req',request],capture_output=True,text=True,timeout=8)
                    if result.returncode or 'data: true' not in result.stdout:
                        raise RuntimeError('Obstacle insertion failed: '+result.stdout+result.stderr)
                    inserted = True
                    emit('obstacle_inserted',xy=BLOCK_XY)
                for sender,receiver,msg in mission.channel.receive(t):
                    if receiver=='coordinator':
                        mission.receive(sender,msg,t)
                    else:
                        workers[receiver].accept(msg)
                for name,worker in workers.items():
                    publish_control(io,name,worker,mission,altitude,t)
                for name,worker in workers.items():
                    if worker.waypoints and name in io.poses:
                        key = (name,worker.token)
                        actual = io.poses[name][1][:2]
                        anchor = visits.setdefault(key,actual)
                        goal = worker.waypoints[0][:2]
                        a,b = np.asarray(anchor),np.asarray(goal)
                        seg = b-a
                        if float(seg@seg)>1e-6:
                            offset = np.asarray(actual)-a
                            path_errors.append(float(np.linalg.norm(offset-np.clip(offset@seg/(seg@seg),0,1)*seg)))
                        if math.dist(actual,goal)<1.:
                            visits[key] = goal
                coverage = float(mission.belief.observed.mean())
                if t80 is None and coverage>=.8:
                    t80 = t
                if t-metric_time>=1:
                    metric_time = t
                    observed = {name:info[1] for name,info in io.poses.items()}
                    for name,pose in observed.items():
                        if name in previous:
                            distances[name] += math.dist(pose[:2],previous[name][:2])
                        nav = io.navigation(name)
                        if nav and name.startswith('rover'):
                            track_errors.append(math.dist(nav[1][:2],pose[:2]))
                    previous = observed
                    states.write(json.dumps({'t_s':round(t,3),'coverage':coverage,'poses':observed,
                                             'tasks':{k:w.task for k,w in workers.items()},
                                             'navigation':{k:io.navigation(k) for k in homes}})+'\n')
                    states.flush()
                if inserted and 'rover_1' in io.poses:
                    x,y,*_ = io.poses['rover_1'][1]
                    min_distance = min(min_distance,math.hypot(max(abs(x-BLOCK_XY[0])-2.5,0),
                                                               max(abs(y-BLOCK_XY[1])-2.5,0)))
                if video and t-video_time>=2.:
                    video_time = t
                    video.draw(io,workers,t,coverage,last_event)
            if mission.completed:
                status = 'complete'
        except (Exception,KeyboardInterrupt) as exc:
            error = repr(exc)
            emit('trial_failed',error=error)
        finally:
            for _ in range(4):
                for name in homes:
                    io.command(name)
                time.sleep(.05)
            emit('zero_velocity_sent',agents=sorted(homes))
            if server.poll() is None:
                os.killpg(server.pid,signal.SIGINT)
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(server.pid,signal.SIGKILL)
                    server.wait()
            if video:
                video.close()
            event_file.close()
    returns = {name:math.dist(io.poses[name][1][:2],home) for name,home in homes.items()
               if name in io.poses}
    report.update(status=status,error=error,duration_s=t,coverage=float(mission.belief.observed.mean()),
                  t80_s=t80,initial_rmse_m=initial_rmse,
                  final_rmse_m=float(np.sqrt(np.mean((mission.belief.mean-(ref-origin))**2))),
                  depth_frames=sensor_frames,distance_m=distances,final_home_error_m=returns,
                  samples=sum(x.kind=='sample' and x.state=='done' for x in mission.tasks.values()),
                  inspections=sum(x.kind=='inspect' and x.state=='done' for x in mission.tasks.values()),
                  returns=sum(a.returned for a in mission.agents.values()),sites=len(mission.seen),
                  remaining_tasks=[k for k,v in mission.tasks.items() if v.state!='done'],
                  lease_expirations=mission.reassignments,rejected_confirmations=mission.rejected,
                  link_cut=mission.channel.cut,link_restored=mission.cut_finished,
                  link_recovery_s=mission.recovery_s,site_visit_error_m=completed_visits,
                  rover_goal_error_m=math.dist(io.poses['rover_1'][1][:2],(46.,-2.))
                  if args.pilot==1 and 'rover_1' in io.poses else None,
                  odometry_outage_drift_m=math.dist(odom_loss_start,odom_loss_end)
                  if odom_loss_start is not None and odom_loss_end is not None else None,
                  route_tracking_rmse_m=float(np.sqrt(np.mean(np.square(path_errors)))) if path_errors else None,
                  obstacle_contact_reports=io.obstacle_contacts,
                  min_obstacle_center_clearance_m=min_distance if math.isfinite(min_distance) else None,
                  wheel_odometry_vs_pose_rmse_m=float(np.sqrt(np.mean(np.square(track_errors)))) if track_errors else None,
                  video_frames=video.frames if video else 0)
    if status=='complete':
        if args.pilot==1:
            accepted = report['rover_goal_error_m']<=2 and (
                not args.obstacle or (mission.blocked.any() and io.obstacle_contacts==0 and min_distance>=.9))
            if args.drop_odom:
                accepted = accepted and report['odometry_outage_drift_m'] is not None and report['odometry_outage_drift_m']<.2
        else:
            accepted = report['returns']==6 and max(returns.values())<=2 and (
                len(completed_visits)==8 and max(completed_visits.values())<=2)
        if not accepted:
            report['status'] = 'verification_failed'
    (out/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,indent=2))
    return 1 if status=='failed' else 0


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pilot',type=int,choices=[1,2,3,4],required=True)
    p.add_argument('--zone',choices=['center','east','west'],default='center')
    p.add_argument('--layout',type=int,choices=[0,1],default=0)
    p.add_argument('--seed',type=int,default=7)
    p.add_argument('--policy',choices=['information_hungarian','nearest_greedy'],default='information_hungarian')
    p.add_argument('--link',choices=['ideal','delay','loss','cut'],default='ideal')
    p.add_argument('--obstacle',action='store_true')
    p.add_argument('--smoke',action='store_true')
    p.add_argument('--drop-odom',action='store_true')
    p.add_argument('--video',action='store_true')
    p.add_argument('--max-time',type=float,default=1200.)
    p.add_argument('--rate',type=float,default=7.)
    p.add_argument('--out',default=str(BASE/'trial'))
    raise SystemExit(trial(p.parse_args()))
