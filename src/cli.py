import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.data_handling import extract_from_path, separate_images, separate_vectors

path = sys.argv[1]
lights, frames, vector = extract_from_path(path)
arrays = separate_images(lights, frames)
vectors = separate_vectors(lights, vector)
for i, array in enumerate(arrays):
    print(f"Saving {lights[i].capitalize()} Channel...")
    np.save(os.path.join(path, f"{lights[i]}.npy"), array)
print("Extraction Done!")
