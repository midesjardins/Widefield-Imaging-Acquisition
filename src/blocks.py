import time
import numpy as np
import matplotlib.pyplot as plt
from src.signal_generator import make_signal

class Stimulation:
    def __init__(self, daq, duration, width=0, pulses=0, jitter=0, frequency=0, duty=0.1, delay=0, pulse_type='square', framerate=30):
        self.daq = daq
        self.duration = duration
        self.type = pulse_type
        self.delay = delay
        self.pulses = pulses
        self.width = width
        self.duty = duty
        self.jitter = jitter
        self.freq = frequency
        self.framerate = framerate
        self.time_delay = np.linspace(0, delay, delay*3000)
        self.time = np.linspace(0, duration, duration*3000)
        self.stim_signal = make_signal(self.time, self.type, self.width, self.pulses, self.jitter, self.freq, self.duty)
        self.empty_signal = np.zeros(len(self.time_delay))

    def run(self, last = False):
        self.stim_signal = make_signal(self.time, self.type, self.width, self.pulses, self.jitter, self.freq, self.duty)
        self.daq.launch(self, last)

class Blocks:
    def __init__(self, data, delay=0, iterations=1):
        self.data = data
        self.iterations = iterations
        self.delay = delay

    def run(self, last=False):
        for iteration in range(self.iterations):
            for item in self.data:
                if iteration + 1 != self.iterations:
                    item.run()
                else:
                    item.run(last=True)
            if iteration + 1 != self.iterations:
                time.sleep(self.delay)