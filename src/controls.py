import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np
from src.signal_generator import digital_square

signal_ajust = [
            [0, None, None, None], 
            [0, 4500, None, None], 
            [0, 3000, 6000, None], 
            [0, 2250, 4500, 6750]]


class Instrument:
    def __init__(self, port, daq_name):
        self.port = port
        self.daq_name = daq_name

class DAQ:
    def __init__(self, name, lights, stimuli, camera):
        self.name = name
        self.lights, self.stimuli, self.camera = lights, stimuli, camera
        self.light_signals, self.stim_signal, self.camera_signal, self.time_values = [], [], None, None

    def launch(self, stim, last):
        self.generate_stim_wave(stim, last)
        self.generate_light_wave(stim)
        self.generate_camera_wave()
        self.write_waveforms()
        self.reset_daq()

    def generate_stim_wave(self, stim, last):
        if last is False:
            self.time_values = np.concatenate((stim.time,stim.time_delay + stim.duration))
            self.stim_signal.append(np.concatenate((stim.stim_signal, stim.empty_signal)))
        else:
            self.time_values = stim.time
            self.stim_signal.append(stim.stim_signal)
    
    def generate_light_wave(self, stim):
        for signal_delay in signal_ajust[len(self.lights)-1]:
            if signal_delay:
                signal = digital_square(self.time_values, stim.framerate/3, 0.05, int(signal_delay/(stim.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
            else:
                self.light_signals.append(np.full(len(self.time_values), False))
    
    def generate_camera_wave(self):
        self.camera_signal = np.max(np.vstack((self.light_signals)), axis=0)

    def write_waveforms(self):
        with nidaqmx.Task(new_task_name='lights') as l_task:
            with nidaqmx.Task(new_task_name='stimuli') as s_task:
                with nidaqmx.Task(new_task_name='camera') as c_task:
                    for stimulus in self.stimuli:
                        s_task.ao_channels.add_ao_voltage_chan(f"{self.name}/{stimulus.port}")
                    for light in self.lights:
                        l_task.do_channels.add_do_chan(f"{self.name}/{light.port}")
                    self.sample(s_task, l_task)
                    self.write([s_task, l_task], [np.stack((self.stim_signal)), np.stack((self.light_signals))])
                    self.start(s_task, l_task)
                    self.wait(s_task, l_task)
                    self.stop(s_task, l_task)
    
    def reset_daq(self):
        self.light_signals, self.stim_signal, self.camera_signal, self.time_values = [], None, None, None

    def start(self, tasks):
        for task in tasks:
            task.start()
    
    def wait(self, tasks):
        for task in tasks:
            task.wait_until_done(timeout=1.5*len(self.time_values)/3000)

    def write(self, tasks, content):
        for i, task in enumerate(tasks):
            task.write(content[i])
    
    def stop(self, tasks):
        for task in tasks:
            task.stop()
    
    def sample(self, tasks):
        for task in tasks:
            task.timing.cfg_samp_clk_timing(3000, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(self.stim_signal))