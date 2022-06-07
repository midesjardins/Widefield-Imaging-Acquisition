from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
import time

def square_signal(time_values, frequency, duty_cycle, delay_frames=0):
    time_start = time.time()
    pulses = 5*np.array(signal.square(2 * np.pi * frequency * time_values, duty_cycle)).clip(min=0)
    if delay_frames == 0:
        #print(f"numpy time: {time.time()-time_start}")
        return pulses
    #print(f"numpy time: {time.time()-time_start}")
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


"""FPS = 20
NUMBER_OF_LIGHTS = 4
EXPOSURE_TIME= 0.1
time_values = np.linspace(0,1,3000)
first_signal = digital_square(time_values,FPS/NUMBER_OF_LIGHTS,EXPOSURE_TIME,0)
second_signal = digital_square(time_values,FPS/NUMBER_OF_LIGHTS,EXPOSURE_TIME,int(1*3000/FPS))
third_signal = digital_square(time_values,FPS/NUMBER_OF_LIGHTS,EXPOSURE_TIME,int(2*3000/FPS))
fourth_signal = digital_square(time_values,FPS/NUMBER_OF_LIGHTS,EXPOSURE_TIME,int(3*3000/FPS))
plt.plot(time_values, first_signal)
plt.plot(time_values, second_signal)
plt.plot(time_values, third_signal)
plt.plot(time_values, fourth_signal)
plt.show()"""