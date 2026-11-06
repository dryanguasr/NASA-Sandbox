"""Screen verified HiRISE terrain offline for a reproducible natural detour case."""
import argparse
import json
from pathlib import Path
import math

import numpy as np
from scipy.ndimage import binary_erosion, label, median_filter

from mission import Grid, astar, load_data, slopes


def passable(z,limit):
    """Match the planner's slope and adjacent-cell step tests."""
    jump = np.zeros_like(z)
    for axis in (0,1):
        diff = np.abs(np.diff(z,axis=axis))
        first = (slice(None,-1),slice(None)) if axis==0 else (slice(None),slice(None,-1))
        second = (slice(1,None),slice(None)) if axis==0 else (slice(None),slice(1,None))
        jump[first] = np.maximum(jump[first],diff)
        jump[second] = np.maximum(jump[second],diff)
    safe = (slopes(z,4)<=limit) & (jump<=4*math.tan(math.radians(limit)))
    safe[[0,-1],:] = False
    safe[:,[0,-1]] = False
    return safe


def line_cells(grid,a,b):
    return list(dict.fromkeys(grid.rc(p) for p in np.linspace(a,b,100)))


def screen(source,out):
    from pyproj import CRS, Transformer

    dem,_,_,meta = load_data(source)
    grid = Grid(32,4)
    margin = np.ones((3,3),bool)
    best = None
    rng = np.random.default_rng(21)
    for r in range(0,len(dem)-31,8):
        for c in range(0,len(dem)-31,8):
            z = dem[r:r+32,c:c+32]
            steepness = slopes(z,4)
            relief = float(np.ptp(z))
            if relief<15 or steepness.max()<26:
                continue
            rover = passable(z,14)
            rover &= slopes(median_filter(z,size=3,mode='nearest'),4)<=16
            rover[[1,-2],:] = False
            rover[:,[1,-2]] = False
            human = passable(z,22)
            safe = binary_erosion(rover,structure=margin)
            groups,_ = label(rover)
            options = np.argwhere(safe)
            # The aerial-only marker needs a strongly hazardous neighborhood.
            danger = np.argwhere(binary_erosion(steepness>24,structure=margin))
            danger = [tuple(a) for a in danger if 3<=a[0]<=28 and 3<=a[1]<=28]
            if len(options)<40 or not danger:
                continue
            hazard = max(danger,key=lambda cell:steepness[cell])
            for _ in range(30):
                ar,br = [tuple(x) for x in options[rng.choice(len(options),2,replace=False)]]
                if groups[ar]!=groups[br]:
                    continue
                a,b = grid.xy(ar),grid.xy(br)
                dist = math.dist(a,b)
                if not 35<=dist<=90:
                    continue
                straight = line_cells(grid,a,b)
                if sum(not human[cell] for cell in straight)<3:
                    continue
                route = astar(grid,z,rover,a,b)
                if not route or not dist*1.15<=route[1]<=dist*2.5:
                    continue
                home_cells = [ar]
                for p in sorted(map(tuple,options),key=lambda x:math.dist(ar,x)):
                    if groups[p]==groups[ar] and 2<=math.dist(ar,p)<=6 and all(math.dist(p,h)>=2 for h in home_cells):
                        home_cells.append(p)
                        if len(home_cells)==4:
                            break
                if len(home_cells)<4:
                    continue
                if any(all(human[cell] for cell in line_cells(grid,grid.xy(h),b)) for h in home_cells):
                    continue
                score = min(route[1]/dist,1.65) + min(relief,35)/60
                if not best or score>best[0]:
                    best = score,r,c,home_cells,br,hazard,dist,route[1],relief
    if not best:
        raise RuntimeError('No natural detour with stable launch area in this source crop')
    _,r,c,homes,target,hazard,dist,route,relief = best
    side = meta['side_m']
    x,y = -side/2+(c+16)*4,side/2-(r+16)*4
    crs = CRS.from_wkt(meta['local_crs_wkt'])
    lon,lat = Transformer.from_crs(crs,crs.geodetic_crs,always_xy=True).transform(x,y)
    xy = lambda rc: grid.xy(rc).tolist()
    result = {'lat':lat,'lon':lon,'reference_search_sha256':meta['terrain_sha256'],
              'search_window_rc':[r,c],'relief_search_m':relief,
              'screened_rover_direct_m':dist,'screened_rover_route_m':route,
              'homes':{name:xy(rc) for name,rc in zip(
                  ('rover_1','rover_2','human_1','human_2','drone_1','drone_2'),homes+homes[:2])},
              'sites':{'S1':xy(target),'S2':xy(hazard)}}
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('output',type=Path)
    a = p.parse_args()
    screen(a.source,a.output)
