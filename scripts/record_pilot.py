#!/usr/bin/env python3
"""Run P0-P2 in Gazebo Harmonic and record actual sensor frames (Linux).

Requires python3-gz-transport13, python3-gz-msgs10 and ffmpeg.
Creates a separate observation world; never replaces the canonical world.
"""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

from gz.transport13 import Node
from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.image_pb2 import Image
from gz.msgs10.odometry_pb2 import Odometry
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.twist_pb2 import Twist

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence'
IDS = ['human_1', 'human_2', 'rover_1', 'rover_2', 'drone_1', 'drone_2']


def main():
    OUT.mkdir(exist_ok=True)
    for script in ['generate_terrain.py', 'validate_scene.py']:
        subprocess.run(['python3', str(ROOT/'scripts'/script)] +
                       (['--check'] if script.startswith('generate') else []), check=True)
    tree = ET.parse(ROOT/'worlds/mars_sandbox.sdf')
    world = tree.getroot().find('world')
    for name, pose, fov in [('overview', '-48 -58 48 0 .61 .88', '1.30'),
                             ('agents', '-22 -24 12 0 .49 .88', '1.25')]:
        model = ET.SubElement(world, 'model', name='observer_'+name)
        ET.SubElement(model, 'static').text = 'true'
        ET.SubElement(model, 'pose').text = pose
        link = ET.SubElement(model, 'link', name='camera_link')
        sensor = ET.SubElement(link, 'sensor', name=name, type='camera')
        ET.SubElement(sensor, 'always_on').text = 'true'
        ET.SubElement(sensor, 'update_rate').text = '10'
        ET.SubElement(sensor, 'topic').text = '/pilot/'+name
        camera = ET.SubElement(sensor, 'camera')
        ET.SubElement(camera, 'horizontal_fov').text = fov
        image = ET.SubElement(camera, 'image')
        ET.SubElement(image, 'width').text = '1280'
        ET.SubElement(image, 'height').text = '720'
        ET.SubElement(image, 'format').text = 'R8G8B8'
        clip = ET.SubElement(camera, 'clip')
        ET.SubElement(clip, 'near').text = '.1'
        ET.SubElement(clip, 'far').text = '180'
    observation = ROOT/'worlds/mars_pilot_observation.sdf'
    tree.write(observation, encoding='utf-8', xml_declaration=True)
    env = dict(os.environ, GZ_SIM_RESOURCE_PATH=str(ROOT/'models'),
               LIBGL_ALWAYS_SOFTWARE='1', GZ_PARTITION='nasa_sandbox_pilot')
    os.environ['GZ_PARTITION'] = env['GZ_PARTITION']
    node = Node()
    state = {'sim': 0., 'pose': {}, 'odom': {}, 'frames': {}, 'phase': 'startup',
             'onboard_frames': {}}
    encoders = {}
    trajectory = open(OUT/'trajectory.jsonl', 'w')
    last_pose = [-1.]

    def clock(msg):
        state['sim'] = msg.sim.sec + msg.sim.nsec/1e9

    def poses(msg):
        for p in msg.pose:
            if p.name in IDS:
                state['pose'][p.name] = [p.position.x,p.position.y,p.position.z]
        if state['sim'] - last_pose[0] >= .1:
            trajectory.write(json.dumps({'sim': state['sim'], 'phase': state['phase'],
                                         'positions': state['pose']})+'\n')
            last_pose[0] = state['sim']

    def odometry(name, msg):
        p = msg.pose.position
        state['odom'][name] = [p.x,p.y,p.z]

    def frame(name, msg):
        if name not in encoders:
            encoders[name] = subprocess.Popen([
                'ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo',
                '-pixel_format', 'rgb24', '-video_size', f'{msg.width}x{msg.height}',
                '-framerate', '10', '-i', '-', '-an', '-c:v', 'libx264',
                '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', str(OUT/(name+'.mp4'))], stdin=subprocess.PIPE)
            subprocess.run(['ffmpeg','-y','-loglevel','error','-f','rawvideo',
                            '-pixel_format','rgb24','-video_size',f'{msg.width}x{msg.height}',
                            '-i','-','-frames:v','1',str(OUT/(name+'.png'))], input=msg.data, check=True)
        encoders[name].stdin.write(msg.data)
        state['frames'][name] = state['frames'].get(name,0)+1

    node.subscribe(Clock, '/world/mars_sandbox/clock', clock)
    node.subscribe(Pose_V, '/world/mars_sandbox/pose/info', poses)
    callbacks = []
    def onboard(name, msg):
        if name not in state['onboard_frames']:
            subprocess.run(['ffmpeg','-y','-loglevel','error','-f','rawvideo',
                            '-pixel_format','rgb24','-video_size',f'{msg.width}x{msg.height}',
                            '-i','-','-frames:v','1',str(OUT/(name+'_rgb.png'))], input=msg.data, check=True)
        state['onboard_frames'][name] = state['onboard_frames'].get(name,0)+1

    for name in ['rover_1','rover_2','drone_1','drone_2']:
        link = 'chassis' if name.startswith('rover') else 'body'
        topic = f'/world/mars_sandbox/model/{name}/link/{link}/sensor/front_rgb/image'
        callback = lambda msg, name=name: onboard(name,msg)
        callbacks.append(callback)
        node.subscribe(Image, topic, callback)
    for name in IDS:
        callback = lambda msg, name=name: odometry(name,msg)
        callbacks.append(callback)
        node.subscribe(Odometry, '/model/'+name+'/odometry', callback)
    for name in ['overview','agents']:
        callback = lambda msg, name=name: frame(name,msg)
        callbacks.append(callback)
        node.subscribe(Image, '/pilot/'+name, callback)
    publishers = {n: node.advertise('/model/'+n+'/cmd_vel', Twist) for n in IDS}
    commands = []

    def send(name, xyz=(0.,0.,0.), yaw=0.):
        msg = Twist()
        msg.linear.x,msg.linear.y,msg.linear.z = xyz
        msg.angular.z = yaw
        publishers[name].publish(msg)
        commands.append({'sim':state['sim'],'agent':name,'linear':xyz,'yaw':yaw})

    def wait_sim(seconds):
        target = state['sim']+seconds
        deadline = time.monotonic()+max(120,seconds*40)
        while state['sim'] < target:
            if server.poll() is not None:
                raise RuntimeError('Gazebo exited; inspect gazebo.log')
            if time.monotonic()>deadline:
                raise TimeoutError('Simulation clock stalled')
            time.sleep(.02)

    results = []
    simultaneous = {}
    log = open(OUT/'gazebo.log','w')
    server = subprocess.Popen(['gz','sim','-s','-r','--headless-rendering','-v','3',
                               str(observation)], env=env, stdout=log, stderr=subprocess.STDOUT,
                              start_new_session=True)
    try:
        deadline = time.monotonic()+180
        while not (len(state['pose'])==6 and len(state['odom'])==6 and
                   len(state['frames'])==2 and len(state['onboard_frames'])==4):
            if server.poll() is not None or time.monotonic()>deadline:
                raise RuntimeError('Missing six poses/odometry or camera frames')
            time.sleep(.2)
        wait_sim(2)
        (OUT/'topics.json').write_text(json.dumps(node.topic_list(),indent=2))
        for name in IDS:
            state['phase'] = 'individual_'+name
            before = list(state['pose'][name])
            send(name,(.18,0,0))
            wait_sim(2)
            send(name)
            wait_sim(1)
            after = list(state['pose'][name])
            distance = math.dist(before,after)
            results.append({'agent':name,'before':before,'after':after,
                            'distance_m':distance,'moved':distance>.05})
            print(json.dumps(results[-1]), flush=True)
        state['phase'] = 'simultaneous'
        combined_before = {k:list(v) for k,v in state['pose'].items()}
        for name in IDS:
            send(name, (.22,0,.07 if name.startswith('drone') else 0),
                 .025 if name.startswith('rover') else 0)
        wait_sim(12)
        simultaneous = {k:math.dist(v,state['pose'][k]) for k,v in combined_before.items()}
    finally:
        state['phase'] = 'stop'
        for name in IDS:
            send(name)
        try:
            wait_sim(2)
            before_stop = {k:list(v) for k,v in state['pose'].items()}
            wait_sim(1)
            stop_drift = {k:math.dist(v,state['pose'][k]) for k,v in before_stop.items()}
        except (RuntimeError,TimeoutError):
            stop_drift = {}
        os.killpg(server.pid, signal.SIGINT)
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(server.pid, signal.SIGKILL)
            server.wait()
        for encoder in encoders.values():
            encoder.stdin.close()
            encoder.wait(timeout=30)
        trajectory.close()
        log.close()
        (OUT/'commands.json').write_text(json.dumps(commands,indent=2))
        report = {'gazebo_version':subprocess.check_output(['gz','sim','--versions'],text=True).strip(),
                  'renderer':'Ogre2 / Mesa software (LIBGL_ALWAYS_SOFTWARE=1)',
                  'sim_seconds':state['sim'],'frames':state['frames'],
                  'onboard_frames':state['onboard_frames'],
                  'simultaneous_distance_m':simultaneous,
                  'individual':results,'stop_drift_m_over_1s':stop_drift,
                  'all_moved':len(results)==6 and all(r['moved'] for r in results),
                  'odometry_topics_received':sorted(state['odom'])}
        (OUT/'results.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2),flush=True)
    assert report['all_moved'], 'Individual motion verification failed'
    assert len(simultaneous)==6 and min(simultaneous.values())>1, 'Combined motion verification failed'
    assert len(stop_drift)==6 and max(stop_drift.values())<.05, 'Stop verification failed'


if __name__ == '__main__':
    main()
