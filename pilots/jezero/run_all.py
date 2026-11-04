"""One command: validate/import data, execute mission, compare, report and export."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PILOT=ROOT/'pilots/jezero'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refresh-data',action='store_true',help='Re-import the published orbital rasters')
    a=p.parse_args()
    def run(*args):subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,check=True)
    if a.refresh_data or not (ROOT/'data/jezero/terrain.npz').exists():
        run(PILOT/'import_data.py')
    run('-m','pytest',PILOT/'test_mission.py','-q')
    run(PILOT/'mission.py')
    run(PILOT/'mission.py','--policy','nearest_greedy','--out','evidence/jezero_baseline')
    run(PILOT/'benchmark.py')
    run(PILOT/'present.py')
    run(PILOT/'export_gazebo.py')
    print('Completed. Open evidence/jezero/viewer.html and evidence/jezero/report.md.')
    print('Gazebo export is a kinematic replay, not a closed-loop dynamics run.')


if __name__=='__main__':main()
