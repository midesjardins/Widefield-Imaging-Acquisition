import nidaqmx
import time
import sys
import os
from nidaqmx.constants import AcquisitionType
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.blocks import Stimulation
from src.signal_generator import digital_square
from pylablib.devices import IMAQ
import matplotlib.pyplot as plt

WIDEFIELD_COMPUTER = False

signal_ajust = [
            [0, None, None, None], 
            [0, 4500, None, None], 
            [0, 3000, 6000, None], 
            [0, 2250, 4500, 6750]]


class Instrument:
    def __init__(self, port, daq_name):
        self.port = port
        self.daq_name = daq_name
        self.stim_number = 0
        self.cam = None

class Camera(Instrument):
    def __init__(self, port, daq_name):
        super().__init__(port, daq_name)
        self.frames = []
        self.metadata = []
        self.CameraStopped = True

    def initialize(self, daq):
        self.daq = daq
        self.cam = IMAQ.IMAQCamera(self.port)
        self.cam.setup_acquisition(nframes=20)
        self.cam.start_acquisition()

    def loop(self, task=None):
        current_time = time.time()
        self.cam.read_multiple_images()
        while not task.is_task_done():
            self.cam.wait_for_frame(timeout=200)
            print(len(self.frames))
            img_tuple =  self.cam.read_multiple_images(return_info=True)
            self.frames += img_tuple[0]
            self.metadata += img_tuple[1]
        elapsed_time = time.time() - current_time
        framerate = len(self.frames)/elapsed_time
        print(f"the framerate is {framerate}")
        self.cam.stop_acquisition()
    
    def save(self, directory):
        save_time = time.time()
        np.save(f"{directory}/{save_time}-data", self.frames)
        np.save(f"{directory}/{save_time}-metadata", self.metadata)
        self.stim_number += 1


        

class DAQ:
    def __init__(self, name, lights, stimuli, camera, framerate, exposure, window):
        self.name = name
        self.window = window
        self.framerate, self.exposure = framerate, exposure
        self.lights, self.stimuli, self.camera = lights, stimuli, camera
        self.tasks, self.light_signals, self.stim_signal, self.camera_signal, self.time_values = [], [], [], None, None

    def launch(self, stim):
        self.stim = stim
        self.generate_stim_wave(stim)
        self.generate_light_wave(stim)
        self.generate_camera_wave()
        #plt.clf()
        #plt.plot(self.camera_signal)
        #plt.savefig("test.pdf")

        self.write_waveforms(stim)
        self.reset_daq()
    

    def generate_stim_wave(self, stim):
        self.time_values = np.concatenate((stim.time,stim.time_delay + stim.duration))
        self.stim_signal.append(np.concatenate((stim.stim_signal, stim.empty_signal)))
        if len(self.stim_signal) != 1:
            self.stim_signal = np.stack((self.stim_signal))
        else:
            self.stim_signal = self.stim_signal[0]
        return (self.time_values, self.stim_signal)
    
    def generate_light_wave(self, stim=None):
        for potential_light_index in range(4):
            if potential_light_index < len(self.lights):
                signal = digital_square(self.time_values, self.framerate/len(self.lights), self.exposure, int(potential_light_index*3000/(self.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
            else:
                self.light_signals.append(np.full(len(self.time_values), False))
        if len(self.light_signals) > 1:
            self.stack_light_signals = np.stack((self.light_signals))

    def plot_lights(self):
        for light_signal in self.light_signals:
            plt.plot(self.time_values, light_signal)
        plt.show()


        """for signal_delay in signal_ajust[len(self.lights)-1]:
            if signal_delay:
                signal = digital_square(self.time_values, self.framerate/3, 0.15, int(signal_delay/(self.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
            else:
                self.light_signals.append(np.full(len(self.time_values), False))
        if len(self.light_signals) != 1:
            self.stack_light_signals = np.stack((self.light_signals))"""
    
    def generate_camera_wave(self):
        self.camera_signal = np.max(np.vstack((self.stack_light_signals)), axis=0)
        self.all_signals = np.stack(self.light_signals + [self.camera_signal])

    def write_waveforms(self, stim):
        if WIDEFIELD_COMPUTER == True: 
            with nidaqmx.Task(new_task_name='lights') as l_task:
                with nidaqmx.Task(new_task_name='stimuli') as s_task:
                    with nidaqmx.Task(new_task_name="trigger") as t_task:
                        self.tasks = [l_task, s_task]
                        for stimulus in self.stimuli:
                            s_task.ao_channels.add_ao_voltage_chan(f"{self.name}/{stimulus.port}")
                        for light in self.lights:
                            l_task.do_channels.add_do_chan(f"{self.name}/{light.port}")
                        l_task.do_channels.add_do_chan(f"{self.name}/port0/line4")
                        self.sample([s_task, l_task])
                        self.camera.initialize(self)
                        self.write([s_task, l_task], [self.stim_signal, self.all_signals])
                        self.start([s_task, l_task])
                        self.camera.loop(l_task)
                        self.wait([s_task, l_task])
                        self.stop([s_task, l_task])
                        print(len(self.camera.frames))

        else:
            time.sleep(3)

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
    

LIGHTS = [Instrument('port0/line3', 'ir'), Instrument('port0/line0', 'red'),
                       Instrument('port0/line2', 'green')]
STIMULI = [Instrument('ao1', 'air-pump')]


"""CAMERA = Camera('img0', 'name')
DAQ1 = DAQ('dev1', LIGHTS, STIMULI, CAMERA, 3, 0.01, None)
STIMULATION = Stimulation(DAQ1,10,frequency=1,duty=0.1)
DAQ1.generate_stim_wave(STIMULATION)
DAQ1.generate_light_wave()
DAQ1.plot_lights()"""