#!/usr/bin/env python3
"""Deterministic synthetic terrain OBJ + height grid; no NASA data."""
from pathlib import Path
import argparse
import math

ROOT = Path(__file__).resolve().parents[1]
MESH = ROOT / "models/mars_terrain/meshes/terrain.obj"
GRID = ROOT / "data/terrain_grid.csv"
MIN, MAX, STEP = -45, 45, 3
N = (MAX - MIN) // STEP + 1


def crater(x, y, cx, cy, r, depth, rim, pad):
    d = (x-cx)**2 + (y-cy)**2
    rr, outer = r*r, (r+pad)**2
    if d <= rr:
        return -(depth*(rr-d)//rr)
    return rim*(outer-d)//(outer-rr) if d < outer else 0


def height_mm(x, y):
    return (2*(x+45)+(y+45)+4*((x-2*y+500)%32)
            +max(0, 330-16*abs(y-int(x/3)-12))
            +crater(x,y,15,12,12,1400,240,6)
            +crater(x,y,-18,21,9,1000,170,6))


def m(n):
    return ("-" if n < 0 else "") + f"{abs(n)//1000}.{abs(n)%1000:03d}"


def generate():
    mesh = ["# NASA-Sandbox: local SYNTHETIC terrain; not derived from NASA data\n",
            "o martian_test_terrain\n"]
    grid = ["x_m,y_m,height_m\n"]
    for x in range(MIN, MAX+1, STEP):
        for y in range(MIN, MAX+1, STEP):
            z = m(height_mm(x,y))
            mesh.append(f"v {x} {y} {z}\n")
            grid.append(f"{x},{y},{z}\n")
    vertices = [(x, y, height_mm(x,y)/1000)
                for x in range(MIN, MAX+1, STEP)
                for y in range(MIN, MAX+1, STEP)]
    normal_index = 0
    for ix in range(N-1):
        for iy in range(N-1):
            a = ix*N+iy+1
            b,c,d = a+N, a+1, a+N+1
            for face in ((a,b,c), (b,d,c)):
                p,q,r = (vertices[i-1] for i in face)
                u,v = ([q[i]-p[i] for i in range(3)],
                       [r[i]-p[i] for i in range(3)])
                n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2],
                     u[0]*v[1]-u[1]*v[0])
                length = math.sqrt(sum(t*t for t in n))
                mesh.append("vn " + " ".join(f"{t/length:.9f}" for t in n) + "\n")
                normal_index += 1
                mesh.append("f " + " ".join(f"{i}//{normal_index}" for i in face) + "\n")
    return {MESH: "".join(mesh), GRID: "".join(grid)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    opts = parser.parse_args()
    for path, contents in generate().items():
        if opts.check:
            if not path.exists() or path.read_text(encoding="utf-8") != contents:
                parser.error(f"Asset missing/out of date: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
            print("Generated", path.relative_to(ROOT))
    if opts.check:
        print("OK: terrain OBJ and CSV match generator")


if __name__ == "__main__":
    main()
