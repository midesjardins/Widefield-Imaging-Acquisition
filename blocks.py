import time
import random
import numpy as np
from signal_generator import generate_signal
import matplotlib.pyplot as plt

class stimulation:
    def __init__(self, duration, width, pulses=0, jitter=0, frequency=0, delay=0, type='square'):
        self.duration = duration
        self.type = type
        self.delay = delay
        self.pulses = pulses
        self.width = width
        self.jitter = jitter
        self.frequency = frequency
        self.time_delay = np.linspace(0, delay, delay*1000)
        self.time = np.linspace(0, duration, duration*1000)
        self.empty_signal = np.zeros(len(self.time_delay))
    def __str__(self):
        return str(self.data)
    
    def randomize_signal(self):
        self.signal = generate_signal(self.time, self.type, self.width, self.pulses, self.jitter, self.frequency)

    def run(self, last=False):
        self.randomize_signal()
        if last is False:
            plt.plot(np.concatenate((self.time,self.time_delay + self.duration)), np.concatenate((self.signal, self.empty_signal)))
        else:
            plt.plot(self.time, self.signal)

        plt.show()
        plt.clf()



class blocks:
    def __init__(self, data, delay=0, iterations=1):
        self.data = data
        self.iterations = iterations
        self.delay = delay

    def run(self, last=False):
        for iteration in range(self.iterations):
            for index, item in enumerate(self.data):
                print(f'iteration={iteration}')
                print(f'index={index}')
                print(f'self.iterations={self.iterations}')
                if iteration + 1 != self.iterations:
                    item.run()
                else:
                    item.run(last=True)
            if iteration + 1 != self.iterations:
                time.sleep(self.delay)

a = stimulation(100, 4, 4, 1, delay=200, type='random-square')
b = stimulation(200, 4, 8, 1, delay=50, type='random-square')
c = blocks([a], iterations=2)
d = blocks([b], iterations=3)
e = blocks([c,d], delay=2, iterations=2)
e.run()