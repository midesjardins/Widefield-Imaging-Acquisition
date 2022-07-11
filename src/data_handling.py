import numpy as np
import matplotlib.pyplot as plt
import os
import json
from src.signal_generator import digital_square
import scipy.signal as signal

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

def frames_acquired_from_camera_signal(camera_signal):
    dy = np.diff(camera_signal)
    indices = np.where(abs(dy) > 0)[0][1::2]
    y_values = np.zeros(len(camera_signal))
    try:
        for index in indices:
            y_values[index:] += 1
    except Exception:
        pass
    return y_values

def average_baseline(frame_list, light_count=1, start_index=0):
    try:
        baselines = []
        for light_index in range(light_count):
            baselines.append(np.mean(np.array(frame_list[(light_count-start_index)%light_count+light_index::light_count]), axis=0))
    except Exception as err:
        print("Baseline Error")
        print(err)
    return baselines

def get_baseline_frame_indices(baseline_indices, frames_acquired):
    print(baseline_indices)
    print(len(frames_acquired))
    list_of_indices = []
    for index in baseline_indices:
        list_of_indices.append([frames_acquired[index[0]],frames_acquired[index[1]]])
    return list_of_indices

def map_activation(frames, baseline):
    return np.array(frames) - np.array([baseline])

def find_similar_frame(frame, baselines):
    means = []
    for baseline in baselines:
        means.append(np.mean(abs(frame-baseline)))
    return means