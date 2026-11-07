"""Summarize Belva runs, including attempts that stopped before returning."""
import argparse
import json
import math
from pathlib import Path
import tarfile

from belva_report import return_tracking
from extension_cases import belva_fixture
from extension_report import rows


def summarize(root, seed, homes):
    folder = root/f'seed-{seed}'
    result_path = folder/'result.json'
    result = json.loads(result_path.read_text()) if result_path.exists() else {}
    events = rows(folder/'events.jsonl') if (folder/'events.jsonl').exists() else []
    states = rows(folder/'states.jsonl') if (folder/'states.jsonl').exists() else []
    last = states[-1] if states else {}
    completed = {e['agent']:e for e in events if e['event']=='task_completed'
                 and e['task']==f'return:{e["agent"]}'}
    returns = {}
    for agent, home in homes.items():
        event = completed.get(agent)
        completion_error = math.dist(event['observed_xy_m'],home) if event else None
        final_error = result.get('final_home_error_m',{}).get(agent)
        last_pose = last.get('poses',{}).get(agent)
        returns[agent] = dict(verified=completion_error is not None and completion_error<=2
                              and final_error is not None and final_error<=2,
                              completion_s=event['t_s'] if event else None,
                              completion_error_m=completion_error, final_error_m=final_error,
                              last_sampled_error_m=math.dist(last_pose[:2],home) if last_pose else None,
                              last_task=last.get('tasks',{}).get(agent))
    inspector = next((e['agent'] for e in events
                      if e['event']=='assigned' and e['task']=='inspect:S1'),None)
    route = next((e for e in events if e['event']=='assigned'
                  and e['task']==f'return:{inspector}'),None)
    track_error = first_deviation = reverse_samples = initial_heading = None
    if route and len(route['path'])>=2:
        end = completed.get(inspector,{}).get('t_s',math.inf)
        samples = [s for s in states if route['t_s']<=s['t_s']<=end and inspector in s['poses']]
        if samples:
            errors = return_tracking(route['path'],[s['poses'][inspector][:2] for s in samples])
            track_error = float(max(errors))
            first_deviation = next((s['t_s'] for s,error in zip(samples,errors) if error>2),None)
            reverse_samples = sum(s.get('rover_control',{}).get(inspector,{}).get('direction')==-1
                                  for s in samples)
        departure = next((s for s in reversed(states)
                          if s['t_s']<=route['t_s'] and inspector in s['poses']),None)
        if departure:
            initial_heading = math.degrees(departure['poses'][inspector][3])
    exit_path = root/f'seed-{seed}.exit'
    return dict(seed=seed, status=result.get('status','no_result'), error=result.get('error'),
                exit_code=int(exit_path.read_text()) if exit_path.exists() else None,
                duration_s=result.get('duration_s',last.get('t_s')), coverage=result.get('coverage'),
                terrain_sha256=result.get('terrain_sha256'), returns=returns,
                verified_count=sum(v['verified'] for v in returns.values()),
                individual_checks=sum(e['event']=='individual_control' and e['passed'] for e in events),
                zero_sent=any(e['event']=='zero_velocity_sent' and set(e['agents'])==set(homes) for e in events),
                remaining_tasks=result.get('remaining_tasks'), inaccessible=result.get('inaccessible'),
                inspection_rover=inspector, rover_return_cross_track_max_m=track_error,
                rover_return_first_over_2m_s=first_deviation,
                rover_return_initial_heading_deg=initial_heading,
                rover_return_reverse_samples=reverse_samples,
                inspection_rover_last_waypoint=last.get('rover_control',{}).get(inspector,{}).get('waypoint'))


def compare(root, out, seeds):
    homes = belva_fixture()['homes']
    runs = [summarize(root,seed,homes) for seed in seeds]
    comparison = dict(runs=runs, six_returns=sum(r['verified_count']==len(homes) for r in runs),
                      complete_missions=sum(r['status']=='complete' and r['verified_count']==len(homes)
                                            and r['zero_sent'] and r['individual_checks']==len(homes)
                                            for r in runs))
    out.mkdir(parents=True,exist_ok=True)
    (out/'seed-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    with tarfile.open(out/'seed-telemetry.tar.gz','w:gz') as archive:
        for name in ('environment.txt','terrain-check.log','scene-check.log','canonical.log'):
            path = root/name
            if path.is_file():
                archive.add(path,arcname=name)
        for seed in seeds:
            for name in (f'seed-{seed}.console.log',f'seed-{seed}.exit',
                         *(f'seed-{seed}/{name}' for name in
                           ('result.json','events.jsonl','states.jsonl','gazebo.log',
                            'live.sdf','provenance.json'))):
                path = root/name
                if path.is_file():
                    archive.add(path,arcname=name)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    parser.add_argument('out',type=Path)
    parser.add_argument('seeds',nargs='+',type=int)
    args = parser.parse_args()
    compare(args.root,args.out,args.seeds)
