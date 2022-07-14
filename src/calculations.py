import numpy as np
import matplotlib.pyplot as plt
import os
import json
import time


def shrink_array(array, extents):
    """Reduce the dimensions of frames to match ROI and return a list of frames"""
    return np.array(array)[
        :, round(extents[2]) : round(extents[3]), round(extents[0]) : round(extents[1])
    ]


def get_array(directory):
    """ Get array from NPY file """
    return np.array(np.load(directory))


def get_dictionary(directory):
    """ Get dictionary from json file """
    with open(directory, "r") as file:
        dictionary = json.load(file)
    return dictionary


def find_rising_indices(array):
    """ Find indices of rising edges in an array """
    dy = np.diff(array)
    return np.concatenate(([0], np.where(dy == 1)[0][1::2] + 1))


def create_complete_stack(first_stack, second_stack):
    """ Create a stack with the first stack as the first half and the second stack as the second half """
    array = []
    for new_array in first_stack:
        array.append(new_array)
    for new_array in second_stack:
        array.append(new_array)
    return np.stack(array)


def reduce_stack(stack, indices):
    """ Reduce the stack to only include the frames at the given indices """
    return stack[:, indices]


def separate_images(lights, frames):
    """ Separate images into different light channels """
    separated_images = []
    for index in range(len(lights)):
        separated_images.append(frames[index :: len(lights), :, :])
    return separated_images


def separate_vectors(lights, vector):
    """ Separate vectors into different light channels """
    separated_vectors = []
    for index in range(len(lights)):
        separated_vectors.append(vector[:, index :: len(lights)])
    return separated_vectors


def extract_from_path(path):
    """ Extract lights, frames and vector files from a given path """
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
    """ Extend the light signal to be wider the camera signal """
    camera_dy = np.diff(camera)
    camera_indices = np.where(abs(camera_dy) > 0)[0]
    difference = camera_indices[1] - camera_indices[0]
    extend = round(0.4 * difference)
    signal_list = []
    for signal in lights:
        dy = np.diff(signal)
        differential_indices = np.where(abs(dy) > 0)[0]
        new_signal = np.copy(signal)
        for index in differential_indices:
            new_signal[index - extend : index + extend] = True
        signal_list.append(new_signal)
    return np.stack(signal_list)


def frames_acquired_from_camera_signal(camera_signal):
    """ Generate an array of frames acquired from the camera signal at each timepoint """
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
    """ Average the baselines of a list of frames """
    try:
        baselines = []
        for light_index in range(light_count):
            baselines.append(
                np.mean(
                    np.array(
                        frame_list[
                            (light_count - start_index) % light_count
                            + light_index :: light_count
                        ]
                    ),
                    axis=0,
                )
            )
    except Exception as err:
        print("Baseline Error")
        print(err)
    return baselines


def get_baseline_frame_indices(baseline_indices, frames_acquired):
    """ Get the start and end indices of the baseline in terms of frames acquired """
    print(baseline_indices)
    print(len(frames_acquired))
    list_of_indices = []
    for index in baseline_indices:
        list_of_indices.append([frames_acquired[index[0]], frames_acquired[index[1]]])
    return list_of_indices


def map_activation(frames, baseline):
    """ Map the activation of each frame to the baseline """
    return np.array(frames) - np.array([baseline])


def timeit(method):
    """ Time the execution of a method """

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print("%r  %2.2f ms" % (method.__name__, (te - ts) * 1000))
        return result

    return timed
