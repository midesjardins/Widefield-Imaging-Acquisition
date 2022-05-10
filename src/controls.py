import nidaqmx
import matplotlib.pyplot as plt
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
        self.light_signals = []
        self.signal_ajust = [[0, None, None, None], [0, 4500, None, None], [0, 3000, 6000, None], [0, 2250, 4500, 6750]]

    def launch(self, stim, last):
        if last is False:
            time_values = np.concatenate((stim.time,stim.time_delay + stim.duration))
            stim_signal = np.concatenate((stim.stim_signal, stim.empty_signal))
        else:
            time_values = stim.time
            stim_signal = stim.stim_signal

        for signal_delay in self.signal_ajust[self.number_of_lights-1]:
            if signal_delay != None:
                self.light_signals.append(square_signal(time_values, stim.framerate/3, 0.1, int(signal_delay/(stim.framerate))))
            else:
                self.light_signals.append(np.zeros(len(time_values)))
        for signal in self.light_signals:
            plt.plot(time_values, signal)
        plt.plot(time_values, stim_signal)
        plt.show()
        self.light_signals = []

        '''repeat = 900/stim.framerate
        trigger_indexes = np.linspace(0, repeat, 4, dtype = int)[0:3]
        index = -1
        begin_time = time.time()
        for time_increment in time_values[0]:
            target_time = time.time() + 1/3000
            index = (index + 1)  % int(repeat)
            self.instruments['air_pump'].analog_write(signal[index])

            if index == trigger_indexes[0]:
                #print('ir')
                self.instruments['infrared'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['infrared'].digital_write(False)

            elif index == trigger_indexes[1]:
                #print('intrinsic')
                self.instruments['red'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['red'].digital_write(False)
                self.instruments['green'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['green'].digital_write(False)

            elif index == trigger_indexes[2]:
                #print('fluo')
                self.instruments['blue'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['blue'].digital_write(False)
            while time.time() < target_time:
                pass
        print(time.time()-begin_time)'''
