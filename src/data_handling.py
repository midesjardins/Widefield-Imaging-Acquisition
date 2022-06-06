import numpy as np
import matplotlib.pyplot as plt
import time
from array2gif import write_gif
from IPython.display import HTML
import matplotlib.animation as animation

def shrink_array(array, extents):
    return array[:,extents[0]:extents[1], extents[2]:extents[3]]

def get_array(directory):
    return np.load(directory)

def init():
    figure = plt.imshow(np.random.random([1024, 1024]))
    plt.ion()
    plt.draw()
    return figure

def animate(array, figure):
    #figure = plt.imshow(array[0], cmap="binary_r")
    #plt.ion()
    maximum = np.max(array)
    print(maximum)
    figure.set(clim=[0,maximum])
    for frame in array:
        figure.set_array(frame)
        plt.draw()
        plt.pause(0.2)

array = get_array("C:\\Users\\ioi\\Documents\\GitHub\\Widefield-Imaging-Acquisition\\data\\First Real Test\\1654112346.2327678-data.npy")
figure = init()
animate(array, figure)