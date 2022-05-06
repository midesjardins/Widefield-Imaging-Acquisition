from src.blocks import Blocks, Stimulation
from src.controls import DAQ, Light, Camera, Stimuli

instruments = {
    'infrared': Light('port1', 'name'),
    'red': Light('port2', 'name'),
    'green': Light('port3', 'name'),
    'blue': Light('port4', 'name'),
    'air_pump': Stimuli('port5', 'name'),
    'camera': Camera('port6', 'name')
}
new_daq = DAQ('acquisition', instruments)

a = Stimulation(new_daq, 2, 0.04, 4, 0, delay=0, pulse_type='random-square')
b = Stimulation(new_daq, 200, 4, 8, 1, delay=50, pulse_type='random-square')
c = Blocks([a], iterations=2)
d = Blocks([b], iterations=3)
e = Blocks([c,d], delay=2, iterations=2)
a.run()