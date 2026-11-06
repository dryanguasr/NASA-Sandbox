"""Record the Jezero replay with seven synchronized Gazebo cameras.

Run after run_all.py, using the system Python with Gazebo bindings and Pillow.
"""
import argparse
from bisect import bisect_right
import csv
import json
import math
import multiprocessing
import os
from pathlib import Path
import shutil
import signal
import subprocess
from threading import Condition
import time
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont
from gz.msgs10.image_pb2 import Image as GazeboImage
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.transport13 import Node

from replay_gazebo import replay

ROOT = Path(__file__).resolve().parents[2]
MISSION = ROOT / 'evidence/jezero'
OUT = ROOT / 'evidence/jezero_replay'
GENERATED = ROOT / 'generated/jezero'
WORLD = 'jezero_mission_replay'
SIZE, WIDTH, HEIGHT, FPS, SPEED = 928, 1920, 1080, 15, 40
CAMERA_WIDTH, CAMERA_HEIGHT = 456, 276
MAP_X, MAP_Y = 496, 68
CAMERA_Z, FOV = 560, 1.02
COLORS = {'drone': '#63dce9', 'rover': '#ffcc72', 'human': '#acf09d'}
KINDS = ('drone', 'rover', 'human')
NAMES = {'drone': 'Dron', 'rover': 'Rover', 'human': 'Humano'}
# Diagonal offset, target height above model origin, and maximum horizontal lag (m).
MOUNTS = {'drone': (4.6, 0.0, .85),
          'rover': (6.4, .55, .9),
          'human': (8.7, .93, 1.1)}
ISOMETRIC_PITCH = math.atan(1/math.sqrt(2))
ISOMETRIC_YAW = -3*math.pi/4
ISOMETRIC_FOV = .39
MODELS = GENERATED / 'observation_models'


def panel_origin(name):
    kind, index = name.split('_')
    return (12 if index=='1' else 1452), KINDS.index(kind)*360+12


def extract_panels():
    """Export the seven panels without changing frame count or timing."""
    panels = {'overview':(960,1080,480,0)}
    for kind in KINDS:
        for index in (1,2):
            name = f'{kind}_{index}'
            panels[name] = (CAMERA_WIDTH,336,*panel_origin(name))
    for name, crop in panels.items():
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(OUT/'jezero_multivista.mp4'),
                        '-vf','crop='+':'.join(map(str,crop)),'-an','-c:v','libx264',
                        '-threads','3','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
                        '-movflags','+faststart',str(OUT/f'jezero_{name}.mp4')],check=True)


def add_camera(link, name, width, height, fov, near, pose):
    sensor = ET.SubElement(link, 'sensor', name=name, type='camera')
    ET.SubElement(sensor, 'pose').text = pose
    ET.SubElement(sensor, 'always_on').text = 'true'
    ET.SubElement(sensor, 'update_rate').text = str(FPS)
    sensor.append(ET.fromstring(f'''<camera>
      <horizontal_fov>{fov}</horizontal_fov>
      <image><width>{width}</width><height>{height}</height><format>R8G8B8</format></image>
      <clip><near>{near}</near><far>1200</far></clip></camera>'''))
    return sensor


def camera_position(name, x, y, z):
    offset, target_z, _ = MOUNTS[name.split('_')[0]]
    return x+offset, y+offset, z+offset+target_z


def camera_world(initial_positions):
    shutil.copytree(GENERATED/'models', MODELS, dirs_exist_ok=True)
    for kind in MOUNTS:
        path = MODELS/f'replay_{kind}'/'model.sdf'
        model_tree = ET.parse(path)
        model = model_tree.getroot().find('model')
        for link in model.findall('link'):
            for sensor in link.findall('sensor'):
                link.remove(sensor)
        model_tree.write(path, encoding='utf-8', xml_declaration=True)
    tree = ET.parse(GENERATED / 'jezero_mission.sdf')
    world = tree.getroot().find('world')
    physics = ET.SubElement(world,'physics',name='recording',type='ignored')
    ET.SubElement(physics,'max_step_size').text = '.02'
    ET.SubElement(physics,'real_time_factor').text = '1'
    ET.SubElement(world.find('light'), 'cast_shadows').text = 'true'
    for name, (x,y,z,_) in initial_positions.items():
        model = ET.SubElement(world,'model',name=f'camera_{name}')
        ET.SubElement(model,'static').text = 'true'
        position = ' '.join(map(str,camera_position(name,x,y,z)))
        ET.SubElement(model,'pose').text = f'{position} 0 {ISOMETRIC_PITCH} {ISOMETRIC_YAW}'
        link = ET.SubElement(model,'link',name='camera_link')
        sensor = add_camera(link,'replay_camera',CAMERA_WIDTH,CAMERA_HEIGHT,
                            ISOMETRIC_FOV,.05,'0 0 0 0 0 0')
        ET.SubElement(sensor,'topic').text = f'/jezero/{name}'
    model = ET.SubElement(world, 'model', name='observer')
    ET.SubElement(model, 'static').text = 'true'
    ET.SubElement(model, 'pose').text = f'0 0 {CAMERA_Z} 0 {math.pi/2} {math.pi/2}'
    link = ET.SubElement(model, 'link', name='camera_link')
    sensor = add_camera(link, 'overview', SIZE, SIZE, FOV, 1, '0 0 0 0 0 0')
    ET.SubElement(sensor, 'topic').text = '/jezero/overview'
    path = GENERATED / 'jezero_observation.sdf'
    tree.write(path, encoding='utf-8', xml_declaration=True)
    return path


def pixel(x, y, z=0):
    scale = SIZE / (2 * math.tan(FOV/2) * (CAMERA_Z-z))
    return round(MAP_X + SIZE/2 + x*scale), round(MAP_Y + SIZE/2 - y*scale)


def drive(trajectory, connection):
    # Keep synchronous service calls in a process separate from Python subscribers.
    centers = {}

    def add_camera_poses(request):
        for agent in list(request.pose):
            x,y,z = agent.position.x,agent.position.y,agent.position.z
            previous_x,previous_y = centers.get(agent.name,(x,y))
            # A fixed world bearing shows turns; bounded lag shows translation in the frame.
            dx,dy = .8*(x-previous_x),.8*(y-previous_y)
            max_lag = MOUNTS[agent.name.split('_')[0]][2]
            scale = max(1.,math.hypot(dx,dy)/max_lag)
            center_x,center_y = x-dx/scale,y-dy/scale
            centers[agent.name] = center_x,center_y
            pose = request.pose.add()
            pose.name = f'camera_{agent.name}'
            pose.position.x,pose.position.y,pose.position.z = camera_position(agent.name,center_x,center_y,z)
            cp,sp = math.cos(ISOMETRIC_PITCH/2),math.sin(ISOMETRIC_PITCH/2)
            cy,sy = math.cos(ISOMETRIC_YAW/2),math.sin(ISOMETRIC_YAW/2)
            pose.orientation.w,pose.orientation.x = cp*cy,-sp*sy
            pose.orientation.y,pose.orientation.z = sp*cy,cp*sy

    def acknowledge(t, request):
        expected = {p.name:(p.position.x,p.position.y,p.position.z) for p in request.pose
                    if not p.name.startswith('camera_')}
        connection.send(('frame',t,expected))
        connection.recv()

    try:
        result = replay(trajectory,SPEED,FPS,WORLD,acknowledge,
                        terrain=GENERATED/'models/jezero_terrain/meshes/terrain.obj',
                        add_camera_poses=add_camera_poses)
        connection.send(('result',result))
    except (Exception,SystemExit) as error:
        connection.send(('error',str(error)))
    finally:
        connection.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    trajectory = MISSION / 'trajectory.jsonl'
    rows = [json.loads(line) for line in trajectory.read_text().splitlines()]
    ids = list(rows[0]['positions'])
    times = [row['time_s'] for row in rows]
    trails = {name: [] for name in ids}
    with (MISSION/'metrics.csv').open() as stream:
        metrics = list(csv.DictReader(stream))
    metric_times = [float(row['time_s']) for row in metrics]
    events = [json.loads(line) for line in (MISSION/'events.jsonl').read_text().splitlines()]
    sites = {e['site']: e for e in events if e['event']=='site_detected'}
    returns = {e['agent']: e['time_s'] for e in events
               if e['event']=='completed' and e['kind']=='return'}
    fonts = {size: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
             for size in (17,20,23,28,33)}
    world = camera_world(rows[0]['positions'])
    os.environ['GZ_PARTITION'] = f'jezero_record_{os.getpid()}'
    env = dict(os.environ, LIBGL_ALWAYS_SOFTWARE='1',
               GZ_SIM_RESOURCE_PATH=str(MODELS))
    node = Node()
    condition = Condition()
    pending = {}
    latest = {'stamp': -1, 'frames': {}, 'poses': {}, 'images': 0}
    camera_ids = {'overview', *ids}

    def receive_image(name, msg):
        width,height = (SIZE,SIZE) if name=='overview' else (CAMERA_WIDTH,CAMERA_HEIGHT)
        if (msg.width,msg.height,msg.step) != (width,height,width*3):
            return
        stamp = msg.header.stamp.sec*10**9 + msg.header.stamp.nsec
        with condition:
            if stamp <= latest['stamp']:
                return
            frames = pending.setdefault(stamp,{})
            frames[name] = bytes(msg.data)
            if frames.keys() == camera_ids:
                latest.update(stamp=stamp,frames=frames,images=latest['images']+1)
                for old in list(pending):
                    if old <= stamp:
                        del pending[old]
                condition.notify_all()
            for old in sorted(pending)[:-12]:
                del pending[old]

    def receive_poses(msg):
        poses = {p.name:(p.position.x,p.position.y,p.position.z)
                 for p in msg.pose if p.name in ids}
        if len(poses) == len(ids):
            latest['poses'] = poses

    callbacks = []
    for name in camera_ids:
        topic = f'/jezero/{name}'
        callback = lambda msg, name=name: receive_image(name,msg)
        callbacks.append(callback)
        node.subscribe(GazeboImage,topic,callback)
    node.subscribe(Pose_V, f'/world/{WORLD}/pose/info', receive_poses)
    command = ['gz','sim','-s','-r','--headless-rendering','-v','3',str(world.relative_to(ROOT))]
    count = 0
    max_pose_error = 0.
    encoder = None
    driver = None
    with (OUT/'multivista-gazebo.log').open('w') as log, (OUT/'multivista-poses.jsonl').open('w') as trace:
        server = subprocess.Popen(command, env=env, cwd=ROOT, stdout=log,
                                  stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic()+80
            while not latest['frames'] or len(latest['poses']) != len(ids):
                if server.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError(f'Camera set or poses unavailable. Pending cameras: '
                                       f'{[sorted(group) for group in pending.values()]}')
                time.sleep(.05)
            encoder = subprocess.Popen([
                'ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24',
                '-video_size',f'{WIDTH}x{HEIGHT}','-framerate',str(FPS),'-i','-',
                '-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',
                '-movflags','+faststart',str(OUT/'jezero_multivista.mp4')],stdin=subprocess.PIPE)

            def capture(t, expected):
                nonlocal count, max_pose_error
                deadline = time.monotonic()+2
                while True:
                    observed = latest['poses']
                    error = max(math.dist(observed[name],point) for name,point in expected.items())
                    if error < .01:
                        break
                    if server.poll() is not None or time.monotonic()>deadline:
                        raise RuntimeError(f'Pose error {error:.3f} m at mission t={t:.1f} s')
                    time.sleep(.004)
                max_pose_error = max(max_pose_error,error)
                with condition:
                    cutoff = latest['stamp']
                    if not condition.wait_for(lambda: latest['stamp'] > cutoff,timeout=8):
                        raise TimeoutError(f'No synchronized camera set after mission t={t:.1f} s')
                    stamp, frames = latest['stamp'],latest['frames']
                trace.write(json.dumps({'time_s':t,'positions':observed,'max_error_m':error,
                                        'camera_stamp_ns':stamp})+'\n')
                frame = Image.new('RGB',(WIDTH,HEIGHT),'#111923')
                frame.paste(Image.frombytes('RGB',(SIZE,SIZE),frames['overview']),(MAP_X,MAP_Y))
                draw = ImageDraw.Draw(frame)

                def label(x,y,value,size=20,color='#edf1f7'):
                    draw.text((x,y),value,font=fonts[size],fill=color)

                draw.rounded_rectangle((510,82,724,120),radius=7,fill='#111923')
                label(524,90,'↑ N   ·   VISTA CENITAL',17)
                scale = pixel(50,0)[0]-pixel(-50,0)[0]
                draw.rectangle((510,935,536+scale,980),fill='#111923')
                draw.line((522,969,522+scale,969),fill='white',width=3)
                label(522,940,'100 m aprox.',17)
                for name, event in sites.items():
                    if event['time_s'] <= t:
                        x,y = pixel(*event['xy_m'])
                        draw.rectangle((x-5,y-5,x+5,y+5),outline='#f8f0e5',width=2)
                        label(x+9,y-9,name,17)
                for name, xyz in observed.items():
                    x,y = pixel(*xyz)
                    color = COLORS[name.split('_')[0]]
                    trail = trails[name]
                    trail.append((x,y))
                    if len(trail)>1:
                        draw.line(trail[-34:],fill=color,width=2)
                    draw.ellipse((x-11,y-11,x+11,y+11),fill=color,outline='#111923',width=2)
                    draw.text((x,y),name[-1],font=fonts[17],fill='#111923',anchor='mm')
                metric = metrics[max(0,bisect_right(metric_times,t)-1)]
                mission = rows[max(0,bisect_right(times,t)-1)]
                label(496,16,'JEZERO  /  NASA SANDBOX',33,'#ffcc72')
                label(995,24,f'Misión {int(t)//60:02d}:{int(t)%60:02d}  ·  {SPEED}×  ·  512 × 512 m',23)
                label(496,1005,f"Cobertura {float(metric['coverage']):.1%}    ·    Muestras {metric['completed_samples']}/4    ·    Error {float(metric['rmse_m']):.2f} m RMSE",23)
                label(496,1042,'USGS / MRO  ·  Reproducción cinemática en Gazebo  ·  Métricas de misión 2.5D',20,'#bec9d6')
                for name in ids:
                    kind, index = name.split('_')
                    color = COLORS[kind]
                    x,y = panel_origin(name)
                    draw.rounded_rectangle((x,y,x+456,y+336),radius=8,fill='#1c2734')
                    frame.paste(Image.frombytes('RGB',(CAMERA_WIDTH,CAMERA_HEIGHT),frames[name]),(x,y+35))
                    label(x+12,y+3,f'{NAMES[kind]} {index}',23,color)
                    label(x+240,y+7,'VISTA ISOMÉTRICA',17,'#bec9d6')
                    task = mission['tasks'][name]
                    if task is None:
                        task_label = 'En base' if t >= returns[name] else 'En espera'
                    else:
                        action, target = task.split(':',1)
                        task_label = {'survey':'Reconocimiento','inspect':'Inspección',
                                      'sample':'Muestreo','return':'Regreso'}[action]
                        if action != 'return':
                            task_label += '  '+target
                    label(x+12,y+312,task_label,17,color)
                if times[-1]/2 <= t < times[-1]/2+SPEED/FPS:
                    frame.save(OUT/'multivista-preview.png')
                repetitions = 30 if count==0 or t>=times[-1] else 1
                raw = frame.tobytes()
                for _ in range(repetitions):
                    encoder.stdin.write(raw)
                count += repetitions

            context = multiprocessing.get_context('spawn')
            parent, child = context.Pipe()
            driver = context.Process(target=drive,args=(trajectory,child))
            driver.start()
            child.close()
            with parent:
                while parent.poll(30):
                    kind, *payload = parent.recv()
                    if kind == 'result':
                        result = payload[0]
                        break
                    if kind == 'error':
                        raise RuntimeError(payload[0])
                    capture(*payload)
                    parent.send(True)
                else:
                    raise TimeoutError('The Gazebo replay worker stopped responding')
        finally:
            if driver is not None:
                driver.join(timeout=2)
                if driver.is_alive():
                    driver.terminate()
                    driver.join()
            if server.poll() is None:
                os.killpg(server.pid,signal.SIGINT)
                try:
                    server.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(server.pid,signal.SIGKILL)
                    server.wait()
            if encoder is not None:
                encoder.stdin.close()
                if encoder.wait(timeout=30):
                    raise RuntimeError('FFmpeg encoding failed')
    result.update({'command':command,'gazebo':subprocess.check_output(['gz','sim','--versions'],text=True).strip(),
                   'max_pose_error_m':max_pose_error,'synchronized_camera_sets':latest['images'],
                   'cameras':sorted(camera_ids),
                   'video_frames':count,'fps':FPS,'speed':SPEED})
    (OUT/'multivista.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract-only',action='store_true',help='Extract panels from the existing montage')
    args = parser.parse_args()
    if not args.extract_only:
        main()
    extract_panels()
