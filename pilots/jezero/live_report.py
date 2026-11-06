"""Package live Gazebo results, source checks, logs and videos."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import tarfile

import numpy as np
import rasterio

from live_world import BASE, ROOT
from mission import Grid, load_data, slopes
from run_live_pilots import combine, schedule


def audit(zone, root):
    data = BASE/'data'/zone
    ref,prior,_,meta = load_data(data)
    source = BASE/'source_center' if zone=='center' else data
    checks = {}
    for name,array in [('reference',ref),('prior',prior)]:
        tif = source/f'{name}.tif'
        if tif.is_file():
            with rasterio.open(tif) as raster:
                np.testing.assert_allclose(raster.read(1),array,rtol=0,atol=.002)
                np.testing.assert_allclose(raster.transform.to_gdal(),meta['affine_gdal'])
                assert '3396190' in raster.crs.to_wkt()
                checks[name] = float(np.max(np.abs(raster.read(1)-array)))
    mesh_error = None
    for manifest in root.glob('p*/*/provenance.json'):
        if json.loads(manifest.read_text())['terrain_sha256']!=meta['terrain_sha256']:
            continue
        mesh = manifest.parent/'models/jezero_terrain/meshes/terrain.obj'
        lines = mesh.read_text().splitlines()
        points = np.array([list(map(float,x.split()[1:])) for x in lines if x.startswith('v ')])
        normals = np.array([list(map(float,x.split()[1:])) for x in lines if x.startswith('vn ')])
        grid = Grid(len(ref),meta['cell_m'])
        xy = [grid.xy((r,c)) for r in range(grid.n) for c in range(grid.n)]
        np.testing.assert_allclose(points[:,:2],xy,rtol=0,atol=1e-7)
        mesh_error = float(np.max(np.abs(points[:,2]+meta['origin_z_m']-ref.ravel())))
        assert mesh_error<1e-6 and (normals[:,2]>0).all()
        np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1,atol=1e-7,rtol=0)
        break
    return dict(zone=zone,sha256=meta['terrain_sha256'],cell_m=meta['cell_m'],
                lat_deg=meta['center_lat_planetocentric_deg'],lon_deg=meta['center_lon_east_deg'],
                mesh_height_error_m=mesh_error,geotiff_height_error_m=checks,
                mean_slope_deg=float(slopes(ref,4.).mean()),max_slope_deg=float(slopes(ref,4.).max()))


def verify_sequence(row, events):
    """Audit the independent event log after each completed trial."""
    if row.get('status')!='complete':
        return
    kinds = [e['event'] for e in events]
    assert kinds[-1]=='zero_velocity_sent'
    if row['pilot']==1:
        if row['obstacle']:
            assert kinds.index('obstacle_inserted')<kinds.index('obstacle_observed')<kinds.index('replan')
            assert row['obstacle_contact_reports']==0
        if row['drop_odom']:
            assert 'navigation_stale_stop' in kinds and row['odometry_outage_drift_m']<.2
        return
    for site in ('S1','S2','S3','S4'):
        indices = []
        for event, task in [('site_detected',None),('task_completed','inspect:'+site),
                            ('sample_enabled','sample:'+site),('task_completed','sample:'+site)]:
            matches = [(i,e) for i,e in enumerate(events) if e['event']==event and
                       (e.get('site')==site if task is None else e.get('task')==task)]
            assert len(matches)==1,(site,event,task,matches)
            i,e = matches[0]
            if event=='task_completed':
                assert e['agent'].startswith('rover_' if task.startswith('inspect:') else 'human_')
            indices.append(i)
        assert indices==sorted(indices)
    returns = [e['agent'] for e in events if e['event']=='task_completed' and e['task'].startswith('return:')]
    assert sorted(returns)==sorted(row['final_home_error_m'])
    assert len(returns)==6 and max(row['final_home_error_m'].values())<=2


def collect(root):
    summary = {}
    for p in (1,2,3,4):
        for name,_ in schedule(p):
            key = f'p{p}/{name}'
            directory = root/key
            result = directory/'result.json'
            row = json.loads(result.read_text()) if result.is_file() else {'pilot':p,'status':'not_run'}
            if (directory/'events.jsonl').is_file():
                events = [json.loads(line) for line in (directory/'events.jsonl').read_text().splitlines()]
                verify_sequence(row,events)
                row['event_sequence_audited'] = row['status']=='complete'
                row['events'] = dict(Counter(e['event'] for e in events))
                replans = [e for e in events if e['event']=='replan']
                if replans:
                    row['observation_to_replan_s'] = replans[0]['t_s']-replans[0]['sensor_stamp_s']
                assignments = {}
                transfers = 0
                for e in events:
                    if e['event']=='assigned':
                        previous = assignments.setdefault(e['task'],e['agent'])
                        if previous!=e['agent']:
                            transfers += 1
                            assignments[e['task']] = e['agent']
                completed = [e['task'] for e in events if e['event']=='task_completed']
                row.update(task_changes_of_agent=transfers,
                           duplicate_committed_tasks=len(completed)-len(set(completed)))
            summary[key] = row
    return summary


def median(values):
    numbers = [v for v in values if v is not None]
    return f'{statistics.median(numbers):.2f}' if numbers else '—'


def report(out,summary,audits,videos):
    lines = [
        '# Jezero en lazo cerrado', '',
        'Los ensayos se ejecutan en Gazebo Harmonic con renderizado Ogre2 por software. '
        'El archivo de telemetría incluye los logs de arranque, pruebas, versiones y GPU cuando están disponibles.',
        '',
        '| Tipo de dato | Uso |','|---|---|',
        '| Real · CTX USGS/MRO | Mapa inicial aproximado. Información nativa de 20 m remuestreada a 4 m. |',
        '| Real · HiRISE USGS/MRO | Geometría y colisión de Gazebo, y referencia del evaluador. Postes nativos de 1 m remuestreados a 4 m. El planificador usa CTX y mediciones locales. |',
        '| Simulado · percepción | Profundidad y RGB de Gazebo con alcance, huella y oclusión. Las alturas reciben ruido por celda y semilla. |',
        '| Simulado · navegación | Rover con odometría de ruedas e IMU y corrección local idealizada cada 2 s a partir de la pose simulada con ruido de 0,035 m. Drones y humanos reciben comandos cinemáticos y usan pose simulada conocida. |',
        '| Ficticio · escenario | Objetivos representados por marcadores de color, obstáculo y condiciones de comunicación. |',
        '| Derivado · evaluación | Cobertura, distancia, llegada y error frente al DEM orbital. Las poses observadas por el evaluador se registran separadas de la navegación. |',
        '',
        'La calibración con ruedas e IMU acumuló error. También se observó pérdida de tracción con dos apoyos pasivos. La versión final del rover usa dos ruedas motrices, un apoyo pasivo trasero y correcciones locales idealizadas. La marcha humana y el vuelo siguen siendo aproximaciones cinemáticas.',
        '', '## Resultados', '',
        '| Piloto | Casos previstos | Completos y verificados | Otros estados | Video |',
        '|---|---:|---:|---|---|',
    ]
    for p in (1,2,3,4):
        rows = [r for r in summary.values() if r['pilot']==p]
        counts = Counter(r['status'] for r in rows)
        other = ', '.join(f'{name} × {n}' for name,n in sorted(counts.items()) if name!='complete') or '—'
        video = f'[Video](videos/piloto_{p}.mp4)' if p in videos else 'Pendiente'
        lines.append(f'| {p} | {len(rows)} | {counts["complete"]} | {other} | {video} |')
    failed = [(key,row) for key,row in summary.items() if row['status']!='complete']
    if failed:
        lines.extend(['','### Casos sin completar',''])
        for key,row in failed:
            unfinished = ', '.join(row.get('remaining_tasks',[])) or '—'
            lines.append(f'- `{key}` · {row["status"]}. Tareas pendientes: {unfinished}.')
    lines.extend(['','### Percepción y misión nominal',''])
    for name in ('clear','obstacle','odom-outage'):
        row = summary['p1/'+name]
        values = [('error de llegada', 'rover_goal_error_m', 'm'),
                  ('distancia del centro del rover al borde del obstáculo', 'min_obstacle_center_clearance_m', 'm'),
                  ('latencia de replanteo', 'observation_to_replan_s', 's'),
                  ('deriva durante pérdida de odometría', 'odometry_outage_drift_m', 'm')]
        measures = ', '.join(f'{label} {row[key]:.2f} {unit}' for label,key,unit in values if row.get(key) is not None)
        contact = f', contactos {row["obstacle_contact_reports"]}' if row.get('obstacle') else ''
        lines.append(f'- **{name}** · {row["status"]}. {measures}{contact}.')
    row = summary['p2/nominal']
    lines.append(f'- **Misión nominal** · {row["status"]}. Detecciones {row.get("sites")}/4, '
                 f'inspecciones {row.get("inspections")}/4, muestreos {row.get("samples")}/4, regresos {row.get("returns")}/6.')
    lines.extend(['','### Comparación de terrenos','',
                  '| Zona | Política | Completas | Llegaron al 80 % | Mediana t80 (s) | Duración mediana de éxitos (s) | Cobertura final mediana (%) |',
                  '|---|---|---:|---:|---:|---:|---:|'])
    for zone in ('center','east','west'):
        for policy in ('information_hungarian','nearest_greedy'):
            rows = [r for k,r in summary.items() if k.startswith(f'p3/{zone}-') and k.endswith(policy)]
            done = [r for r in rows if r['status']=='complete']
            t80 = [r.get('t80_s') for r in rows]
            coverage = [100*r['coverage'] for r in rows if 'coverage' in r]
            lines.append(f'| {zone} | {policy} | {len(done)}/{len(rows)} | {sum(t is not None for t in t80)} | '
                         f'{median(t80)} | {median([r.get("duration_s") for r in done])} | {median(coverage)} |')
    pairs = [(r,summary[k.replace('information_hungarian','nearest_greedy')])
             for k,r in summary.items() if k.startswith('p3/') and k.endswith('information_hungarian')]
    coverage_delta = [near['t80_s']-info['t80_s'] for info,near in pairs
                      if info.get('t80_s') is not None and near.get('t80_s') is not None]
    duration_delta = [near['duration_s']-info['duration_s'] for info,near in pairs
                      if info['status']==near['status']=='complete']
    lines.extend(['',f'Mediana de proximidad menos política informativa en pares medibles. '
                  f'Tiempo hasta el 80 %: **{median(coverage_delta)} s** ({len(coverage_delta)} pares). '
                  f'Duración total: **{median(duration_delta)} s** ({len(duration_delta)} pares completos).',
                  '', '### Comunicaciones','',
                  '| Modo | Completas | Reasignaciones a otro agente | Confirmaciones rechazadas | Recuperación mediana (s) | Duración mediana de éxitos (s) |',
                  '|---|---:|---:|---:|---:|---:|'])
    for link in ('ideal','delay','loss','cut'):
        rows = [r for k,r in summary.items() if k.startswith('p4/') and k.endswith('-'+link)]
        done = [r for r in rows if r['status']=='complete']
        lines.append(f'| {link} | {len(done)}/{len(rows)} | {sum(r.get("task_changes_of_agent",0) for r in rows)} | '
                     f'{sum(r.get("rejected_confirmations",0) for r in rows)} | {median([r.get("link_recovery_s") for r in rows])} | '
                     f'{median([r.get("duration_s") for r in done])} |')
    lines.extend(['','Una reasignación puede repetir trabajo parcial. La telemetría distingue reasignaciones, confirmaciones rechazadas y tareas duplicadas aceptadas. La latencia de recuperación se mide desde el fin del corte hasta el primer estado recibido.',
                  '', '### Procedencia de los recortes','',
                  '| Zona | Centro lat/lon (°) | Pendiente media / máxima (°) | GeoTIFF verificados |',
                  '|---|---|---|---:|'])
    for a in audits:
        lines.append(f'| {a["zone"]} | {a["lat_deg"]:.5f}, {a["lon_deg"]:.5f} | '
                     f'{a["mean_slope_deg"]:.2f} / {a["max_slope_deg"]:.2f} | {len(a["geotiff_height_error_m"])} |')
    lines.extend(['','Cada zona tiene 128 × 128 m a 4 m por celda. Los centros ejecutados están separados más que el ancho de cada recorte. La auditoría conserva hashes y la comprobación de escala, orientación, cotas y normales.',
                  '', '[Reproducción](../../pilots/jezero/LIVE.md) · [CSV por ensayo](trials.csv) · [Matriz completa](matrix.json) · [Auditoría de terreno](terrain_audit.json) · [Telemetría y logs](telemetry.tar.gz).',''])
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8')


def package(root,out):
    out.mkdir(parents=True,exist_ok=True)
    summary = collect(root)
    (out/'matrix.json').write_text(json.dumps(summary,indent=2)+'\n')
    audits = [audit(z,root) for z in ('center','east','west') if (BASE/'data'/z/'terrain.npz').is_file()]
    (out/'terrain_audit.json').write_text(json.dumps(audits,indent=2)+'\n')
    fields = ['run','status','duration_s','t80_s','coverage','initial_rmse_m','final_rmse_m',
              'drone_distance_m','rover_distance_m','human_distance_m','inspections','samples','returns',
              'link_recovery_s','task_changes_of_agent','duplicate_committed_tasks']
    with (out/'trials.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore')
        writer.writeheader()
        for key,row in summary.items():
            distances = {f'{kind}_distance_m':sum(v for a,v in row.get('distance_m',{}).items() if a.startswith(kind))
                         for kind in ('drone','rover','human')}
            writer.writerow(dict(row,run=key,**distances))
    with tarfile.open(out/'telemetry.tar.gz','w:gz') as archive:
        for key in summary:
            for name in ('result.json','states.jsonl','events.jsonl','gazebo.log','console.log'):
                if (root/key/name).is_file():
                    archive.add(root/key/name,arcname=f'{key}/{name}')
        for name in ('baseline.log','regression.log','live-tests.log','imports.log','center-import.log','environment.txt'):
            if (BASE/name).is_file():
                archive.add(BASE/name,arcname=f'preflight/{name}')
        for trial in ('p1-obstacle','p1-turn','p1-fused','p1-tripod','p2-test'):
            for name in ('result.json','events.jsonl','states.jsonl','gazebo.log'):
                if (BASE/trial/name).is_file():
                    archive.add(BASE/trial/name,arcname=f'calibration/{trial}/{name}')
        for zone in ('east','west'):
            for log in (BASE/'data'/zone).glob('import_*.log'):
                archive.add(log,arcname=f'preflight/{zone}/{log.name}')
    videos = {}
    combine(root,1,['clear','obstacle'])
    for pilot in (1,2,3,4):
        video = root/'videos'/f'piloto_{pilot}.mp4'
        if video.is_file():
            subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
            dest = out/'videos'/video.name
            dest.parent.mkdir(exist_ok=True)
            shutil.copyfile(video,dest)
            videos[pilot] = hashlib.sha256(dest.read_bytes()).hexdigest()
    (out/'video_hashes.json').write_text(json.dumps(videos,indent=2)+'\n')
    report(out,summary,audits,videos)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=Path,default=BASE/'final')
    parser.add_argument('--out',type=Path,default=ROOT/'evidence/jezero_live')
    opts = parser.parse_args()
    package(opts.runs,opts.out)
