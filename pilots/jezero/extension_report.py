"""Validate and package the five Gazebo scenarios of pilots 5 and 6."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tarfile

from extension_cases import OPEN_END, WALL_X, sites_for
from live_world import BASE, ROOT

CASES = {5:('bypass','sealed'),6:('hidden','emergent','oracle')}


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def validate(pilot,scenario,directory):
    result = json.loads((directory/'result.json').read_text())
    events = rows(directory/'events.jsonl')
    states = rows(directory/'states.jsonl')
    assert result['status']=='complete',(scenario,result['status'],result.get('remaining_tasks'))
    assert len([e for e in events if e['event']=='individual_control' and e['passed']])==6
    assert events[-1]['event']=='zero_velocity_sent'
    assert result['returns']==6 and max(result['final_home_error_m'].values())<=2
    assert result['video_frames']>0
    if pilot==5:
        crossings = {}
        routes = {}
        for name in result['final_home_error_m']:
            xy = [row['poses'][name][:2] for row in states]
            cut = [a[1]+(b[1]-a[1])*(WALL_X-a[0])/(b[0]-a[0])
                   for a,b in zip(xy,xy[1:]) if (a[0]<WALL_X<=b[0] or b[0]<WALL_X<=a[0])]
            if cut:
                crossings[name] = cut
        assert any(name.startswith('drone') for name in crossings)
        terrestrial = {name:ys for name,ys in crossings.items() if not name.startswith('drone')}
        assert not result['wall_entry_agents']
        if scenario=='bypass':
            assert any(n.startswith('rover') for n in terrestrial)
            assert any(n.startswith('human') for n in terrestrial)
            assert min(y for ys in terrestrial.values() for y in ys)>OPEN_END
            for task in ('inspect:S1','sample:S1'):
                event = next(e for e in events if e['event']=='assigned' and e['task']==task)
                index = next(i for i,e in enumerate(states) if e['t_s']>=event['t_s'])
                start = states[max(0,index-1)]['poses'][event['agent']][:2]
                route = [start,*event['path']]
                direct = math.dist(route[0],route[-1])
                length = sum(math.dist(a,b) for a,b in zip(route,route[1:]))
                assert length>direct
                cross_y = start[1]+(route[-1][1]-start[1])*(WALL_X-start[0])/(route[-1][0]-start[0])
                assert cross_y<OPEN_END
                arrival = next(e['t_s'] for e in events if e['event']=='task_completed' and e['task']==task)
                routes[task] = dict(agent=event['agent'],euclidean_m=direct,route_m=length,
                                    travel_and_service_s=arrival-event['t_s'],straight_crossing_y_m=cross_y)
        else:
            assert not terrestrial and result['inaccessible']==['inspect:S1']
            assert result['inspections']==result['samples']==0
        result.update(scarp_crossings_y_m=crossings,route_comparison=routes)
    else:
        discoveries = {}
        for site in sites_for(6):
            names = [('site_appeared','site',site.name),('site_detected','site',site.name),
                     ('assigned','task','inspect:'+site.name),('task_completed','task','inspect:'+site.name),
                     ('sample_enabled','task','sample:'+site.name),('assigned','task','sample:'+site.name),
                     ('task_completed','task','sample:'+site.name)]
            sequence = []
            for kind,key,value in names:
                matches = [(i,e) for i,e in enumerate(events) if e['event']==kind and e.get(key)==value]
                assert len(matches)==1,(scenario,names,matches)
                sequence.append(matches[0])
            assert [i for i,_ in sequence]==sorted(i for i,_ in sequence)
            assert sequence[3][1]['agent'].startswith('rover_')
            assert sequence[6][1]['agent'].startswith('human_')
            appeared,detected,assigned = [event for _,event in sequence[:3]]
            if scenario!='oracle':
                assert detected['sensor_stamp_s']>=appeared['t_s']-.02
                assert math.dist(site.xy,detected['xy'])<2,(scenario,detected)
            discoveries[site.name] = dict(observer=detected['observer'],
                appeared_s=appeared['t_s'],detected_s=detected['t_s'],
                detection_delay_s=detected['t_s']-appeared['t_s'],
                allocation_delay_s=assigned['t_s']-detected['t_s'])
        if scenario!='oracle':
            observers = [d['observer'] for d in discoveries.values()]
            assert any(name.startswith('drone') for name in observers)
            assert any(name.startswith(('rover','human')) for name in observers)
        if scenario=='emergent':
            assert discoveries['S3']['appeared_s']>=24
        result.update(discoveries=discoveries,duplicate_science_tasks=0)
    result['accepted'] = True
    return result


def movie(inputs,output):
    command = ['ffmpeg','-v','error','-y']
    for clip in inputs:
        command.extend(('-i',str(clip)))
    segments = ';'.join(f'[{i}:v]setpts=PTS-STARTPTS[v{i}]' for i in range(len(inputs)))
    concat = ''.join(f'[v{i}]' for i in range(len(inputs)))
    filters = f'{segments};{concat}concat=n={len(inputs)}:v=1:a=0,fps=15[out]'
    command.extend(('-filter_complex',filters,'-map','[out]','-c:v','libx264',
                    '-threads','2','-crf','20','-movflags','+faststart',str(output)))
    subprocess.run(command,check=True)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(output),'-f','null','-'],check=True)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def report(out,results):
    lines = ['# Jezero · terreno no convexo y tareas descubiertas','',
             'Los cinco escenarios se ejecutaron en Gazebo Harmonic. El video de cada piloto alterna sus variantes con el mapa cenital al centro y seis vistas laterales con cuadrícula de 4 m.', '',
             '| Piloto y variante | Duración simulada (s) | Cobertura | Inspecciones / muestreos | Regresos |',
             '|---|---:|---:|---:|---:|']
    for key,r in results.items():
        lines.append(f'| {key} | {r["duration_s"]:.2f} | {r["coverage"]:.1%} | {r["inspections"]} / {r["samples"]} | {r["returns"]} |')
    bypass,sealed = results['p5/bypass'],results['p5/sealed']
    lines.extend(['','## Piloto 5 · cuenca con acceso parcial','',
                  'El recorte occidental CTX/HiRISE de 128 × 128 m aporta relieve orbital real. Una barrera experimental añadida, que representa un escarpe infranqueable, garantiza la geometría no convexa del tránsito terrestre. La variante abierta deja un corredor al norte. La cerrada extiende la barrera hasta el borde. El dron observa ambos lados en las dos variantes.', '',
                  'Los agentes estiman la transitabilidad con alturas observadas, ocupación, pendiente, desnivel y margen. Los límites experimentales de pendiente son 18° para el rover y 22° para el humano. El planificador conserva la distinción entre un paso todavía sin observar y una desconexión incluso con paso optimista por terreno desconocido.', '',
                  '| Tarea | Agente | Distancia directa (m) | Ruta transitable (m) | Viaje y servicio (s) |',
                  '|---|---|---:|---:|---:|'])
    for task,r in bypass['route_comparison'].items():
        lines.append(f'| {task} | {r["agent"]} | {r["euclidean_m"]:.1f} | {r["route_m"]:.1f} | {r["travel_and_service_s"]:.1f} |')
    crossing = [y for name,ys in bypass['scarp_crossings_y_m'].items() if not name.startswith('drone') for y in ys]
    lines.extend(['',f'Los cruces terrestres observados en la variante abierta quedaron al norte del extremo de la barrera (y = {OPEN_END} m). El menor fue y = {min(crossing):.2f} m. '
                  f'En la variante cerrada se clasificó `{sealed["inaccessible"][0]}` como inaccesible y se confirmaron cero cruces terrestres. La distancia directa es una referencia geométrica que atraviesa la barrera.', '',
                  '[Video del piloto 5](piloto_5.mp4).','',
                  '## Piloto 6 · tareas descubiertas al explorar','',
                  'Los objetivos son marcadores ficticios. Las variantes oculta y emergente comienzan con el tablero científico vacío. Las cámaras nadir de los drones y las cámaras terrestres simuladas de corto alcance reportan detecciones por pose, tiempo y color. Una observación terrestre requiere al menos 12 píxeles de color y profundidad dentro del alcance de 5,5 m. La confianza es un indicador del detector basado en píxeles y carece de calibración probabilística.', '',
                  'El alero simulado oculta S4 desde arriba. En la variante emergente Gazebo inserta S3 durante la ejecución. La variante oráculo entrega las posiciones al coordinador al inicio para comparar. Una detección abre la inspección y completarla habilita el muestreo. Las detecciones repetidas se consolidan por sitio. El explorador terrestre tiene prioridad en el corredor compartido, así que las inspecciones esperan a que termine su reconocimiento en las tres variantes.', '',
                  '| Variante | Sitio | Observador | Aparición (s) | Detección (s) | Detección a asignación (s) |',
                  '|---|---|---|---:|---:|---:|'])
    for variant in CASES[6]:
        for site,d in results[f'p6/{variant}']['discoveries'].items():
            lines.append(f'| {variant} | {site} | {d["observer"]} | {d["appeared_s"]:.2f} | {d["detected_s"]:.2f} | {d["allocation_delay_s"]:.2f} |')
    lines.extend(['','La auditoría comprobó una única cadena de inspección y muestreo por sitio, ninguna asignación científica anterior a su detección en las variantes exploratorias y al menos un descubrimiento aéreo y uno terrestre en cada una. Estos ensayos usan enlace ideal y asignaciones con caducidad. La comparación con el oráculo corresponde a una semilla por variante.', '',
                  '[Video del piloto 6](piloto_6.mp4).','',
                  '## Datos y reproducción','',
                  '- CTX es el mapa inicial. HiRISE construye el suelo y queda en el simulador y el evaluador. Los resultados incluyen el SHA-256 de cada recorte.',
                  '- La barrera, el alero y los marcadores son geometría ficticia del escenario. Profundidad, RGB, navegación y posición observada proceden de Gazebo. Los humanos conservan su movimiento cinemático con orientación hacia el avance.',
                  '- En la calibración terrestre se descartaron detecciones adelantadas al acortar el alcance y endurecer el filtro de color. Tras un atasco del explorador, se reservó el corredor y se desplazó el estacionamiento del segundo rover. La variante emergente se repitió por separado tras un fallo de arranque de sensores. Los videos publicados corresponden a los ensayos que superaron la auditoría.', '',
                  '    OPENBLAS_NUM_THREADS=1 /usr/bin/python3 pilots/jezero/run_live_pilots.py 5 6 --jobs 3 --rate 7 --out generated/closed_loop/extensions',
                  '    /usr/bin/python3 pilots/jezero/extension_report.py', '',
                  '[Resultados por variante](results.json) · [Telemetría y logs](telemetry.tar.gz) · [Hashes de los videos](video_hashes.json).',''])
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--p5',type=Path,default=BASE/'extensions')
    parser.add_argument('--p6',type=Path,default=BASE/'extensions')
    parser.add_argument('--emergent',type=Path,help='Override the folder for a separately repeated emergent trial')
    parser.add_argument('--out',type=Path,default=ROOT/'evidence/jezero_56')
    args = parser.parse_args()
    roots = {5:args.p5,6:args.p6}
    results,hashes = {},{}
    args.out.mkdir(parents=True,exist_ok=True)
    with tarfile.open(args.out/'telemetry.tar.gz','w:gz') as archive:
        for pilot,scenarios in CASES.items():
            clips = []
            for scenario in scenarios:
                key = f'p{pilot}/{scenario}'
                folder = args.emergent if key=='p6/emergent' and args.emergent else roots[pilot]/key
                results[key] = validate(pilot,scenario,folder)
                clips.append(folder/'live.mp4')
                for name in ('result.json','states.jsonl','events.jsonl','gazebo.log','console.log','provenance.json'):
                    if (folder/name).is_file():
                        archive.add(folder/name,arcname=f'{key}/{name}')
            name = f'piloto_{pilot}.mp4'
            hashes[name] = movie(clips,args.out/name)
        for path in (BASE/'extension-checks').glob('*.log'):
            archive.add(path,arcname=f'preflight/{path.name}')
        for trial in ('extensions/p6/hidden','extensions_hidden/p6/hidden','extensions_final/p6/emergent'):
            for name in ('result.json','events.jsonl'):
                path = BASE/trial/name
                if path.is_file():
                    archive.add(path,arcname=f'calibration/{trial}/{name}')
    (args.out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    (args.out/'video_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    report(args.out,results)
    for key,result in results.items():
        print(f'{key}: {result["duration_s"]:.2f}s, coverage={result["coverage"]:.1%}')


if __name__=='__main__':
    main()
