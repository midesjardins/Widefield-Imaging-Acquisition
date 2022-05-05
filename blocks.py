import time
import random
import numpy as np
from signal_generator import generate_signal
import matplotlib.pyplot as plt

class stimulation:
    def __init__(self, duration, width, pulses=0, jitter=0, frequency=0, type='square'):
        self.duration = duration
        self.pulses = pulses
        self.width = width
        self.jitter = jitter
        self.frequency = frequency
        self.time = np.linspace(0, duration, duration*1000)
        self.signal = generate_signal(self.time, type, width, pulses, jitter, frequency)

    def __str__(self):
        return str(self.data)

    def run(self):
        plt.plot(self.time, self.signal)
        plt.show()



class blocks:
    def __init__(self, data, delay=0, iterations=1, jitter=0):
        self.data = data
        self.iterations = iterations
        self.delay = delay
        self.jitter = jitter

    def run(self):
        for item in self.data:
                item.run()
                print(self.delay + round(random.random(), 2) * self.jitter)
                time.sleep(self.delay + round(random.random(), 2) * self.jitter)