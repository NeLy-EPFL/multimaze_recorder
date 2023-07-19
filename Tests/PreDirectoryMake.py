from pathlib import Path
from PIL import Image
import json

# Create arena and corridor folders

folder = Path("/home/matthias/Videos/SpeedTest2/")

arenas_folder = Path("/mnt/labserver/DURRIEU_Matthias/Experimental_data/MultiMazeRecorder/Videos/").joinpath(folder.name)
arenas_folder.mkdir(parents=True, exist_ok=True)
for arena in range(1, 10):
    arena_folder = arenas_folder.joinpath(f"arena{arena}")
    arena_folder.mkdir(parents=True, exist_ok=True)
    for corridor in range(1, 7):
        corridor_folder = arena_folder.joinpath(f"corridor{corridor}")
        corridor_folder.mkdir(parents=True, exist_ok=True)