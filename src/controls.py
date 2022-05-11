import nidaqmx
import matplotlib.pyplot as plt
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import LineGrouping
from nidaqmx.constants import Edge
import numpy as np
import time
from src.signal_generator import square_signal


class Instrument:
    def __init__(self, port, daq_name):
        self.port = port
        self.daq_name = daq_name

class Camera(Instrument):
    def capture(self):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(True)
            task.write(False)'''

class Light(Instrument):
    def analog_write(self, value):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(value)'''
    def digital_write(self, value):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(value)'''

class Stimuli(Instrument):
    def analog_write(self, value):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(value)'''
    def digital_write(self, value):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(value)'''


class DAQ:
    def __init__(self, name, instruments):
        self.name = name
        self.instruments = instruments
        self.number_of_lights = len(self.instruments['lights'])
        self.lights_tasks = None
        self.camera_task = None
        self.stimuli_tasks = None
        self.stim_signal = None
        self.duration = None
        self.light_signals = []
        self.camera_signal = None
        self.ports = instruments['ports']
        self.signal_ajust = [
            [0, None, None, None], 
            [0, 4500, None, None], 
            [0, 3000, 6000, None], 
            [0, 2250, 4500, 6750]]

    def launch(self, stim, last):
        if last is False:
            time_values = np.concatenate((stim.time,stim.time_delay + stim.duration))
            self.stim_signal = np.concatenate((stim.stim_signal, stim.empty_signal))
        else:
            time_values = stim.time
            self.stim_signal = stim.stim_signal

        for signal_delay in self.signal_ajust[self.number_of_lights-1]:
            if signal_delay is not None:
                signal = square_signal(time_values, stim.framerate/3, 0.05, int(signal_delay/(stim.framerate)), digital=True)
                signal[-1] = False
                self.light_signals.append(signal)
            else:
                self.light_signals.append(np.full(len(time_values), False))
        self.camera_signal= np.max(np.vstack((self.light_signals)), axis=0)
        self.duration = stim.duration
        self.write_waveforms()
        self.light_signals = []

    def write_waveforms(self):
        signal_stack = np.stack((self.light_signals))
        print(signal_stack)
        with nidaqmx.Task(new_task_name='lights') as l_task:
            with nidaqmx.Task(new_task_name='stimuli') as s_task:
                with nidaqmx.Task(new_task_name='camera') as c_task:
                    #c_task.co_channels.add_co_pulse_chan_time(f"{self.name}/{self.ports['camera']}")
                    s_task.ao_channels.add_ao_voltage_chan(f"{self.name}/{self.ports['stimuli']}")
                    l_task.do_channels.add_do_chan(f"{self.name}/port0/line0")
                    l_task.do_channels.add_do_chan(f"{self.name}/port0/line1")
                    l_task.do_channels.add_do_chan(f"{self.name}/port0/line2")
                    l_task.do_channels.add_do_chan(f"{self.name}/port0/line3")
                    #c_task.timing.cfg_samp_clk_timing(rate=3000)
                    #c_task.write(self.camera_signal)
                    #s_task.timing.cfg_samp_clk_timing(rate=3000, samps_per_chan=100000)
                    s_task.timing.cfg_samp_clk_timing(3000, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(self.stim_signal))
                    l_task.timing.cfg_samp_clk_timing(3000, sample_mode=AcquisitionType.FINITE, samps_per_chan=len(self.stim_signal))
                    s_task.write(self.stim_signal)
                    l_task.write(signal_stack)
                    s_task.start()
                    l_task.start()
                    s_task.wait_until_done(timeout=1.5*self.duration)
                    l_task.wait_until_done(timeout=1.5*self.duration)
                    s_task.stop()
                    l_task.stop()
                    #s_task.write(self.stim_signal)
                    #l_task.write(signal_stack)
                    #c_task.start()
                    #s_task.write(5)
                    #l_task.start()
