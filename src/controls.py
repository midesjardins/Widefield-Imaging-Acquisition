import nidaqmx
import time
import sys
import os
from nidaqmx.constants import AcquisitionType
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.blocks import Stimulation
from src.signal_generator import digital_square
from src.data_handling import shrink_array, find_rising_indices, create_complete_stack, reduce_stack
from pylablib.devices import IMAQ
import matplotlib.pyplot as plt
import threading
import warnings
warnings.filterwarnings("ignore")

WIDEFIELD_COMPUTER = True

class Instrument:
    def __init__(self, port, name):
        self.port = port
        self.name = name
        self.cam = None
        self.activated = False
    def activate(self):
        self.activated = True

class Camera(Instrument):
    def __init__(self, port, name):
        super().__init__(port, name)
        self.frames, self.metadata = [], []
        #self.first = True
        self.video_running = False
        self.cam = IMAQ.IMAQCamera("img0")
        self.cam.setup_acquisition(nframes=100)
        self.cam.start_acquisition()

    def initialize(self, daq):
        self.daq = daq
        self.frames = []
        #if self.first:
            #self.cam = IMAQ.IMAQCamera("img0")
            #self.cam.setup_acquisition(nframes=100)
        #self.first = False
        #self.cam.start_acquisition()

    def loop(self, task):
        while task.is_task_done() is False and self.daq.stop_signal is False:
            self.cam.wait_for_frame(timeout=200)
            self.frames += self.cam.read_multiple_images()
            self.video_running = True
        self.video_running = False
        self.daq.stop_signal = False
        #self.cam.stop_acquisition()
    
    def save(self, directory, extents):
        if extents:
            self.frames = shrink_array(self.frames, extents)
        save_time = time.time()
        np.save(f"{directory}/{save_time}-data", self.frames)
        np.save(f"{directory}/{save_time}-metadata", self.metadata)


        

class DAQ:
    def __init__(self, name, lights, stimuli, camera, framerate, exposure, window):
        self.name = name
        self.window = window
        self.framerate, self.exposure = framerate, exposure
        self.stop_signal = False
        self.lights, self.stimuli, self.camera = lights, stimuli, camera
        self.tasks, self.light_signals, self.stim_signal, self.camera_signal = [], [], [], None

    def return_lights(self):
        lights = []
        for light in self.lights:
            lights.append(light.name)
        return lights

    def launch(self, exp):
        self.exp = exp
        self.generate_stim_wave()
        print(str(time.time()-self.start_runtime) + "to generate stim wave")
        self.generate_light_wave()
        print(str(time.time()-self.start_runtime) + "to generate light wave")
        self.generate_camera_wave()
        print(str(time.time()-self.start_runtime) + "to generate camers wave")
        self.write_waveforms()
        self.reset_daq()
    

    def generate_stim_wave(self):
        self.stim_signal = np.stack((self.exp.stim_signal))
        self.stim_signal[0][-1] = 0
        self.stim_signal[1][-1] = 0
    
    def generate_light_wave(self):
        for potential_light_index in range(4):
            if potential_light_index < len(self.lights):
                signal = digital_square(self.exp.time, self.framerate/len(self.lights), self.exposure, int(potential_light_index*3000/(self.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
        if len(self.light_signals) > 1:
            self.stack_light_signals = np.stack((self.light_signals))
        else:
            self.stack_light_signals = self.light_signals
    
    def generate_camera_wave(self):
        self.camera_signal = np.max(np.vstack((self.stack_light_signals)), axis=0)
        self.all_signals = np.stack(self.light_signals + [self.camera_signal])

    def write_waveforms(self):
        if WIDEFIELD_COMPUTER:
            with nidaqmx.Task(new_task_name='lights') as l_task:
                self.control_task = l_task
                with nidaqmx.Task(new_task_name='stimuli') as s_task:
                    self.tasks = [l_task, s_task]
                    for stimulus in self.stimuli:
                        s_task.ao_channels.add_ao_voltage_chan(f"{self.name}/{stimulus.port}")
                    for light in self.lights:
                        l_task.do_channels.add_do_chan(f"{self.name}/{light.port}")
                    l_task.do_channels.add_do_chan(f"{self.name}/port0/line4")
                    print(str(time.time()-self.start_runtime) + "to define tasks")
                    self.camera.initialize(self)
                    print(str(time.time()-self.start_runtime) + "to initialize camera")
                    self.sample([s_task, l_task])
                    self.write([s_task, l_task], [self.stim_signal, self.all_signals])
                    self.start([s_task, l_task])
                    print(str(time.time()-self.start_runtime) + "to sample/write/start")
                    self.camera.loop(l_task)
                    self.stop([s_task, l_task])

        else:
            time.sleep(2)
            np.save("/Users/maxence/chul/Widefield-Imaging-Acquisition/all_signals.npy", self.all_signals)
            np.save("/Users/maxence/chul/Widefield-Imaging-Acquisition/stim_signal.npy", self.stim_signal)
            pass
            """start_time = time.time()
            self.signal_is_running = True
            while time.time()-start_time < self.exp.time[-1]:
                self.current_signal_time = round(time.time() - start_time, 2)
                time.sleep(0.01)
            self.signal_is_running = False"""

    def plot_lights(self):
        for light_signal in self.light_signals:
            plt.plot(self.exp.time, light_signal)
        plt.show()

    def save(self, directory):
        stack = create_complete_stack(self.all_signals, self.stim_signal)
        indices = find_rising_indices(self.all_signals[-1])
        reduced_stack = reduce_stack(stack, indices)
        save_time = time.time()
        np.save(f"{directory}/{save_time}-signal_data", reduced_stack)
    
    def reset_daq(self):
        self.light_signals, self.stim_signal, self.camera_signal, self.exp.time = [], [], None, None

    def start(self, tasks):
        for task in tasks:
            task.start()
    
    def wait(self, tasks):
        for task in tasks:
            task.wait_until_done(timeout=1.5*len(self.exp.time)/3000)

    def sample(self, tasks):
        for task in tasks:
            task.timing.cfg_samp_clk_timing(3000, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(self.stim_signal[0]))

    def write(self, tasks, content):
        for i, task in enumerate(tasks):
            task.write(content[i])
    
    def stop(self, tasks):
        for task in tasks:
            task.stop()
    




"""LIGHTS = [Instrument('port0/line3', 'ir'), Instrument('port0/line0', 'red'),
                       Instrument('port0/line2', 'green')]
STIMULI = [Instrument('ao1', 'air-pump')]
CAMERA = Camera('img0', 'name')
DAQ1 = DAQ('dev1', LIGHTS, STIMULI, CAMERA, 3, 0.01, None)
STIMULATION = Stimulation(DAQ1,10,frequency=1,duty=0.1)
DAQ1.generate_stim_wave(STIMULATION)
DAQ1.generate_light_wave()
DAQ1.plot_lights()"""