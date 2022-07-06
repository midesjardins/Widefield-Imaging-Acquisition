import numpy as np
import matplotlib.pyplot as plt
import os
import json
from signal_generator import digital_square

def shrink_array(array, extents):
    """Reduce the dimensions of frames to match ROI and return a list of frames"""
    return np.array(array)[:,round(extents[2]):round(extents[3]), round(extents[0]):round(extents[1])]

def get_array(directory):
    return np.array(np.load(directory))

def get_dictionary(directory):
    with open(directory, 'r') as file:
        dictionary = json.load(file)
    return dictionary

def init():
    figure = plt.imshow(np.random.random([1024, 1024]))
    plt.ion()
    plt.draw()
    return figure

def animate(array, figure):
    maximum = np.max(array)
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
    return np.concatenate(([0], np.where(dy == 1)[0][1::2]+1))

def create_complete_stack(first_stack, second_stack):
    array = []
    for new_array in first_stack:
        array.append(new_array)
    for new_array in second_stack:
        array.append(new_array)
    return np.stack(array)

def reduce_stack(stack, indices):
    return stack[:, indices]

def separate_images(lights, frames):
    separated_images = []
    for index in range(len(lights)):
        separated_images.append(frames[index::len(lights),:,:])
    return separated_images

def extract_from_path(path):
    files_list = os.listdir(path)
    for file_name in files_list:
        if "-data" in file_name:
            frames = get_array(os.path.join(path, file_name))
        if "-metadata" in file_name and "json" in file_name:
            lights = get_dictionary(os.path.join(path, file_name))["Lights"]
    return (lights, frames)


def separate_vectors(lights, vector):
    separated_vectors = []
    for index in range(len(lights)):
        separated_vectors.append(vector[:,index::len(lights)])
    return separated_vectors

def extract_from_path(path):
    files_list = os.listdir(path)
    for file_name in files_list:
        if "-data" in file_name:
            frames = get_array(os.path.join(path, file_name))
        if "-metadata" in file_name and "json" in file_name:
            lights = get_dictionary(os.path.join(path, file_name))["Lights"]
        if "-signal_data" in file_name:
            vector = get_array(os.path.join(path, file_name))
    return (lights, frames, vector)


def extend_light_signal(lights, camera):
    camera_dy = np.diff(camera)
    camera_indices = np.where(abs(camera_dy) > 0)[0]
    difference = camera_indices[1] - camera_indices[0]
    extend = round(0.4*difference)
    signal_list = []
    for signal in lights:
        dy = np.diff(signal)
        differential_indices = np.where(abs(dy) > 0)[0]
        new_signal = np.copy(signal)
        for index in differential_indices:
            new_signal[index-extend:index+extend] = True
        signal_list.append(new_signal)
    return np.stack(signal_list)

"""x = np.linspace(0,10,1000)
red = digital_square(x, 1, 0.2, 0)
green = digital_square(x, 1, 0.2, 50)
camera  = np.max(np.vstack([red, green]), axis=0)
plt.plot(x, red)
plt.plot(x, green)
plt.plot(x, camera, alpha=0.5)
signals = extend_light_signal([red, green], camera)
for signal in signals:
    plt.plot(x, signal)
plt.show()"""


#lights = ["ir", "red", "green", "blue"]
#frames = np.array([[[1,2,3],[4,5,6],[7,8,9]],[[10,11,12],[13,14,15],[16,17,18]],[[19,20,21],[21,22,23],[24,25,26]]])
#reduced_stack = np.array([[1,2,3],[4,5,6],[7,8,9],[10,11,12]])

#print(separate_images(lights, frames, reduced_stack))

#plot_multiple_arrays(np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/stim_signal.npy"))
#indices = find_rising_indices(np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/all_signals.npy")[-1])
#stack = create_complete_stack(np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/all_signals.npy"), np.load("/Users/maxence/chul/Widefield-Imaging-Acquisition/stim_signal.npy"))
#print(len(stack[0]))
#reduced_stack = reduce_stack(stack, indices)
#print(len(reduced_stack[0]))

#array = get_array("C:\\Users\\ioi\\Documents\\GitHub\\Widefield-Imaging-Acquisition\\data\\First Real Test\\1654112346.2327678-data.npy")
#figure = init()
#animate(array, figure)