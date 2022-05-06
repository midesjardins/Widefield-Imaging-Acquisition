import nidaqmx

def analog_read():
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
        value = task.read()
        print(value)

def analog_write():
    with nidaqmx.Task() as task:
        task.co_channels.add_co_pulse_chan_time("Dev1/ao0")
        task.write(2)


def digital_read():
    with nidaqmx.Task() as task:
        task.co_channels.add_co_pulse_chan_time("Dev1/port0/line0")
        task.write(True)

def digital_write():
    with nidaqmx.Task() as task:
        task.co_channels.add_co_pulse_chan_time("Dev1/port0/line1")
        value = task.read()
        print(value)
