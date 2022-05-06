import nidaqmx
import matplotlib.pyplot as plt
import numpy as np


class Instrument:
    def __init__(self, port, daq_name):
        self.port = port
        self.daq_name = daq_name

    def capture(self):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(True)
            task.write(False)'''

    def analog_read(self):
        '''with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(f"{self.daq_name}/{self.port}")
            return task.read()'''

    def analog_write(self, value):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(value)'''


    def digital_write(self, value):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            task.write(value)'''

    def digital_read(self):
        '''with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq_name}/{self.port}")
            return task.read()'''

class DAQ:
    def __init__(self, name, instruments):
        self.name = name
        self.instruments = instruments

    def launch(self, stim, last):
        if last is False:
            time = stim.time,stim.time_delay + stim.duration
            signal = np.concatenate((stim.signal, stim.empty_signal))
        else:
            time = stim.time
            signal = stim.signal

        index = -1
        for time_increment in time[0]:
            index = (index + 1)  % 3
            self.instruments['air_pump'].analog_write(signal[index])

            if index == 0:
                self.instruments['infrared'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['infrared'].digital_write(False)

            elif index == 1:
                self.instruments['red'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['red'].digital_write(False)
                self.instruments['green'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['green'].digital_write(False)

            else:
                self.instruments['blue'].digital_write(True)
                self.instruments['camera'].capture()
                self.instruments['blue'].digital_write(False)

