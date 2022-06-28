import nidaqmx
import time
import sys
import os
from nidaqmx.constants import AcquisitionType
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.signal_generator import digital_square
from src.data_handling import shrink_array, find_rising_indices, create_complete_stack, reduce_stack
from pylablib.devices import IMAQ
import warnings
warnings.filterwarnings("ignore")

WIDEFIELD_COMPUTER = True
class Instrument:
    def __init__(self, port, name):
        """A class used to represent a analog or digital instrument controlled by a DAQ

        Args:
            port (str): The associated physical port
            name (str): The name of the instrument
        """
        self.port = port
        self.name = name
        self.cam = None

class Camera(Instrument):
    def __init__(self, port, name):
        """A class used to represent a physical camera connected to the computer by a framegrabber

        Args:
            port (str): The name of the camera physical trigger port
            name (str): The name of the camera (can be found using NI-MAX)
        """
        super().__init__(port, name)
        self.frames = []
        self.video_running = False
        self.cam = IMAQ.IMAQCamera("img0")
        self.cam.setup_acquisition(nframes=100)
        self.cam.start_acquisition()

    def initialize(self, daq):
        """Initialize / Reset the camera parameters

        Args:
            daq (DAQ): The associated DAQ instance
        """
        self.daq = daq
        self.daq.stop_signal = False
        self.frames = []

    def loop(self, task):
        self.task = task
        """While camera is running, add each acquired frame to a frames list

        Args:
            task (Task): The nidaqmx task used to track if acquisition is finished
        """
        while task.is_task_done() is False and self.daq.stop_signal is False:
            try:
                self.cam.wait_for_frame(timeout=0.1)
                self.frames += self.cam.read_multiple_images()
                self.video_running = True
            except Exception:
                pass
        self.frames += self.cam.read_multiple_images()
        self.video_running = False
    
    def save(self, directory, extents):
        """Save the acquired frames (reduced if necessary) to a 3D NPY file

        Args:
            directory (str): The location in which to save the NPY file
            extents (tuple): The positions of the corners used to resize the frames 
                             Equal to None if original size is kept
        """
        if extents:
            self.frames = shrink_array(self.frames, extents)
        np.save(f"{directory}/{self.daq.experiment_name}-data", self.frames)


        

class DAQ:
    def __init__(self, name, lights, stimuli, camera, framerate, exposure):
        """A class used to represent a Data Acquisition Device (DAQ)

        Args:
            name (str): The name of the DAQ
            lights (list of Instrument): A list of the lights used in the experiment
            stimuli (list of Instrument): A list of the stimuli used in the experiment
            camera (Camera): The camera used in the experiment
            framerate (int): The acquisition framerate
            exposure (float): The exposure time in seconds
        """
        self.name = name
        self.framerate, self.exposure = framerate, exposure
        self.stop_signal = False
        self.lights, self.stimuli, self.camera = lights, stimuli, camera
        self.tasks, self.light_signals, self.stim_signal, self.camera_signal = [], [], [], None

    def launch(self, name, time_values, stim_values):
        """Generate stimulation, light and camera signal and write them to the DAQ

        Args:
            name (str): The name of the experiment
            time_values (array): A array containing the time values
            stim_values (array): A array containing the stimulation values
        """

        self.experiment_name = name
        self.time_values = time_values
        self.stim_values = stim_values
        self.generate_stim_wave()
        self.generate_light_wave()
        self.generate_camera_wave()
        self.write_waveforms()
        print("write waveforms done")
        self.reset_daq()
        print("reset daq done")
    

    def generate_stim_wave(self):
        """Create a stack of the stimulation signals and set the last values to zero"""
        self.stim_signal = np.stack((self.stim_values))
        self.stim_signal[0][-1] = 0
        self.stim_signal[1][-1] = 0
    
    def generate_light_wave(self):
        """Generate a light signal for each light used and set the last value to zero"""
        for potential_light_index in range(4):
            if potential_light_index < len(self.lights):
                signal = digital_square(self.time_values, self.framerate/len(self.lights), self.framerate*self.exposure/len(self.lights), int(potential_light_index*3000/(self.framerate)))
                signal[-1] = False
                self.light_signals.append(signal)
        if len(self.light_signals) > 1:
            self.stacked_lights = np.stack((self.light_signals))
        else:
            self.stacked_lights = self.light_signals
    
    def generate_camera_wave(self):
        """Generate camera signal using the light signals and add it to the list of all signals"""
        self.camera_signal = np.max(np.vstack((self.stacked_lights)), axis=0)
        self.all_signals = np.stack(self.light_signals + [self.camera_signal])

    def write_waveforms(self):
        """Write lights, stimuli and camera signal to the DAQ"""
        if WIDEFIELD_COMPUTER:
            with nidaqmx.Task(new_task_name='lights') as l_task:
                self.control_task = l_task
                with nidaqmx.Task(new_task_name='stimuli') as s_task:
                    null_lights = [[False, False]]
                    self.tasks = [l_task, s_task]
                    for stimulus in self.stimuli:
                        s_task.ao_channels.add_ao_voltage_chan(f"{self.name}/{stimulus.port}")
                    for light in self.lights:
                        l_task.do_channels.add_do_chan(f"{self.name}/{light.port}")
                        null_lights.append([False, False])
                    l_task.do_channels.add_do_chan(f"{self.name}/{self.camera.port}")
                    self.camera.initialize(self)
                    self.sample([s_task, l_task])
                    self.write([s_task, l_task], [self.stim_signal, self.all_signals])
                    self.start([s_task, l_task])
                    self.camera.loop(l_task)
                    self.stop([s_task, l_task])
                    s_task.write([[0, 0],[0, 0]])
                    l_task.write(null_lights)
                    self.start([s_task, l_task])

        else:
            time.sleep(2)
            pass

    def return_lights(self):
        lights = []
        for light in self.lights:
            lights.append(light.name)
        return lights

    def save(self, directory):
        """Save the light and stimulation data for each frame as a NPY file

        Args:
            directory (str): The directory in which to save the NPY file
        """
        stack = create_complete_stack(self.all_signals, self.stim_signal)
        indices = find_rising_indices(self.all_signals[-1])
        reduced_stack = reduce_stack(stack, indices)
        np.save(f"{directory}/{self.experiment_name}-signal_data", reduced_stack)
    
    def reset_daq(self):
        """Reset the DAQ parameters
        """
        self.light_signals, self.stim_signal, self.camera_signal, self.time_values = [], [], None, None

    def start(self, tasks):
        """Start each nidaqmx task in a list

        Args:
            tasks (list): A list of nidaqmx tasks
        """
        for task in tasks:
            task.start()
    
    def wait(self, tasks):
        """Wait for completion of nidaqmx tasks in a list

        Args:
            tasks (list): A list of nidaqmx tasks
        """
        for task in tasks:
            task.wait_until_done(timeout=1.5*len(self.time_values)/3000)

    def sample(self, tasks):
        """Set the sampling rate for a list of nidaqmx tasks

        Args:
            tasks (list): A list of nidaqmx tasks
        """
        for task in tasks:
            task.timing.cfg_samp_clk_timing(3000, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(self.stim_signal[0]))

    def write(self, tasks, content):
        """Write a list of arrays to a list of nidaqmx tasks

        Args:
            tasks (list): A list of nidaqmx tasks
            content (list): A list of arrays to write
        """
        for i, task in enumerate(tasks):
            task.write(content[i])
    
    def stop(self, tasks):
        """Stop each nidaqmx task in a list

        Args:
            tasks (list): A list of nidaqmx tasks
        """
        for task in tasks:
            task.stop()