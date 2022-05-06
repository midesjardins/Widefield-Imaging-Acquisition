from blocks import Blocks, Stimulation
from controls import DAQ, Instrument

instruments = {
    'infrared': Instrument('port1'),
    'red': Instrument('port2'),
    'green': Instrument('port3'),
    'blue': Instrument('port4'),
    'air_pump': Instrument('port5'),
    'camera': Instrument('port6')
}
new_daq = DAQ('acquisition', instruments)

a = Stimulation(100, 4, 4, 1, delay=200, pulse_type='random-square')
b = Stimulation(200, 4, 8, 1, delay=50, pulse_type='random-square')
c = Blocks([a], iterations=2)
d = Blocks([b], iterations=3)
e = Blocks([c,d], delay=2, iterations=2)
e.run()
