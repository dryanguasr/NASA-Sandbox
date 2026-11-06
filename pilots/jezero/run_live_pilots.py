"""Execute all planned trials in independent Gazebo partitions and preserve failures."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

from live_world import BASE, prepare

TRIAL = Path(__file__).with_name('live_trial.py')


def schedule(pilot):
    if pilot==1:
        return [
            ('clear', ['--video','--smoke']),
            ('obstacle', ['--video','--obstacle']),
            ('odom-outage', ['--drop-odom','--obstacle']),
        ]
    if pilot==2:
        return [('nominal',['--video','--smoke'])]
    if pilot==5:
        return [(case,['--zone','west','--scenario',case,'--video','--smoke'])
                for case in ('bypass','sealed')]
    if pilot==6:
        return [(case,['--scenario',case,'--video','--smoke'])
                for case in ('hidden','emergent','oracle')]
    if pilot==3:
        cases = []
        policies = ('information_hungarian','nearest_greedy')
        for zone,layout,seed,policy in itertools.product(('center','east','west'),(0,1),(7,11),policies):
            video = ['--video'] if (zone,layout,seed)==('center',0,7) else []
            cases.append((f'{zone}-{layout}-{seed}-{policy}',
                          ['--zone',zone,'--layout',str(layout),'--seed',str(seed),'--policy',policy,*video]))
        return cases
    return [(f'{seed}-{link}',['--seed',str(seed),'--link',link,
                             *(['--video'] if seed==7 and link in ('ideal','cut') else [])])
            for seed,link in itertools.product((7,11),('ideal','delay','loss','cut'))]


def execute(root,pilot,name,flags,excluded,rate):
    out = root/f'p{pilot}'/name
    out.mkdir(parents=True,exist_ok=True)
    result = out/'result.json'
    zone = flags[flags.index('--zone')+1] if '--zone' in flags else 'center'
    if zone in excluded:
        outcome = {'pilot':pilot,'zone':zone,'status':'excluded','error':excluded[zone]}
        result.write_text(json.dumps(outcome,indent=2)+'\n')
        return outcome
    command = ['/usr/bin/python3','-u',str(TRIAL),'--pilot',str(pilot),'--out',str(out),
               '--rate',str(min(rate,7) if '--video' in flags else rate),*flags]
    env = dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    with (out/'console.log').open('w') as log:
        run = subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.exists():
        return json.loads(result.read_text())
    outcome = {'pilot':pilot,'status':'failed','command':command,'exit_code':run.returncode}
    result.write_text(json.dumps(outcome,indent=2)+'\n')
    return outcome


def combine(root,pilot,paths):
    videos = [root/f'p{pilot}'/name/'live.mp4' for name in paths]
    if not all(video.is_file() and video.stat().st_size for video in videos):
        return
    if pilot>=5 and not all(json.loads((video.parent/'result.json').read_text())['status']=='complete'
                            for video in videos):
        return
    (root/'videos').mkdir(exist_ok=True)
    out = root/'videos'/f'piloto_{pilot}.mp4'
    if pilot==1:
        labels = ('Caso libre','Caso con obstaculo insertado')
        overlay = ';'.join(
            f"[{i}:v]drawtext=text='{label}':x=312:y=46:fontsize=18:"
            f"fontcolor=white:box=1:boxcolor=0x111923@0.9:boxborderw=5[v{i}]"
            for i,label in enumerate(labels))
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(videos[0]),'-i',str(videos[1]),
                        '-filter_complex',overlay+';[v0][v1]concat=n=2:v=1:a=0[v]',
                        '-map','[v]','-c:v','libx264','-threads','2','-crf','21',
                        '-movflags','+faststart',str(out)],check=True)
    else:
        listing = root/f'video-p{pilot}.txt'
        listing.write_text(''.join(f"file '{video.as_posix()}'\n" for video in videos))
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),
                        '-c','copy','-movflags','+faststart',str(out)],check=True)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'],check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pilots',nargs='*',type=int,choices=[1,2,3,4,5,6])
    parser.add_argument('--out',type=Path,default=BASE/'executed')
    parser.add_argument('--jobs',type=int,default=4)
    parser.add_argument('--rate',type=float,default=10)
    args = parser.parse_args()
    pilots = args.pilots or [1,2,3,4]
    root = args.out.resolve()
    if root.exists() and any(root.iterdir()):
        parser.error('Choose an empty output directory to avoid reusing evidence from an earlier matrix')
    if args.jobs < 1 or args.rate <= 0:
        parser.error('--jobs and --rate must be positive')
    root.mkdir(parents=True,exist_ok=True)
    excluded = {}
    zones = ['center']
    if 3 in pilots:
        zones.append('east')
    if 3 in pilots or 5 in pilots:
        zones.append('west')
    for zone in zones:
        try:
            prepare(zone)
        except (RuntimeError,ValueError,OSError,subprocess.TimeoutExpired) as error:
            excluded[zone] = str(error)
    work = [(pilot,name,flags) for pilot in pilots for name,flags in schedule(pilot)]
    outcomes = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {pool.submit(execute,root,pilot,name,flags,excluded,args.rate):(pilot,name)
                   for pilot,name,flags in work}
        for future in as_completed(pending):
            pilot,name = pending[future]
            result = future.result()
            outcomes[f'p{pilot}/{name}'] = result
            (root/'matrix.json').write_text(json.dumps(outcomes,indent=2)+'\n')
            print(f'P{pilot} {name}: {result["status"]} t={result.get("duration_s","—")}',flush=True)
    pairs = {1:['clear','obstacle'],2:['nominal'],
             3:['center-0-7-information_hungarian','center-0-7-nearest_greedy'],
             4:['7-ideal','7-cut'],5:['bypass','sealed'],6:['hidden','emergent','oracle']}
    for pilot in pilots:
        combine(root,pilot,pairs[pilot])


if __name__=='__main__':
    main()
