import nidaqmx
import time
import sys
import os
from nidaqmx.constants import AcquisitionType
import numpy as np
from src.calculations import (
    extend_light_signal,
    shrink_array,
    find_rising_indices,
    reduce_stack,
)
from src.waveforms import digital_square
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


class Camera(Instrument):
    def __init__(self, port, name):
        """A class used to represent a physical camera connected to the computer by a framegrabber

        Args:
            port (str): The name of the camera physical trigger port
            name (str): The name of the camera (can be found using NI-MAX)
        """
        super().__init__(port, name)
        self.frames = []
        self.baseline_frames = []
        self.frames_read = 0
        self.video_running = False
        try:
            self.cam = IMAQ.IMAQCamera("img0")
            self.cam.setup_acquisition(nframes=100)
            self.cam.start_acquisition()
        except Exception as err:
            pass

    def initialize(self, daq):
        """Initialize / Reset the camera parameters

        Args:
            daq (DAQ): The associated DAQ instance
        """
        self.daq = daq
        self.daq.stop_signal = False
        self.frames = []
        self.frames_read_list = []
        self.baseline_read_list = []
        self.frames_read = 0

    def delete_frames(self):
        """Read all frames in the buffer"""
        self.cam.read_multiple_images()

    def loop(self, task):
        """While camera is running, add each acquired frame to a frames list

        Args:
            task (Task): The nidaqmx task used to track if acquisition is finished
        """
        self.task = task
        while task.is_task_done() is False and self.daq.stop_signal is False:
            try:
                self.cam.wait_for_frame(timeout=0.1)
                new_frames = self.cam.read_multiple_images()
                self.frames += new_frames
                self.video_running = True
                if self.adding_frames:
                    self.baseline_data += new_frames
                    self.frames_read_list.append(self.frames_read)
                if self.baseline_completed:
                    self.baseline_frames += new_frames
                    self.baseline_read_list.append(self.frames_read)
                self.frames_read += len(new_frames)
            except Exception as err:
                print("cam err")
                print(err)
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
        if self.is_saving:
            while self.is_saving:
                pass
        np.save(os.path.join(directory, "data", f"{self.file_index}.npy"), self.frames)


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
        self.trigger_activated = False
        self.trigger_port = None
        self.framerate, self.exposure = framerate, exposure
        self.stop_signal = False
        self.lights, self.stimuli, self.camera = lights, stimuli, camera
        self.tasks, self.light_signals, self.stim_signal, self.camera_signal = (
            [],
            [],
            [],
            None,
        )

    def launch(self, name, time_values, stim_values):
        """Generate stimulation, light and camera signal and write them to the DAQ

        Args:
            name (str): The name of the experiment
            time_values (array): A array containing the time values
            stim_values (array): A array containing the stimulation values
        """
        self.reset_daq()
        self.experiment_name = name
        self.time_values = time_values
        self.stim_values = stim_values
        self.generate_stim_wave()
        if len(self.lights) > 0:
            self.generate_light_wave()
            self.generate_camera_wave()
            self.extend_light_wave()
        self.write_waveforms()

    def set_trigger(self, port):
        """ Set the trigger port and activate it"""
        self.trigger_activated = True
        self.trigger_port = port

    def remove_trigger(self):
        """Deactivate the trigger"""
        self.trigger_activated = False

    def generate_stim_wave(self):
        """Create a stack of the stimulation signals and set the last values to zero"""
        self.stim_signal = np.stack((self.stim_values[:-1]))
        self.d_stim_signal = self.stim_values[-1]
        self.stim_signal[0][-1] = 0
        self.stim_signal[1][-1] = 0
        self.d_stim_signal[-1] = False

    def generate_light_wave(self):
        """Generate a light signal for each light used and set the last value to zero"""
        self.light_signals = []
        for potential_light_index in range(4):
            if potential_light_index < len(self.lights):
                signal = digital_square(
                    self.time_values,
                    self.framerate / len(self.lights),
                    self.framerate * self.exposure / len(self.lights),
                    int(potential_light_index * 3000 / (self.framerate)),
                )
                signal[-1] = False
                self.light_signals.append(signal)
        if len(self.light_signals) > 1:
            self.stacked_lights = np.stack((self.light_signals))
        else:
            self.stacked_lights = self.light_signals

    def generate_camera_wave(self):
        """Generate camera signal using the light signals and add it to the list of all signals"""
        try:
            self.camera_signal = np.max(np.vstack((self.stacked_lights)), axis=0)
        except ValueError:
            self.camera_signal = np.zeros(len(self.stim_signal[0]))
        self.all_signals = np.stack(self.light_signals + [self.camera_signal])
        self.allz_signals = np.stack(self.light_signals + [self.camera_signal] + [self.d_stim_signal])

    def extend_light_wave(self):
        """Extend the light signal to be wider than the camera signal"""
        self.stacked_lights = extend_light_signal(
            self.stacked_lights, self.camera_signal
        )

    def write_waveforms(self):
        """Write lights, stimuli and camera signal to the DAQ"""
        if WIDEFIELD_COMPUTER:
            with nidaqmx.Task(new_task_name="lights") as l_task:
                self.control_task = l_task
                with nidaqmx.Task(new_task_name="a_stimuli") as s_task:
                    null_lights = [[False, False]]
                    self.tasks = [l_task, s_task]
                    for light in self.lights:
                        l_task.do_channels.add_do_chan(f"{self.name}/{light.port}")
                        null_lights.append([False, False])
                    if len(self.lights) > 0:
                        l_task.do_channels.add_do_chan(f"{self.name}/{self.camera.port}")
                    for stimulus in self.stimuli:
                        if "ao0" in stimulus.port or "ao1" in stimulus.port:
                            s_task.ao_channels.add_ao_voltage_chan(
                                f"{self.name}/{stimulus.port}"
                            )
                        else:
                            l_task.do_channels.add_do_chan(
                                f"{self.name}/{stimulus.port}"
                            )
                            null_lights.append([False, False])
                    self.camera.initialize(self)
                    self.sample([s_task, l_task])
                    if len(self.lights) > 0:
                        self.write(
                            [s_task, l_task], [self.stim_signal, self.allz_signals]
                        )
                        self.camera.delete_frames()
                        if self.trigger_activated:
                            with nidaqmx.Task(new_task_name="trigger") as t_task:
                                t_task.di_channels.add_di_chan(
                                    (f"{self.name}/{self.trigger_port}")
                                )
                                while True:
                                    time.sleep(0.001)
                                    if t_task.read():
                                        break
                        self.start([s_task, l_task])
                        self.camera.loop(l_task)
                        self.stop([s_task, l_task])
                        s_task.write([[0, 0], [0, 0]])
                        l_task.write(null_lights)
                        self.start([s_task, l_task])
                    else:
                        self.write([s_task, l_task], [self.stim_signal, self.d_stim_signal])
                        self.camera.delete_frames()
                        if self.trigger_activated:
                            with nidaqmx.Task(new_task_name="trigger") as t_task:
                                t_task.di_channels.add_di_chan(
                                    (f"{self.name}/{self.trigger_port}")
                                )
                                while True:
                                    time.sleep(0.001)
                                    if t_task.read():
                                        break
                        self.start([s_task, l_task])
                        while (
                            s_task.is_task_done() is False and self.stop_signal is False
                        ):
                            time.sleep(0.01)
                            pass
                        self.stop([s_task, l_task])
                        s_task.write([[0, 0], [0, 0]])
                        l_task.write([False, False])
                        self.start([s_task, l_task])

        else:
            time.sleep(2)
            self.stop_signal = True
            pass

    def save(self, directory):
        """Save the light and stimulation data for each frame as a NPY file

        Args:
            directory (str): The directory in which to save the NPY file
        """
        try:
            indices = find_rising_indices(self.all_signals[-1])
            reduced_stack = reduce_stack(self.all_signals, indices)
            np.save(f"{directory}/{self.experiment_name}-light_signal", reduced_stack)
        except Exception as err:
            print(err)
        np.save(f"{directory}/{self.experiment_name}-stim_signal", self.stim_signal)

    def reset_daq(self):
        """Reset the DAQ parameters
        """
        self.light_signals, self.stim_signal, self.camera_signal, self.time_values = (
            [],
            [],
            None,
            None,
        )

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
            task.wait_until_done(timeout=1.5 * len(self.time_values) / 3000)

    def sample(self, tasks):
        """Set the sampling rate for a list of nidaqmx tasks

        Args:
            tasks (list): A list of nidaqmx tasks
        """
        for task in tasks:
            task.timing.cfg_samp_clk_timing(
                3000,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=len(self.stim_signal[0]),
            )

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
