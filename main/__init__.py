from blocks import Blocks, Stimulation
from controls import DAQ, Instrument

instruments = {
    'infrared': Instrument('port1', 'name'),
    'red': Instrument('port2', 'name'),
    'green': Instrument('port3', 'name'),
    'blue': Instrument('port4', 'name'),
    'air_pump': Instrument('port5', 'name'),
    'camera': Instrument('port6', 'name')
}
new_daq = DAQ('acquisition', instruments)

a = Stimulation(new_daq, 1, 0.04, 4, 0, delay=0, pulse_type='random-square')
b = Stimulation(new_daq, 200, 4, 8, 1, delay=50, pulse_type='random-square')
c = Blocks([a], iterations=2)
d = Blocks([b], iterations=3)
e = Blocks([c,d], delay=2, iterations=2)
a.run()