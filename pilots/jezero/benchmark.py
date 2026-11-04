"""Paired noise-seed comparison on one terrain, not statistical generalization."""
from pathlib import Path
import argparse
import copy
import csv
import json
import numpy as np
from mission import load_data, run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/jezero')
    p.add_argument('--out',type=Path,default=Path('evidence/jezero'))
    p.add_argument('--seeds',type=int,nargs='+',default=[7,11,19])
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    data=load_data(a.data)
    config=json.loads(Path(__file__).with_name('scenario.json').read_text())
    rows=[]
    for seed in a.seeds:
        for policy in ['information_hungarian','nearest_greedy']:
            c=copy.deepcopy(config);c['seed']=seed
            r=run(*data,c,policy);s=r['summary']
            row={'seed':seed,'policy':policy,'success':s['success'],'duration_s':s['duration_s'],
                 'initial_rmse_m':s['initial_rmse_m'],'final_rmse_m':s['final_rmse_m'],
                 'coverage':s['observed_fraction'],'samples':s['samples_completed'],
                 'drone_distance_m':sum(x['distance_m'] for x in s['agents'].values() if x['kind']=='drone')}
            for threshold in [.5,.8,.95]:
                ts=[m['time_s'] for m in r['metrics'] if m['coverage']>=threshold]
                row[f't{int(threshold*100)}_s']=ts[0] if ts else None
            rows.append(row);print(json.dumps(row),flush=True)
    with (a.out/'benchmark.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={'seeds':a.seeds,'terrain_sha256':data[3]['terrain_sha256'],
            'scope':'One fixed crop and fixed target layout; seeds vary only sensor noise.', 'policies':{}}
    for policy in sorted({r['policy'] for r in rows}):
        rs=[r for r in rows if r['policy']==policy]
        result['policies'][policy]={'successes':sum(r['success'] for r in rs),'runs':len(rs)}
        for key in ['duration_s','final_rmse_m','drone_distance_m','t50_s','t80_s','t95_s']:
            values=[r[key] for r in rs if r[key] is not None]
            result['policies'][policy][key]={'mean':float(np.mean(values)),'min':float(min(values)),'max':float(max(values))}
    (a.out/'benchmark_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if not all(r['success'] for r in rows):raise SystemExit(2)


if __name__=='__main__':main()
