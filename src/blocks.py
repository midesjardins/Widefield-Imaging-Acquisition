import time
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from .signal_generator import make_signal 

class Stimulation:
    def __init__(self, daq, duration, width=0, pulses=0, jitter=0, frequency=0, duty=0.1, delay=0, pulse_type='square', name=""):
        self.daq = daq
        self.duration = duration
        self.type = pulse_type
        self.delay = delay
        self.pulses = pulses
        self.width = width
        self.duty = duty
        self.jitter = jitter
        self.freq = frequency
        self.name = name
        self.time_delay = np.linspace(0, delay, delay*3000)
        self.time = np.linspace(0, duration, duration*3000)
        self.stim_signal = make_signal(self.time, self.type, self.width, self.pulses, self.jitter, self.freq, self.duty)
        self.empty_signal = np.zeros(len(self.time_delay))
        self.exp = None

    def __str__(self, indent=""):
        if self.type == "random-square":
            return indent+f"{self.name} --- Duration: {self.duration}, Pulses: {self.pulses}, Width: {self.width}, Jitter: {self.jitter}, Delay: {self.delay}"
        if self.type == "square":
            return indent+f"{self.name} --- Duration: {self.duration}, Frequency: {self.freq}, Duty: {self.duty}, Delay: {self.delay}"
        else:
            return f"there appears to be a weird type, which goes like this {self.type}"
    def run(self, exp):
        print(f"stim ran")
        self.exp = exp
        self.stim_signal = make_signal(self.time, self.type, self.width, self.pulses, self.jitter, self.freq, self.duty)
        self.daq.launch(self)

class Block:
    def __init__(self, name, data, delay=0, iterations=1):
        self.name = name
        self.data = data
        self.iterations = iterations
        self.delay = delay
        self.exp = None

    def __str__(self, indent=""):
        stim_list = []
        for iteration in range(self.iterations):
            stim_list.append(indent + self.name + f" ({iteration+1}/{self.iterations})")
            for item in self.data:
                stim_list.append(item.__str__(indent=indent+"   "))
        return "\n".join(stim_list)

    def run(self, exp):
        self.exp = exp
        for iteration in range(self.iterations):
            for item in self.data:
                item.run(self.exp)
                time.sleep(self.delay)

class Experiment:
    def __init__(self, blocks, framerate, exposition, mouse_id, directory, daq):
        self.blocks = blocks
        self.framerate = framerate
        self.exposition = exposition
        self.mouse_id = mouse_id
        self.directory = directory
        self.daq = daq
    
    def start(self, save):
        print("experiment saved")
        self.blocks.run(self)
        if save is True:
            self.save()
            self.daq.camera.save(self.directory)

    def save(self):
        with open(f'{self.directory}/experiment-metadata.txt', 'w') as file:
            file.write(f"Blocks\n{self.blocks}\n\nFramerate\n{self.framerate}\n\nExposition\n{self.exposition}\n\nMouse ID\n{self.mouse_id}")