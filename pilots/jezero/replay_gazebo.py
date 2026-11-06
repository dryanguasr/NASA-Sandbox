"""Play a completed mission in Gazebo. Pose replay is NOT closed-loop control.

Start the exported world with `gz sim -r` in the same GZ_PARTITION first.
Run with system Python containing gz.transport13 and gz.msgs10 bindings.
"""
from pathlib import Path
import argparse
import json
import math
import time


def terrain_height(path):
    """Read the regular, north-to-south mesh emitted by export_gazebo.py."""
    vertices = [tuple(map(float,line.split()[1:4]))
                for line in Path(path).read_text().splitlines() if line.startswith('v ')]
    n = math.isqrt(len(vertices))
    if n < 2 or n*n != len(vertices):
        raise ValueError('Expected a square Jezero terrain mesh')
    west,north,_ = vertices[0]
    cell = vertices[1][0]-west
    if cell <= 0 or vertices[n][1] >= north:
        raise ValueError('Expected eastward columns and southward rows')

    def height(x,y):
        c,r = (x-west)/cell,(north-y)/cell
        if not (0 <= c <= n-1 and 0 <= r <= n-1):
            raise ValueError(f'Replay pose outside the terrain mesh: {x}, {y}')
        col,row = min(int(c),n-2),min(int(r),n-2)
        u,v = c-col,r-row
        nw,ne = (vertices[row*n+col+i][2] for i in (0,1))
        sw,se = (vertices[(row+1)*n+col+i][2] for i in (0,1))
        if u+v <= 1:
            return nw+u*(ne-nw)+v*(sw-nw)
        return se+(1-u)*(sw-se)+(1-v)*(ne-se)
    return height


def replay(trajectory, speed, hz, world, on_pose=None, terrain=None):
    try:
        from gz.transport13 import Node
        from gz.msgs10.pose_v_pb2 import Pose_V
        from gz.msgs10.boolean_pb2 import Boolean
    except ImportError as e:
        raise SystemExit('Install python3-gz-transport13 and python3-gz-msgs10; use /usr/bin/python3') from e
    frames=[json.loads(line) for line in Path(trajectory).read_text().splitlines()]
    if len(frames)<2:raise SystemExit('At least two trajectory frames are required')
    height = terrain_height(terrain) if terrain is not None else None
    node = Node()
    service = f'/world/{world}/set_pose_vector/blocking'
    deadline = time.monotonic()+8
    while service not in node.service_list():
        if time.monotonic() >= deadline:
            raise SystemExit(f'{service} unavailable. Check running world and GZ_PARTITION.')
        time.sleep(.1)
    start=time.monotonic();i=0;sent=0
    while True:
        elapsed = sent/hz if on_pose is not None else time.monotonic()-start
        t = min(frames[-1]['time_s'],frames[0]['time_s']+elapsed*speed)
        while i<len(frames)-2 and frames[i+1]['time_s']<t:i+=1
        lo,hi=frames[i],frames[i+1]
        f=max(0,min(1,(t-lo['time_s'])/(hi['time_s']-lo['time_s'])))
        req=Pose_V()
        for aid,left in lo['positions'].items():
            right=hi['positions'][aid];pose=req.pose.add();pose.name=aid
            xyz=[left[k]+f*(right[k]-left[k]) for k in range(3)]
            if height is not None:
                # Retain the mission's nominal clearance over the rendered triangles.
                xyz[2] = height(*xyz[:2]) + (40 if aid.startswith('drone_') else .12)
            pose.position.x,pose.position.y,pose.position.z=xyz
            delta=math.atan2(math.sin(right[3]-left[3]),math.cos(right[3]-left[3]))
            yaw=left[3]+f*delta;pose.orientation.w=math.cos(yaw/2);pose.orientation.z=math.sin(yaw/2)
        ok,response=node.request(service,req,Pose_V,Boolean,5000)
        if not ok:
            # A timed-out pose command can safely be repeated before advancing the replay.
            ok,response=node.request(service,req,Pose_V,Boolean,5000)
        if not ok or not response.data:
            raise SystemExit(f'Pose service failed at t={t:.2f}s (transport={ok}, response={response!s}). Check -r and model names.')
        sent+=1
        if on_pose is not None:
            on_pose(t, req)
        if t>=frames[-1]['time_s']:break
        time.sleep(max(0, start+sent/hz-time.monotonic()))
    return {'status':'replay_completed','pose_vectors':sent,'mission_seconds':t,
            'note':'Visualization only; no dynamics or closed-loop validation.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trajectory',default='evidence/jezero/trajectory.jsonl')
    p.add_argument('--speed',type=float,default=40,help='Mission seconds per real second')
    p.add_argument('--hz',type=float,default=10)
    p.add_argument('--world',default='jezero_mission_replay')
    p.add_argument('--terrain',type=Path,default=Path('generated/jezero/models/jezero_terrain/meshes/terrain.obj'),
                   help='Exported mesh used to align replay heights with rendered triangles')
    a=p.parse_args()
    if not (math.isfinite(a.speed) and math.isfinite(a.hz) and a.speed>0 and a.hz>0):
        p.error('speed and hz must be positive and finite')
    terrain = a.terrain if a.terrain.is_file() else None
    if terrain is None:
        p.error(f'Terrain mesh not found: {a.terrain}. Run the exporter or specify --terrain.')
    print(json.dumps(replay(a.trajectory,a.speed,a.hz,a.world,terrain=terrain)))


if __name__=='__main__':main()
