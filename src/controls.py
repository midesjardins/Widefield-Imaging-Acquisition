import nidaqmx
import time
from nidaqmx.constants import AcquisitionType
import numpy as np
from pandas.core.indexing import need_slice
from src.signal_generator import digital_square
from pylablib.devices import IMAQ
import re
import os
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
        indexes_fr_default = []
        indexes_fr_current = []
        indexes_et_default = []
        indexes_et_current = []
        lines = []
        """with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.icd') as file:
            with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.txt', "w") as new_file:
                for line in file:
                    new_file.write(line)
        with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.txt') as txt_file:
            for i, line in enumerate(txt_file):
                if "Attribute (Frame Rate)" in line:
                    indexes_fr_default.append(i+11)
                    indexes_fr_current.append(i+12)
                if "Attribute (Exposure Time)" in line:

                    indexes_et_default.append(i+11)
                    indexes_et_current.append(i+12)

        with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.txt') as txt_edit:
            for i, line in enumerate(txt_edit):
                if i in indexes_fr_default:
                    lines.append(f"                                    Default ({self.daq.framerate})\n")   
                elif i in indexes_fr_current:
                    lines.append(f"                                    Current ({self.daq.framerate})\n")
                elif i in indexes_et_default:
                    lines.append(f"                                    Default ({self.daq.exposure})\n")   
                elif i in indexes_et_current:
                    lines.append(f"                                    Current ({self.daq.exposure})\n")
                else:
                    lines.append(line)

        with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.icd', "w") as file:
            file.write("".join(lines))

        with open('C:\\Users\\Public\\Documents\\National Instruments\\NI-IMAQ\\Data\\Dalsa 1M60.icd', 'w') as file:
            file.write("".join(lines))"""
        self.cam = IMAQ.IMAQCamera(self.port)
        print("cam init")
        self.cam.setup_acquisition(nframes=20)
        #self.cam.configure_trigger_in(trig_type="ext",trig_action="buffer")
        self.cam.set_roi(0,1024,0,1024)
        self.cam.start_acquisition()
        self.cam.setup_serial_params(write_term="\r", datatype="str")
        self.cam.serial_write("sem 4")
        while True:
            try:
                self.cam.serial_read(1)
            except Exception:
                break
        current_time = time.time()
        while time.time()-current_time <  3:
            print(time.time()-current_time)
        print("acquisition started")

    def loop(self, task=None):
        if task == None:
            self.cam.read_multiple_images()
            while not self.CameraStopped:
                self.cam.wait_for_frame(timeout=200)
                img_tuple =  self.cam.read_multiple_images(return_info=True)
                self.frames += img_tuple[0]
                self.metadata += img_tuple[1]
            self.cam.stop_acquisition()
        
        else:
            self.cam.read_multiple_images()
            while not task.is_task_done():
                self.cam.wait_for_frame(timeout=200)
                print(len(self.frames))
                img_tuple =  self.cam.read_multiple_images(return_info=True)
                self.frames += img_tuple[0]
                self.metadata += img_tuple[1]
            self.cam.stop_acquisition()
            #self.metadata.append({"time": time.time(), "daq": self.daq.read_metadata()})
    
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
    
    def generate_light_wave(self, stim):
        for signal_delay in signal_ajust[len(self.lights)-1]:
            if signal_delay:
                signal = digital_square(self.time_values, self.framerate/3, 0.15, int(signal_delay/(self.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
            else:
                self.light_signals.append(np.full(len(self.time_values), False))
        if len(self.light_signals) != 1:
            self.stack_light_signals = np.stack((self.light_signals))
    
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
            self.camera.daq = self
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
    