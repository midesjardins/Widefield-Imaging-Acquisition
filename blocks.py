import time
import numpy as np
import matplotlib.pyplot as plt
from signal_generator import make_signal

class Stimulation:
    def __init__(self, duration, width, pulses=0, jitter=0, frequency=0, delay=0, pulse_type='square'):
        self.duration = duration
        self.type = pulse_type
        self.delay = delay
        self.pulses = pulses
        self.width = width
        self.jitter = jitter
        self.freq = frequency
        self.time_delay = np.linspace(0, delay, delay*1000)
        self.time = np.linspace(0, duration, duration*1000)
        self.signal = make_signal(self.time, self.type, self.width, self.pulses, self.jitter, self.freq)
        self.empty_signal = np.zeros(len(self.time_delay))
    
    def randomize_signal(self):
        self.signal = make_signal(self.time, self.type, self.width, self.pulses, self.jitter, self.freq)

    def run(self, last=False):
        self.randomize_signal()
        if last is False:
            plt.plot(np.concatenate((self.time,self.time_delay + self.duration)), np.concatenate((self.signal, self.empty_signal)))
        else:
            plt.plot(self.time, self.signal)

        plt.show()
        plt.clf()

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