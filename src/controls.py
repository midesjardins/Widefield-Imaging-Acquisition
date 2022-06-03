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

class Instrument:
    def __init__(self, port, daq_name):
        self.port = port
        self.daq_name = daq_name
        self.cam = None

class Camera(Instrument):
    def __init__(self, port, daq_name):
        super().__init__(port, daq_name)
        self.frames, self.metadata = [], []

    def initialize(self, daq):
        self.daq = daq
        self.cam = IMAQ.IMAQCamera(self.port)
        self.cam.setup_acquisition(nframes=20)
        self.cam.start_acquisition()

    def loop(self, task):
        while not task.is_task_done():
            self.cam.wait_for_frame(timeout=200)
            print(len(self.frames))
            img_tuple =  self.cam.read_multiple_images(return_info=True)
            self.frames += img_tuple[0]
            self.metadata += img_tuple[1]
        self.cam.stop_acquisition()
    
    def save(self, directory):
        save_time = time.time()
        np.save(f"{directory}/{save_time}-data", self.frames)
        np.save(f"{directory}/{save_time}-metadata", self.metadata)


        

class DAQ:
    def __init__(self, name, lights, stimuli, camera, framerate, exposure, window):
        self.name = name
        self.window = window
        self.framerate, self.exposure = framerate, exposure
        self.signal_is_running = False
        self.lights, self.stimuli, self.camera = lights, stimuli, camera
        self.tasks, self.light_signals, self.stim_signal, self.camera_signal = [], [], [], None

    def launch(self, stim):
        self.stim = stim
        self.generate_stim_wave()
        self.generate_light_wave()
        self.generate_camera_wave()
        self.write_waveforms()
        self.reset_daq()
    

    def generate_stim_wave(self):
        #self.time_values = np.concatenate((stim.time,stim.time_delay + stim.duration))
        #self.time_values = self.stim.time
        #self.stim_signal.append(np.concatenate((stim.stim_signal, stim.empty_signal)))
        print(self.stim.stim_signal)
        if len(self.stim.stim_signal) != 1:
            self.stim_signal = np.stack((self.stim.stim_signal))
        else:
            self.stim_signal = self.stim.stim_signal[0]
    
    def generate_light_wave(self):
        for potential_light_index in range(4):
            if potential_light_index < len(self.lights):
                signal = digital_square(self.stim.time, self.framerate/len(self.lights), self.exposure, int(potential_light_index*3000/(self.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
            else:
                self.light_signals.append(np.full(len(self.stim.time), False))
        if len(self.light_signals) > 1:
            self.stack_light_signals = np.stack((self.light_signals))
    
    def generate_camera_wave(self):
        self.camera_signal = np.max(np.vstack((self.stack_light_signals)), axis=0)
        self.all_signals = np.stack(self.light_signals + [self.camera_signal])

    def write_waveforms(self):
        if WIDEFIELD_COMPUTER:
            with nidaqmx.Task(new_task_name='lights') as l_task:
                with nidaqmx.Task(new_task_name='stimuli') as s_task:
                    self.tasks = [l_task, s_task]
                    for stimulus in self.stimuli:
                        s_task.ao_channels.add_ao_voltage_chan(f"{self.name}/{stimulus.port}")
                    for light in self.lights:
                        l_task.do_channels.add_do_chan(f"{self.name}/{light.port}")
                    l_task.do_channels.add_do_chan(f"{self.name}/{self.camera.port}")
                    self.camera.initialize(self)
                    self.sample([s_task, l_task])
                    self.write([s_task, l_task], [self.stim_signal, self.all_signals])
                    self.start([s_task, l_task])
                    self.camera.loop(l_task)
                    self.wait([s_task, l_task])
                    self.stop([s_task, l_task])

        else:
            start_time = time.time()
            self.signal_is_running = True
            while time.time()-start_time < self.stim.time[-1]:
                self.current_signal_time = round(time.time() - start_time, 2)
                time.sleep(0.01)
            self.signal_is_running = False

    def plot_lights(self):
        for light_signal in self.light_signals:
            plt.plot(self.stim.time, light_signal)
        plt.show()

    def read_metadata(self):
        pass
    
    def reset_daq(self):
        self.light_signals, self.stim_signal, self.camera_signal, self.stim.time = [], [], None, None

    def start(self, tasks):
        for task in tasks:
            task.start()
    
    def wait(self, tasks):
        for task in tasks:
            task.wait_until_done(timeout=1.5*len(self.stim.time)/3000)

    def sample(self, tasks):
        for task in tasks:
            task.timing.cfg_samp_clk_timing(3000, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(self.stim_signal))

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