from src.blocks import Blocks, Stimulation
from src.controls import DAQ, Light, Camera, Stimuli
from src.signal_generator import square_signal

instruments1 = {
    'lights': [Light('port1', 'ir'), Light('port2', 'red'), Light('port3', 'green'), Light('port4', 'blue')],
    'stimuli': [Stimuli('port5', 'name')],
    'camera': Camera('port6', 'name'),
    'ports': {
        'lights': 'port1/line0:3',
        'stimuli': 'port2/line1',
        'camera': 'port3/line1'
    }
}

instruments2 = {
    'lights': [Light('port1', 'ir'), Light('port2', 'red'), Light('port3', 'green')],
    'stimuli': [Stimuli('port5', 'name')],
    'camera': Camera('port6', 'name'),
    'ports': {
        'lights': 'port1/line0:3',
        'stimuli': 'port2/line1',
        'camera': 'port3/line1'
    }
}

new_daq = DAQ('acquisition', instruments1)
other_daq = DAQ('acquisition', instruments2)

a = Stimulation(other_daq, 1, 0.004, 4, 0, delay=1, pulse_type='random-square')
b = Stimulation(new_daq, 1, 0.01, 12, 0.01, delay=5, pulse_type='random-square')
c = Blocks([a], iterations=2)
d = Blocks([b], iterations=3)
e = Blocks([c,d], delay=2, iterations=2)
a.run()
