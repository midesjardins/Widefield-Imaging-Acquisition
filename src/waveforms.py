import numpy as np
from scipy.signal import square


def square_signal(time, frequency, duty, heigth, delay=0):
    """Generate a square signal

    Args:
        time (array of float): The array of time values
        frequency (float): The frequency of the signal
        duty (float): The duty cycle of the signal
        delay (int, optional): The number of values by which to delay the signal. Defaults to 0.

    Returns:
        array of float: The generated signal
    """
    pulses = heigth * np.array(square(2 * np.pi * frequency * time, duty)).clip(min=0)
    if delay == 0:
        return pulses
    return np.concatenate((np.zeros(delay), pulses))[:-delay]


def digital_square(time, frequency, duty, delay=0):
    """Generate a digital square signal

    Args:
        time (array of float): The array of time values
        frequency (float): The frequency of the signal
        duty (float): The duty cycle of the signal
        delay (int, optional): The number of values by which to delay the signal. Defaults to 0.

    Returns:
        array of bool: The generated signal
    """
    pulses = np.ma.make_mask(
        np.array(square(2 * np.pi * frequency * time, duty)).clip(min=0)
    )
    if delay == 0:
        return pulses
    return np.concatenate((np.full(delay, False), pulses))[:-delay]


def random_square(time, pulses, width, jitter):
    """Generate a random square signal

    Args:
        time (array of float): The array of time values
        pulses (int): The number of pulses to generate
        width (float): The width of each individual pulse
        jitter (float): The random delay between each individual pulse

    Returns:
        array of float: The generated signal
    """
    pulse_signal = np.zeros(len(time))
    buffer = (float(width) + jitter, float(time[-1] - width - jitter))
    uniform_distribution = np.linspace(*buffer, pulses)
    random_numbers = np.around(np.random.uniform(-jitter, jitter, pulses), 3)
    randomized_distribution = uniform_distribution + random_numbers
    for value in randomized_distribution:
        pulse_signal[(time > value - width / 2) & (time < value + width / 2)] = 5
    return pulse_signal


def make_signal(time, pulse_type, width, pulses, jitter, frequency, duty, heigth):
    """" Generate a signal based on the given pulse type

    Args:
        time (array of float): The array of time values
        pulse_type (str): The type of pulse to generate
        width (float): The width of each individual pulse
        pulses (int): The number of pulses to generate
        jitter (float): The random delay between each individual pulse
        frequency (float): The frequency of the signal
        duty (float): The duty cycle of the signal

    Returns:
        array of float: The generated signal
    """
    if pulse_type == "square":
        return square_signal(time, frequency, duty, heigth)
    if pulse_type == "random-square":
        return random_square(time, pulses, width, jitter)
