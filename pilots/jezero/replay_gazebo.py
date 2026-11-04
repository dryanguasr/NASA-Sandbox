"""Play a completed mission in Gazebo. Pose replay is NOT closed-loop control.

Start the exported world with `gz sim -r` in the same GZ_PARTITION first.
Run with system Python containing gz.transport13 and gz.msgs10 bindings.
"""
from pathlib import Path
import argparse
import json
import math
import time


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trajectory',default='evidence/jezero/trajectory.jsonl')
    p.add_argument('--speed',type=float,default=40,help='Mission seconds per real second')
    p.add_argument('--hz',type=float,default=10)
    p.add_argument('--world',default='jezero_mission_replay')
    a=p.parse_args()
    if a.speed<=0 or a.hz<=0:p.error('speed and hz must be positive')
    try:
        from gz.transport13 import Node
        from gz.msgs10.pose_v_pb2 import Pose_V
        from gz.msgs10.boolean_pb2 import Boolean
    except ImportError as e:
        raise SystemExit('Install python3-gz-transport13 and python3-gz-msgs10; use /usr/bin/python3') from e
    frames=[json.loads(line) for line in Path(a.trajectory).read_text().splitlines()]
    if len(frames)<2:raise SystemExit('At least two trajectory frames are required')
    node=Node();service=f'/world/{a.world}/set_pose_vector'
    start=time.monotonic();i=0;sent=0
    while True:
        t=min(frames[-1]['time_s'],(time.monotonic()-start)*a.speed)
        while i<len(frames)-2 and frames[i+1]['time_s']<t:i+=1
        lo,hi=frames[i],frames[i+1]
        f=max(0,min(1,(t-lo['time_s'])/(hi['time_s']-lo['time_s'])))
        req=Pose_V()
        for aid,left in lo['positions'].items():
            right=hi['positions'][aid];pose=req.pose.add();pose.name=aid
            xyz=[left[k]+f*(right[k]-left[k]) for k in range(3)]
            pose.position.x,pose.position.y,pose.position.z=xyz
            delta=math.atan2(math.sin(right[3]-left[3]),math.cos(right[3]-left[3]))
            yaw=left[3]+f*delta;pose.orientation.w=math.cos(yaw/2);pose.orientation.z=math.sin(yaw/2)
        ok,response=node.request(service,req,Pose_V,Boolean,2000)
        if not ok or not response.data:
            raise SystemExit('Pose service failed. Check running world, -r, GZ_PARTITION and model names.')
        sent+=1
        if t>=frames[-1]['time_s']:break
        time.sleep(1/a.hz)
    print(json.dumps({'status':'replay_completed','pose_vectors':sent,'mission_seconds':t,
                      'note':'Visualization only; no dynamics or closed-loop validation.'}))


if __name__=='__main__':main()
