from src.blocks import Blocks, Stimulation
from src.controls import DAQ, Light, Camera, Stimuli

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
    'lights': [Light('port1', 'ir'), Light('port2', 'red'), Light('port3', 'green'),Light('port4', 'blue')],
    'stimuli': [Stimuli('port5', 'name')],
    'camera': Camera('port6', 'name'),
    'ports': {
        'lights': 'port0/line0:3',
        'stimuli': 'ao1',
        'camera': 'port2'
    }
}

new_daq = DAQ('dev1', instruments1)
other_daq = DAQ('dev1',instruments2)

a = Stimulation(other_daq, 5, 0.2, 10, 0, delay=0, pulse_type='random-square')
b = Stimulation(other_daq, 1, 0.1, 8, 0.01, delay=0, pulse_type='random-square')
c = Blocks([a], iterations=2)
d = Blocks([b], iterations=3)
e = Blocks([c,d], delay=2, iterations=2)
e.run()