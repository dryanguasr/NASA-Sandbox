"""Build live Gazebo worlds from checksum-verified orbital crops."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np

from export_gazebo import ROOT, export, text, write_xml
from mission import Grid, load_data
from replay_gazebo import terrain_height
from extension_cases import FOV_GROUND, belva_fixture, fixtures

BASE = ROOT / 'generated/closed_loop'
DATA = ROOT / 'data/jezero'
KINDS = {'drone': 'scout_drone', 'rover': 'scout_rover', 'human': 'astronaut'}
IDS = [f'{kind}_{i}' for kind in KINDS for i in (1, 2)]
HOME = dict(zip(IDS, [(-50,-46),(-42,-46),(-50,-42),(-42,-42),(-50,-50),(-42,-50)]))
LAYOUTS = [[(-26,-14),(22,-22),(26,22),(-22,26)], [(-30,22),(26,-30),(18,26),(-18,-22)]]
SITE_COLORS = [(0,1,0),(0,0,1),(1,0,1),(0,1,1)]
FOV = 1.45
SENSOR_SIZE = 80
BLOCK_XY = (-18,-2)
P1_HOME = {'drone_1':(-50,-2), 'rover_1':(-50,-2)}


def control_topic(name):
    return f'/live/{name}/cmd_vel'


def prepare(zone):
    folder = BASE/'data'/zone
    if (folder/'terrain.npz').exists():
        load_data(folder)
        return folder
    folder.mkdir(parents=True,exist_ok=True)
    ref,prior,valid,meta = load_data(DATA)
    packaged = ROOT/'data/jezero_live'/zone
    if (packaged/'terrain.npz').is_file():
        load_data(packaged)
        for name in ('terrain.npz','metadata.json'):
            shutil.copyfile(packaged/name,folder/name)
    elif zone=='center':
        start = (len(ref)-32)//2
        sl = np.s_[start:start+32,start:start+32]
        np.savez_compressed(folder/'terrain.npz', reference=ref[sl],prior=prior[sl],valid=valid[sl])
        meta.update(shape=[32,32],side_m=128.,affine_gdal=[-64.,4.,0.,64.,0.,-4.],
                    parent_terrain_sha256=meta['terrain_sha256'])
        meta['terrain_sha256'] = hashlib.sha256((folder/'terrain.npz').read_bytes()).hexdigest()
        (folder/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    elif zone=='belva':
        raise ValueError('Belva requires the verified orbital crop in data/jezero_live/belva')
    else:
        sign = 1 if zone=='east' else -1
        failures = []
        for offset in (.010,.006):
            lon = meta['center_lon_east_deg']+sign*offset
            attempt = folder/f'attempt_{offset}'
            result = subprocess.run([sys.executable,str(Path(__file__).with_name('import_data.py')),
                                     '--out',str(attempt),'--lon',str(lon),'--side-m','128'],
                                    capture_output=True,text=True,timeout=180)
            (folder/f'import_{offset}.log').write_text(result.stdout+result.stderr)
            try:
                if result.returncode:
                    raise ValueError(f'import exit {result.returncode}')
                load_data(attempt)
            except (ValueError,OSError) as exc:
                failures.append(str(exc))
                continue
            for name in ('metadata.json','terrain.npz','reference.tif','prior.tif'):
                shutil.copyfile(attempt/name,folder/name)
            break
        else:
            raise RuntimeError(f'{zone}: no verified crop ({failures})')
    load_data(folder)
    return folder


def sensor(link, name, kind, topic, pose, width, height, fov, hz=2, mask=None):
    item = ET.SubElement(link,'sensor',name=name,type=kind)
    text(item,'pose',pose)
    text(item,'topic',topic)
    text(item,'always_on','true')
    text(item,'update_rate',hz)
    cam = ET.SubElement(item,'camera')
    text(cam,'horizontal_fov',fov)
    image = ET.SubElement(cam,'image')
    text(image,'width',width)
    text(image,'height',height)
    if kind=='camera':
        text(image,'format','R8G8B8')
    clip = ET.SubElement(cam,'clip')
    text(clip,'near',.1)
    text(clip,'far',140)
    if mask is not None:
        text(cam,'visibility_mask',mask)


def box(name, xyz, size, rgb, collision):
    model = ET.Element('model',name=name)
    text(model,'static','true')
    text(model,'pose',' '.join(map(str,xyz))+' 0 0 0')
    link = ET.SubElement(model,'link',name='box')
    for kind in ('visual','collision') if collision else ('visual',):
        obj = ET.SubElement(link,kind,name=kind)
        geom = ET.SubElement(ET.SubElement(obj,'geometry'),'box')
        text(geom,'size',' '.join(map(str,size)))
        if kind=='visual':
            material = ET.SubElement(obj,'material')
            color = ' '.join(map(str,rgb))+' 1'
            text(material,'diffuse',color)
            text(material,'emissive',color)
    return model


def add_video_grid(terrain_path, ground):
    """World-fixed 4 m grid, visible only to side recording cameras."""
    tree = ET.parse(terrain_path)
    link = tree.find('model/link')
    visual = ET.SubElement(link,'visual',name='video_grid')
    text(visual,'visibility_flags',2)
    text(visual,'cast_shadows','false')
    geom = ET.SubElement(ET.SubElement(visual,'geometry'),'mesh')
    text(geom,'uri','model://jezero_terrain/meshes/video_grid.obj')
    material = ET.SubElement(visual,'material')
    text(material,'ambient','.37 .22 .14 1')
    text(material,'diffuse','.55 .33 .20 1')
    with (terrain_path.parent/'meshes/video_grid.obj').open('w') as stream:
        stream.write('o video_grid\nvn 0 0 1\n')
        index = 1
        for axis in (0,1):
            for fixed in range(-58,59,4):
                for along in range(-62,62,4):
                    vertices = [(fixed+edge,along+step) if axis==0 else (along+step,fixed+edge)
                                for step in (0,4) for edge in (-.045,.045)]
                    for x,y in vertices:
                        stream.write(f'v {x:.4f} {y:.4f} {ground(x,y)+.025:.5f}\n')
                    for face in ((0,1,2),(1,3,2)) if axis==0 else ((0,2,1),(1,2,3)):
                        stream.write('f '+' '.join(f'{index+i}//1' for i in face)+'\n')
                    index += 4
    write_xml(tree.getroot(),terrain_path)


def differential_variant(model):
    """Two centered drive wheels and a passive rear caster for reliable turns."""
    for tag,name in (('link','wheel_bl'),('link','wheel_br'),('joint','joint_bl'),('joint','joint_br')):
        model.remove(model.find(f"{tag}[@name='{name}']"))
    for name,y in (('wheel_fl',.42),('wheel_fr',-.42)):
        wheel = model.find(f"link[@name='{name}']")
        wheel.find('pose').text = f'0 {y} .28 -1.5707963 0 0'
        for radius in wheel.findall('.//cylinder/radius'):
            radius.text = '.28'
    drive = model.find('plugin')
    for tag in ('left_joint','right_joint'):
        drive.remove(drive.findall(tag)[1])
    drive.find('wheel_radius').text = '.28'
    chassis = model.find('link')
    chassis.find('pose').text = '0 0 .49 0 0 0'
    text(chassis.find('inertial'),'pose','-.12 0 0 0 0 0')
    for index,x in enumerate((-.51,)):
        for kind in ('visual','collision'):
            item = ET.SubElement(chassis,kind,name=f'caster_{index}_{kind}')
            text(item,'pose',f'{x} 0 -.36 0 0 0')
            geom = ET.SubElement(ET.SubElement(item,'geometry'),'sphere')
            text(geom,'radius','.10')
            if kind=='collision':
                ode = ET.SubElement(ET.SubElement(ET.SubElement(item,'surface'),'friction'),'ode')
                text(ode,'mu','.025')
                text(ode,'mu2','.025')


def build(data,out,pilot,layout,video,rate,scenario=None):
    ref,prior,_,meta = load_data(data)
    grid = Grid(len(ref),meta['cell_m'])
    assert grid.n==32 and grid.cell==4
    out.mkdir(parents=True,exist_ok=True)
    home = P1_HOME if pilot==1 else HOME
    if pilot==7:
        home = belva_fixture()['homes']
    if pilot==6:
        # Park the second rover off the eastbound ground-scout corridor.
        home = {**home,'rover_2':(-42,-34)}
    poses = {name:[*xy,0,0] for name,xy in home.items()}
    trajectory = out/'spawn.jsonl'
    trajectory.write_text(json.dumps({'positions':poses})+'\n')
    export(data,out,trajectory)
    ground = terrain_height(out/'models/jezero_terrain/meshes/terrain.obj')
    root = ET.parse(out/'jezero_mission.sdf').getroot()
    world = root.find('world')
    world.set('name','jezero_live')
    physics = ET.SubElement(world,'physics',name='live',type='ignored')
    text(physics,'max_step_size','.01')
    text(physics,'real_time_factor',rate)
    ET.SubElement(world,'plugin',filename='gz-sim-imu-system',name='gz::sim::systems::Imu')
    altitude = float(np.max(prior)-meta['origin_z_m']+23.)
    for inc in world.findall('include')[1:]:
        name = inc.findtext('name')
        kind = name.split('_')[0]
        x,y = home[name]
        z = altitude if kind=='drone' else ground(x,y)+.035
        inc.find('pose').text = f'{x} {y} {z} 0 0 0'
        tree = ET.parse(ROOT/'models'/KINDS[kind]/'model.sdf')
        model = tree.getroot().find('model')
        model.set('name',name)
        drive = model.find('plugin')
        text(drive,'topic',control_topic(name))
        if kind=='rover':
            differential_variant(model)
        for link in model.findall('link'):
            for old in link.findall('sensor'):
                link.remove(old)
        link = model.find('link')
        if kind=='rover':
            imu = ET.SubElement(link,'sensor',name='heading',type='imu')
            text(imu,'topic',f'/live/{name}/imu')
            text(imu,'always_on','true')
            text(imu,'update_rate',30)
        if kind=='drone':
            for k in ('depth_camera','camera'):
                sensor(link,k,k,f'/live/{name}/{k}','0 0 -.25 0 1.570796326795 0',
                       SENSOR_SIZE,SENSOR_SIZE,FOV,mask=1)
        if pilot==6 and kind!='drone':
            camera_z = .86 if kind=='rover' else 1.62
            camera_x = .67 if kind=='rover' else .35
            for k in ('depth_camera','camera'):
                sensor(link,k,k,f'/live/{name}/{k}',f'{camera_x} 0 {camera_z} 0 .12 0',
                       SENSOR_SIZE,SENSOR_SIZE,FOV_GROUND,mask=1)
        if video:
            offset,target = {'drone':(5.,0.),'rover':(7.,.18),'human':(8.5,.93)}[kind]
            pitch = np.arctan(1/np.sqrt(2))
            sensor(link,'side','camera',f'/live/{name}/side',
                   f'{offset} {offset} {offset+target} 0 {pitch} {-3*np.pi/4}',
                   288,168,.48,mask=3)
        folder = out/'models'/f'replay_{kind}'
        # Each include needs its own topic names.
        instance = out/'models'/name
        instance.mkdir(exist_ok=True)
        inc.find('uri').text = f'model://{name}'
        (instance/'model.config').write_bytes((folder/'model.config').read_bytes())
        write_xml(tree.getroot(),instance/'model.sdf')
    if pilot>=5:
        fixtures(world,out,pilot,scenario,ground,box)
    elif pilot!=1:
        for index,((x,y),rgb) in enumerate(zip(LAYOUTS[layout],SITE_COLORS),1):
            world.append(box(f'fictional_site_{index}',(x,y,ground(x,y)+.4),(2.3,2.3,.8),rgb,False))
    else:
        x,y = BLOCK_XY
        obstacle = box('injected_obstacle',(x,y,ground(x,y)+1.5),(5,5,3),(1,0,0),True)
        contact = ET.SubElement(obstacle.find('link'),'sensor',name='contacts',type='contact')
        text(contact,'topic','/live/obstacle/contacts')
        text(contact,'always_on','true')
        text(ET.SubElement(contact,'contact'),'collision','collision')
        ET.SubElement(world,'plugin',filename='gz-sim-contact-system',name='gz::sim::systems::Contact')
        (out/'obstacle.sdf').write_text('<sdf version="1.10">'+ET.tostring(obstacle,encoding='unicode')+'</sdf>')
    if video:
        add_video_grid(out/'models/jezero_terrain/model.sdf',ground)
        model = ET.SubElement(world,'model',name='overview')
        text(model,'static','true')
        text(model,'pose','0 0 102 0 1.570796326795 1.570796326795')
        link = ET.SubElement(model,'link',name='camera')
        sensor(link,'overview','camera','/live/overview','0 0 0 0 0 0',576,576,1.24,mask=1)
    path = out/'live.sdf'
    write_xml(root,path)
    return path,home,altitude


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zones',nargs='+',choices=['center','east','west'])
    args = parser.parse_args()
    for zone in args.zones:
        print(prepare(zone),flush=True)
