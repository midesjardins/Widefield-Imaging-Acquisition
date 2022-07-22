import numpy as np

array = np.random.randint(0, 4096, (150, 200, 200))
np.save("/Users/maxence/Desktop/bobby/data/0.npy", array)