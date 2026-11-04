"""Generate an offline viewer, measured-result report and separate plots."""
from pathlib import Path
import argparse
import base64
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mission import load_data


def b64(x):return base64.b64encode(np.ascontiguousarray(x).tobytes()).decode('ascii')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='data/jezero');p.add_argument('--out',type=Path,default=Path('evidence/jezero'))
    a=p.parse_args();out=a.out
    ref,prior,valid,meta=load_data(a.data)
    s=json.loads((out/'summary.json').read_text());c=json.loads((out/'scenario_used.json').read_text())
    events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
    trajectory=[json.loads(x) for x in (out/'trajectory.jsonl').read_text().splitlines()]
    metrics=list(csv.DictReader((out/'metrics.csv').open()))
    with np.load(out/'belief_frames.npz') as arrays:
        mean=arrays['mean'].copy();var=arrays['var'].copy()
    # Viewer downsamples to 64x64 and quantizes height for display only. Numerical artifacts retain full precision.
    stride=max(1,len(ref)//64);low=float(min(np.min(ref),np.min(prior),np.min(mean)));high=float(max(np.max(ref),np.max(prior),np.max(mean)))
    quant=lambda x:np.clip(np.round((x[::stride,::stride]-low)/(high-low)*65535),0,65535).astype('<u2')
    frames=[]
    for m in metrics:
        t=float(m['time_s']);tr=max((x for x in trajectory if x['time_s']<=t),key=lambda x:x['time_s'])
        seen=sorted({e['site'] for e in events if e['event']=='site_detected' and e['time_s']<=t})
        frames.append(dict(tr,seen_sites=seen,coverage=float(m['coverage']),completed_samples=int(m['completed_samples'])))
    payload={'n':len(ref[::stride]),'side':meta['side_m'],'summary':s,'sites':c['injected_sites'],
             'frames':frames,'trajectory':trajectory,'events':events,
             'prior':b64(quant(prior)),'reference':b64(quant(ref)),
             'mean':[b64(quant(x)) for x in mean],
             'sigma':[b64(np.clip(np.sqrt(x[::stride,::stride])/c['initial_sigma_m']*255,0,255).astype('uint8')) for x in var]}
    template=Path(__file__).with_name('viewer_template.html').read_text()
    (out/'viewer.html').write_text(template.replace('__PILOT_DATA__',json.dumps(payload,separators=(',',':'))),encoding='utf-8')
    ts=[float(m['time_s']) for m in metrics]
    for key,label,name in [('coverage','Fraction observed locally','coverage.png'),('rmse_m','Elevation RMSE against held-out DEM (m)','rmse.png')]:
        fig,ax=plt.subplots(figsize=(9,4.8));ax.plot(ts,[float(m[key]) for m in metrics],linewidth=2)
        ax.set(xlabel='Mission time (s)',ylabel=label,title='Jezero pilot · simulated observations on real orbital terrain')
        ax.grid(alpha=.25);fig.tight_layout();fig.savefig(out/name,dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,7));im=ax.imshow(ref-meta['origin_z_m'],extent=[-meta['side_m']/2,meta['side_m']/2,-meta['side_m']/2,meta['side_m']/2])
    for aid in s['agents']:
        poses=np.array([f['positions'][aid] for f in trajectory]);ax.plot(poses[:,0],poses[:,1],label=aid,linewidth=1.2)
    for site in c['injected_sites']:ax.annotate(site['id'],site['xy_m'])
    ax.set(xlabel='Local easting (m)',ylabel='Local northing (m)',title='Actual Jezero topography · simulated agent trajectories')
    fig.colorbar(im,ax=ax,label='Height relative to local origin (m)');ax.legend(loc='upper left',fontsize=8)
    fig.tight_layout();fig.savefig(out/'mission_map.png',dpi=160);plt.close(fig)
    benchmark=json.loads((out/'benchmark_summary.json').read_text()) if (out/'benchmark_summary.json').exists() else None
    compare=''
    if benchmark:
        compare='\n## Comparación pareada\n\nMismo terreno y objetivos; solo cambia el ruido del sensor entre semillas. No demuestra generalización.\n\n| Política | Ejecuciones completas | Duración media (s) | Tiempo al 80 % (s) | Distancia aérea total (m) |\n|---|---:|---:|---:|---:|\n'
        for name,b in benchmark['policies'].items():
            compare+=f"| {name} | {b['successes']}/{b['runs']} | {b['duration_s']['mean']:.1f} | {b['t80_s']['mean']:.1f} | {b['drone_distance_m']['mean']:.1f} |\n"
        compare+='\nLa política informativa favorece conocer el terreno temprano, pero no necesariamente minimiza la duración total de la misión. Conservar ambos objetivos para la siguiente iteración.\n'
    rows='\n'.join(f"| {aid} | {d['distance_m']:.1f} | {', '.join(d['tasks_completed'])} |" for aid,d in s['agents'].items())
    report=f'''# Piloto Jezero — resultados ejecutados

## Alcance y procedencia

Terreno orbital **real**: recorte de {meta['side_m']:.0f} × {meta['side_m']:.0f} m centrado en {meta['center_lat_planetocentric_deg']}° N, {meta['center_lon_east_deg']}° E. MRO/CTX (20 m de información nativa) inicializa el mapa; MRO/HiRISE (postes nativos de 1 m, remuestreados a {meta['cell_m']} m) actúa como referencia oculta del simulador. Hay {meta['shape'][0]} × {meta['shape'][1]} celdas de cálculo.

La misión, los objetivos y los sensores son **hipotéticos**. El simulador revela alturas mediante huellas de observación y ruido controlado; no reconstruye geometría a partir de cámaras. El error se mide respecto al DEM de referencia, no respecto a mediciones de campo. No se ejecutó Gazebo para producir estas métricas.

- Motor: {s['engine']}.
- Comunicación: global, instantánea y sin pérdidas.
- Semilla principal: {s['seed']}.
- SHA-256 de datos: `{s['terrain_sha256']}`.
- Versiones de ejecución: `{json.dumps(s['versions'])}`.

## Resultado principal

| Medida | Resultado |
|---|---:|
| Misión completada y seis regresos | {s['success']} |
| Tiempo simulado total | {s['duration_s']:.0f} s |
| Cobertura por observación local | {100*s['observed_fraction']:.2f} % |
| Error inicial CTX frente a HiRISE | {s['initial_rmse_m']:.4f} m RMSE |
| Error final del mapa estimado | {s['final_rmse_m']:.4f} m RMSE |
| Objetivos ficticios descubiertos | {s['discovered_sites']} |
| Inspecciones de rovers | {s['inspections_completed']} |
| Muestreos humanos | {s['samples_completed']} |
| Pasos terrestres registrados en celdas no observadas | {s['ground_steps_in_unobserved_cells']} |

El chequeo de celdas y pendientes NO certifica seguridad física: no modela boulders subpíxel, suelo, contactos ni colisiones entre agentes.

## Trabajo por agente

| Agente | Distancia de la simulación (m) | Tareas terminadas |
|---|---:|---|
{rows}

{compare}
## Cómo se generan las tareas

Los sectores de reconocimiento se proponen a partir del déficit de información del mapa inicial. Solo los sensores pueden revelar objetivos ficticios al entrar en su huella. Una detección crea `inspect`; completar esa tarea con un rover crea `sample`; solo entonces se puede asignar a un humano. La asignación húngara minimiza el costo definido sobre tareas actualmente factibles, con bonificación informativa para reconocimiento. No optimiza globalmente toda la misión ni reproduce íntegramente DisCoverage. Las tareas ya iniciadas se mantienen para evitar oscilaciones.

## Evidencia reproducible

- `viewer.html`: visor autónomo, sin servicios externos, con capas, reproducción y tareas.
- `events.jsonl`, `tasks.json`, `trajectory.jsonl`: trazabilidad temporal.
- `metrics.csv`, `summary.json`, `belief_final.npz`, `belief_frames.npz`: resultados numéricos.
- `benchmark.csv`, `benchmark_summary.json`: comparación con proximidad.
- `generated/jezero/`: exportación de terreno y seis agentes para **reproducción cinemática** en Gazebo; no es validación de control cerrado.

## Límites que deben conservarse

CTX y HiRISE pertenecen a **una sola misión**, MRO. Interpolar CTX a 4 m no crea detalles reales nuevos. La incertidumbre del mapa es un supuesto condicional del modelo y no la precisión oficial de esos productos. No hay límites de comunicación, baterías, soporte vital, biomecánica, aerodinámica, SLAM o reconstrucción fotogramétrica. Los dos humanos son agentes independientes de una misión ficticia; no se certifica ningún protocolo de EVA.

## Fuentes

Fergason et al. (2020), USGS, *Mars 2020 Terrain Relative Navigation HiRISE DTM Mosaic*. DOI: https://doi.org/10.5066/P9REJ9JN

Fergason et al. (2020), USGS, *Mars 2020 Terrain Relative Navigation CTX DTM Mosaic*. DOI: https://doi.org/10.5066/P906QQT8

Catálogos originales: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/index.html y https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/CTX/index.html
'''
    (out/'report.md').write_text(report,encoding='utf-8')
    print('Created viewer.html, report.md, mission_map.png, coverage.png and rmse.png')


if __name__=='__main__':main()
