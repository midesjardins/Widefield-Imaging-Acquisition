from scipy import signal
import numpy as np

def square_signal(time_values, frequency, duty_cycle, delay_frames=0):
    pulses = 5*np.array(signal.square(2 * np.pi * frequency * time_values, duty_cycle)).clip(min=0)
    if delay_frames == 0:
        return pulses
    return np.concatenate((np.zeros(delay_frames), pulses))[:-delay_frames]

def digital_square(time_values, frequency, duty_cycle, delay_frames=0):
    pulses = np.ma.make_mask(np.array(signal.square(2 * np.pi * frequency * time_values, duty_cycle)).clip(min=0))
    if delay_frames == 0:
        return pulses
    return np.concatenate((np.full(delay_frames, False), pulses))[:-delay_frames]

def random_square(time_values, pulses, width, jitter):
    pulse_signal = np.zeros(len(time_values))
    buffer = (float(width)+jitter, float(time_values[-1]-width-jitter))
    uniform_distribution = np.linspace(*buffer, pulses)
    random_numbers = np.around(np.random.uniform(-jitter, jitter, pulses), 3)
    randomized_distribution = uniform_distribution + random_numbers
    for value in randomized_distribution:
        pulse_signal[(time_values>value-width/2) & (time_values<value+width/2)] = 5
    return pulse_signal

def make_signal(time, pulse_type, width, pulses, jitter, frequency, duty):
    if pulse_type == 'square':
        return square_signal(time, frequency, duty)
    if pulse_type == 'random-square':
        return random_square(time, pulses, width, jitter)