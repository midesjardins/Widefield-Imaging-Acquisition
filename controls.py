import nidaqmx



class Instrument:
    def __init__(self, port):
        self.port = port

    def analog_read(self):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(f"{self.daq.name}/{self.port}")
            value = task.read()
            print(value)

    def analog_write(self):
        with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq.name}/{self.port}")
            task.write(2)


    def digital_write(self):
        with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq.name}/{self.port}")
            task.write(True)

    def digital_read(self):
        with nidaqmx.Task() as task:
            task.co_channels.add_co_pulse_chan_time(f"{self.daq.name}/{self.port}")
            value = task.read()
            print(value)

class DAQ:
    def __init__(self, name, instruments):
        self.name = name
        self.instruments = instruments

    def launch(self):
        pass

