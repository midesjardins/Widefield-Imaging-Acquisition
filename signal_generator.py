from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
import random

def square_signal(time_values, frequency, signal_width):
    duty_cycle = 1 - signal_width * frequency
    return np.array(signal.square(2 * np.pi * frequency * time_values, duty_cycle)).clip(min=0)

def random_square(time_values, pulses, width, jitter):
    signal = np.zeros(len(time_values))
    buffer = (float(width)+jitter, float(time_values[-1]-width-jitter))
    uniform_distribution = np.linspace(*buffer, pulses)
    random_numbers = np.around(np.random.uniform(-jitter, jitter, pulses), 3)
    randomized_distribution = uniform_distribution + random_numbers
    for value in randomized_distribution:
        signal[(time_values>value-width/2) & (time_values<value+width/2)] = 5
    return signal

def generate_signal(time, type, width, pulses, jitter, frequency):
    if type == 'square':
        return square_signal(time, frequency, width)
    if type == 'random-square':
        return random_square(time, pulses, width, jitter)