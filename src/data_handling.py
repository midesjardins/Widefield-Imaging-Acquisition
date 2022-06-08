import numpy as np
import matplotlib.pyplot as plt
import time
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
    maximum = np.max(array)
    print(maximum)
    figure.set(clim=[0,maximum])
    for frame in array:
        figure.set_array(frame)
        plt.draw()
        plt.pause(0.2)

def plot_multiple_arrays(arrays_list):
    for array in arrays_list:
        plt.plot(array)
        plt.show()
        plt.clf()

def find_rising_indices(array):
    dy = np.diff(array)
    return np.concatenate(([0], np.where(dy == 1)[0][1::2]))

def create_complete_stack(first_stack, second_stack):
    array = []
    for new_array in first_stack:
        array.append(new_array)
    for new_array in second_stack:
        array.append(new_array)
    return np.stack(array)

def reduce_stack(stack, indices):
    return stack[:, indices]

#plot_multiple_arrays(np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/stim_signal.npy"))
#indices = find_rising_indices(np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/all_signals.npy")[-1])
#stack = create_complete_stack(np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/all_signals.npy"), np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/stim_signal.npy"))
#print(len(stack[0]))
#reduced_stack = reduce_stack(stack, indices)
#print(len(reduced_stack[0]))

#array = get_array("C:\\Users\\ioi\\Documents\\GitHub\\Widefield-Imaging-Acquisition\\data\\First Real Test\\1654112346.2327678-data.npy")
#figure = init()
#animate(array, figure)