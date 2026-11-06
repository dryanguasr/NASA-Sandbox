"""Scenario fixtures for Jezero pilots 5–7, used by the simulator and evaluator."""
from dataclasses import dataclass
import json
import xml.etree.ElementTree as ET

from export_gazebo import ROOT, text

RAVINE_GOAL = (30,-22)
WALL_X = 2
WALL_EDGE = 1.9
OPEN_END = 22
TIMED_APPEARANCE_S = 24.
FOV_GROUND = 1.32
GROUND_SCOUT = (-10,-42)


@dataclass(frozen=True)
class Site:
    name: str
    xy: tuple
    color: tuple


def belva_fixture():
    return json.loads((ROOT/'data/jezero_live/belva/scenario.json').read_text())


def sites_for(pilot):
    if pilot==7:
        sites = belva_fixture()['sites']
        return [Site('S1',tuple(sites['S1']),(0,1,0)),
                Site('S2',tuple(sites['S2']),(0,0,1))]
    if pilot==5:
        return [Site('S1',RAVINE_GOAL,(0,1,0))]
    return [Site('S1',(-26,-14),(0,1,0)),Site('S2',(22,-22),(0,0,1)),
            Site('S3',(26,22),(1,0,1)),Site('S4',(-26,-42),(0,1,1))]


def fixtures(world,out,pilot,scenario,ground,box):
    if pilot==5:
        end = 62 if scenario=='sealed' else OPEN_END
        for index,lo in enumerate(range(-62,end,4)):
            y = lo+2
            model = box(f'experimental_scarp_{index}',(WALL_X,y,ground(WALL_X,y)+1.6),
                        (2*WALL_EDGE,4.04,7.),(1,0,0),True)
            world.append(model)
    elif pilot==6:
        x,y = sites_for(6)[-1].xy
        # The roof is opaque to both cameras. A shallow overhang shelters the ground-only target.
        world.append(box('fictional_overhang',(x,y,ground(x,y)+2.6),(9,9,.45),(.42,.30,.20),True))
    for site in sites_for(pilot):
        x,y = site.xy
        model = box(f'fictional_site_{site.name}',(x,y,ground(x,y)+.4),(2.3,2.3,.8),site.color,False)
        if pilot==6 and scenario=='emergent' and site.name=='S3':
            (out/'late_site.sdf').write_text('<sdf version="1.10">'+ET.tostring(model,encoding='unicode')+'</sdf>')
        else:
            world.append(model)


def inside_wall(x,y,scenario,margin=0.):
    top = 62 if scenario=='sealed' else OPEN_END
    return abs(x-WALL_X)<WALL_EDGE+margin and -62-margin<y<top+margin
