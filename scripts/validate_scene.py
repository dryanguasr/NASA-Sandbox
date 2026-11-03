#!/usr/bin/env python3
"""Offline checks. SDF parsing is not a Gazebo dynamics test."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
IDS = {"human_1", "human_2", "drone_1", "drone_2", "rover_1", "rover_2"}
MODELS = {"astronaut", "scout_rover", "scout_drone", "mars_terrain"}


def validate():
    root = ET.parse(ROOT/"worlds/mars_sandbox.sdf").getroot()
    world = root.find("world")
    assert world is not None and world.attrib["name"] == "mars_sandbox"
    assert world.findtext("gravity") == "0 0 -3.71"
    manifest = json.loads((ROOT/"data/scenario.json").read_text())
    assert manifest["frame"] == "LOCAL_ENU_SYNTHETIC"
    assert manifest["terrain"]["validated_nasa_data"] is False
    agents = manifest["agents"]
    assert len(agents) == 6 and {a["id"] for a in agents} == IDS
    assert {kind: sum(a["kind"]==kind for a in agents)
            for kind in ("human","rover","drone")} == {"human":2,"rover":2,"drone":2}
    includes = {i.findtext("name"):i for i in world.findall("include")}
    assert set(includes) == IDS | {"mars_terrain"}
    for a in agents:
        inc = includes[a["id"]]
        assert inc.findtext("uri") == "model://" + a["model"]
        pose = list(map(float, inc.findtext("pose").split()))
        assert len(pose) == 6 and all(abs(x-y)<1e-6 for x,y in zip(pose,a["pose"]))
        assert a["topic"] == "/model/" + a["id"] + "/cmd_vel"
    for name in MODELS:
        path=ROOT/"models"/name
        assert (path/"model.config").is_file() and (path/"model.sdf").is_file()
        ET.parse(path/"model.config")
        ET.parse(path/"model.sdf")
    mesh=(ROOT/"models/mars_terrain/meshes/terrain.obj").read_text()
    grid=(ROOT/"data/terrain_grid.csv").read_text()
    assert sum(line.startswith("v ") for line in mesh.splitlines()) == 961
    assert sum(line.startswith("f ") for line in mesh.splitlines()) == 1800
    assert len(grid.splitlines()) == 962
    rover=ET.parse(ROOT/"models/scout_rover/model.sdf").getroot()
    drive=next(p for p in rover.findall(".//plugin")
               if p.get("name") == "gz::sim::systems::DiffDrive")
    assert len(drive.findall("left_joint")) == 2
    assert len(drive.findall("right_joint")) == 2
    print("OK: 2 humans, 2 drones, 2 rovers; valid XML and mesh")


if __name__ == "__main__":
    validate()
