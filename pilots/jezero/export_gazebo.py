"""Export actual DEM + six STATIC pose-driven agents for Gazebo replay only.

This is a visual bridge, not closed-loop autonomy or a dynamics validation.
Canonical Pilot 0 files are never modified.
"""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET
import numpy as np
from mission import Grid, load_data

ROOT=Path(__file__).resolve().parents[2]


def text(parent, name, value):
    node=ET.SubElement(parent,name);node.text=str(value);return node


def write_xml(root,path):
    ET.indent(root)
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)


def export(data,out,trajectory):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    ref,_,valid,meta=load_data(data);g=Grid(len(ref),meta['cell_m'])
    terrain=out/'models/jezero_terrain';(terrain/'meshes').mkdir(parents=True,exist_ok=True)
    vertices=np.array([[*g.xy((r,c)),float(ref[r,c]-meta['origin_z_m'])] for r in range(g.n) for c in range(g.n)])
    faces=[]
    for r in range(g.n-1):
        for c in range(g.n-1):
            a=r*g.n+c;b=a+1;cc=a+g.n;d=cc+1
            faces.extend([(a,cc,b),(b,cc,d)])
    with (terrain/'meshes/terrain.obj').open('w') as f:
        f.write('# Real USGS/MRO HiRISE crop; 4 m computational posts, no vertical exaggeration\no jezero\n')
        for v in vertices:f.write('v '+' '.join(f'{x:.7f}' for x in v)+'\n')
        for a,b,c in faces:
            normal=np.cross(vertices[b]-vertices[a],vertices[c]-vertices[a]);normal/=np.linalg.norm(normal)
            if normal[2]<=0:raise ValueError('Mesh normal must point up')
            f.write('vn '+' '.join(f'{x:.9f}' for x in normal)+'\n')
        for i,face in enumerate(faces,1):f.write('f '+' '.join(f'{v+1}//{i}' for v in face)+'\n')
    root=ET.Element('sdf',version='1.10');model=ET.SubElement(root,'model',name='jezero_terrain')
    text(model,'static','true');link=ET.SubElement(model,'link',name='ground')
    for kind in ['collision','visual']:
        obj=ET.SubElement(link,kind,name='terrain_'+kind);mesh=ET.SubElement(ET.SubElement(obj,'geometry'),'mesh')
        text(mesh,'uri','model://jezero_terrain/meshes/terrain.obj')
        if kind=='visual':
            mat=ET.SubElement(obj,'material');text(mat,'ambient','.45 .28 .18 1');text(mat,'diffuse','.65 .4 .24 1')
    write_xml(root,terrain/'model.sdf')
    for name in ['jezero_terrain','replay_human','replay_drone','replay_rover']:
        folder=out/'models'/name;folder.mkdir(parents=True,exist_ok=True)
        conf=ET.Element('model');text(conf,'name',name);text(conf,'version','1.0');sdf=text(conf,'sdf','model.sdf');sdf.set('version','1.10')
        text(conf,'description','Jezero mission replay; not a physics-validated agent.')
        write_xml(conf,folder/'model.config')
    for kind,old in [('human','astronaut'),('drone','scout_drone'),('rover','scout_rover')]:
        tree=ET.parse(ROOT/'models'/old/'model.sdf');m=tree.getroot().find('model');m.set('name','replay_'+kind)
        for plugin in list(m.findall('plugin')):m.remove(plugin)
        for old_static in list(m.findall('static')):m.remove(old_static)
        text(m,'static','true')
        # Static visual agents are moved with set_pose_vector. Do not use this world for contact tests.
        for l in m.findall('link'):
            for collision in list(l.findall('collision')):l.remove(collision)
        write_xml(tree.getroot(),out/'models'/('replay_'+kind)/'model.sdf')
    poses=json.loads(Path(trajectory).read_text().splitlines()[0])['positions']
    root=ET.Element('sdf',version='1.10');w=ET.SubElement(root,'world',name='jezero_mission_replay')
    text(w,'gravity','0 0 -3.71')
    for system,filename in [('Physics','physics'),('UserCommands','user-commands'),('SceneBroadcaster','scene-broadcaster'),('Sensors','sensors')]:
        plugin=ET.SubElement(w,'plugin',filename=f'gz-sim-{filename}-system',name='gz::sim::systems::'+system)
        if system=='Sensors':text(plugin,'render_engine','ogre2')
    scene=ET.SubElement(w,'scene');text(scene,'ambient','.55 .45 .35 1');text(scene,'background','.2 .15 .12 1')
    light=ET.SubElement(w,'light',type='directional',name='sun');text(light,'direction','-.4 .2 -.9');text(light,'diffuse','1 .85 .7 1')
    inc=ET.SubElement(w,'include');text(inc,'uri','model://jezero_terrain')
    for aid,pose in poses.items():
        kind=aid.split('_')[0]
        inc=ET.SubElement(w,'include');text(inc,'uri','model://replay_'+kind);text(inc,'name',aid)
        text(inc,'pose',f'{pose[0]} {pose[1]} {pose[2]} 0 0 {pose[3]}')
    write_xml(root,out/'jezero_mission.sdf')
    (out/'README.txt').write_text('REAL TOPOGRAPHY; STATIC AGENTS; KINEMATIC REPLAY ONLY.\nNo sensor reconstruction or closed-loop dynamics run is claimed.\n')
    (out/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(f'Gazebo replay exported: {out}; {len(vertices)} vertices, {len(faces)} triangles, six agents.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/jezero');p.add_argument('--out',default='generated/jezero')
    p.add_argument('--trajectory',default='evidence/jezero/trajectory.jsonl')
    a=p.parse_args();export(a.data,a.out,a.trajectory)


if __name__=='__main__':main()
