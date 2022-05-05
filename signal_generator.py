from scipy import signal
import numpy as np
import matplotlib.pyplot as plt

def square_signal(time_values, frequency, signal_width):
    duty_cycle = 1 - signal_width * frequency
    return np.array(signal.square(2 * np.pi * frequency * time_values, duty_cycle)).clip(min=0)