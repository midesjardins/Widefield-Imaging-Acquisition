import nidaqmx
import time
from nidaqmx.constants import AcquisitionType
import numpy as np
from src.signal_generator import digital_square
from pylablib.devices import IMAQ
import re

signal_ajust = [
            [0, None, None, None], 
            [0, 4500, None, None], 
            [0, 3000, 6000, None], 
            [0, 2250, 4500, 6750]]


class Instrument:
    def __init__(self, port, daq_name):
        self.port = port
        self.daq_name = daq_name
        self.cam = None

class Camera(Instrument):
    def __init__(self, port, daq_name):
        super().__init__(port, daq_name)
        self.frames = []
        self.metadata = []
        self.daq = None

    def initialize(self, daq):
        self.daq = daq
        with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.icd') as file:
            lines = []
            for i, line in enumerate(file):
                if i == 2408:
                    lines.append(f"                                    Current ({self.daq.exp.framerate})")
                else:
                    lines.append(line)
        with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.icd', 'w') as file:
            file.write("".join(lines))
        self.cam = IMAQ.IMAQCamera(self.port)
        self.cam.setup_acquisition(mode="sequence", nframes=100)
        self.cam.set_roi(0,1024,0,1024)
        self.cam.start_acquisition()

    def loop(self, task):
        self.cam.read_multiple_images()
        while not task.is_task_done():
            self.cam.wait_for_frame()
            self.frames.append(self.cam.read_oldest_image())
            self.metadata.append({"time": time.time(), "daq": self.daq.read_metadata()})
        """for i in range(7):
            self.frames.append(self.cam.read_oldest_image())"""
    
    def save(self):
        np.save(f"{self.daq.exp.directory}/{time.time()}-data", self.frames)
        np.save(f"{self.daq.exp.directory}/{time.time()}-metadata", self.metadata)

    def stop(self):
        self.cam.stop_acquisition()


        

class DAQ:
    def __init__(self, name, lights, stimuli, camera):
        self.name = name
        self.lights, self.stimuli, self.camera = lights, stimuli, camera
        self.tasks, self.light_signals, self.stim_signal, self.camera_signal, self.time_values, self.exp = [], [], [], None, None, None

    def launch(self, stim, exp):
        self.exp = exp
        self.generate_stim_wave(stim)
        self.generate_light_wave(stim)
        self.generate_camera_wave()
        self.write_waveforms(stim)
        self.reset_daq()

    def generate_stim_wave(self, stim):
        self.time_values = np.concatenate((stim.time,stim.time_delay + stim.duration))
        self.stim_signal.append(np.concatenate((stim.stim_signal, stim.empty_signal)))
        if len(self.stim_signal) != 1:
            self.stim_signal = np.stack((self.stim_signal))
        else:
            self.stim_signal = self.stim_signal[0]
    
    def generate_light_wave(self, stim):
        for signal_delay in signal_ajust[len(self.lights)-1]:
            if signal_delay:
                signal = digital_square(self.time_values, self.exp.framerate/3, 0.05, int(signal_delay/(self.exp.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
            else:
                self.light_signals.append(np.full(len(self.time_values), False))
        if len(self.light_signals) != 1:
            self.light_signals = np.stack((self.light_signals))
    
    def generate_camera_wave(self):
        self.camera_signal = np.max(np.vstack((self.light_signals)), axis=0)

    def write_waveforms(self, stim):
        with nidaqmx.Task(new_task_name='lights') as l_task:
            with nidaqmx.Task(new_task_name='stimuli') as s_task:
                self.tasks = [l_task, s_task]
                for stimulus in self.stimuli:
                    s_task.ao_channels.add_ao_voltage_chan(f"{self.name}/{stimulus.port}")
                for light in self.lights:
                    l_task.do_channels.add_do_chan(f"{self.name}/{light.port}")
                self.sample([s_task, l_task])
                self.camera.initialize(self)
                self.write([s_task, l_task], [self.stim_signal, self.light_signals])
                #self.write([s_task, l_task], [self.stim_signal, [[False, False, False, True],[False, False, False, True], [False, False, False, True], [False, False, False, True]]])
                self.start([s_task, l_task])
                self.camera.loop(l_task)
                self.wait([s_task, l_task])
                self.stop([s_task, l_task, self.camera])
                print(len(self.camera.frames))
                print(len(self.camera.metadata))

    def read_metadata(self):
        dico = {}
        for task in self.tasks:
            name = task.name
            value =time.time()
            # to be changed
            dico[name] = value
        return dico
    
    def reset_daq(self):
        self.light_signals, self.stim_signal, self.camera_signal, self.time_values = [], [], None, None

    def start(self, tasks):
        for task in tasks:
            task.start()
    
    def wait(self, tasks):
        for task in tasks:
            task.wait_until_done(timeout=1.5*len(self.time_values)/3000)

    def sample(self, tasks):
        for task in tasks:
            task.timing.cfg_samp_clk_timing(3000, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(self.stim_signal))

    def write(self, tasks, content):
        for i, task in enumerate(tasks):
            task.write(content[i])
    
    def stop(self, tasks):
        for task in tasks:
            task.stop()
    