import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.data_handling import extract_from_path, separate_images

path = sys.argv[0]
lights, frames = extract_from_path(path)
arrays = separate_images(lights, frames)
for i, array in enumerate(arrays):
    print(f"Setting {lights[i].capitalize()} Light...")
    np.save(os.path.join(path, f"{lights[i]}.npy"), array)
print("Extraction Done!")
