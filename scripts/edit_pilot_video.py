#!/usr/bin/env python3
"""Assemble captured Gazebo cameras with labels from measured phase timestamps."""
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parents[1]/'evidence'


def stamp(seconds):
    ms = round(seconds*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def main():
    report = json.loads((OUT/'results.json').read_text())
    duration = report['frames']['agents']/10
    phases = [(0., 'Vista general | Terreno sintetico de 90 x 90 m'),
              (5., 'Dos astronautas, dos rovers y dos drones')]
    previous = 'startup'
    for line in (OUT/'trajectory.jsonl').read_text().splitlines():
        row = json.loads(line)
        phase = row['phase']
        if phase != previous:
            label = ('Control individual: '+phase.removeprefix('individual_')
                     if phase.startswith('individual_') else
                     {'simultaneous':'Movimiento simultaneo de los seis agentes',
                      'stop':'Parada de los seis agentes verificada con poses'}.get(phase,phase))
            phases.append((5+row['sim'], label))
            previous = phase
    subtitles = []
    for i,(start,label) in enumerate(phases):
        end = phases[i+1][0] if i+1<len(phases) else 5+duration
        subtitles.append(f'{i+1}\n{stamp(start)} --> {stamp(end)}\n{label}\n')
    (OUT/'pilot.srt').write_text('\n'.join(subtitles),encoding='utf-8')
    filters = (
        '[0:v]trim=duration=5,setpts=PTS-STARTPTS[a];'
        '[1:v]setpts=PTS-STARTPTS[b];'
        '[a][b]concat=n=2:v=1:a=0,'
        "drawbox=x=0:y=0:w=iw:h=64:color=black@0.65:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='NASA SANDBOX | Gazebo Harmonic':fontcolor=white:fontsize=30:x=28:y=16,"
        "drawbox=x=0:y=ih-34:w=iw:h=34:color=black@0.65:t=fill,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='Terreno sintetico | Humanos y drones cinematicos | Captura real de simulacion':"
        "fontcolor=white:fontsize=18:x=28:y=h-26,"
        "subtitles=pilot.srt:force_style='FontName=DejaVu Sans,FontSize=20,MarginV=46,Outline=2'"
        '[v]')
    subprocess.run(['ffmpeg','-y','-loglevel','warning','-i','overview.mp4','-i','agents.mp4',
                    '-filter_complex',filters,'-map','[v]','-an','-c:v','libx264',
                    '-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags',
                    '+faststart','piloto_marciano.mp4'],cwd=OUT,check=True)


if __name__ == '__main__':
    main()
