import nidaqmx
import matplotlib.pyplot as plt
import numpy as np


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

    def launch(self, stim, last):
        if last is False:
            time_values = stim.time,stim.time_delay + stim.duration
            signal = np.concatenate((stim.signal, stim.empty_signal))
        else:
            time_values = stim.time
            signal = stim.signal

        repeat = 9000/stim.framerate
        trigger_indexes = np.linspace(0, repeat, 4, dtype = int)[0:3]
        index = -1
        begin_time = time.time()
        for time_increment in time_values[0]:
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
            end_increment = time.time()
