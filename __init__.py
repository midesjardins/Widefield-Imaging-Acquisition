from pylablib.devices import IMAQ
from src.blocks import Blocks, Stimulation
from src.controls import DAQ, Instrument, Camera
from PIL import Image as im
from matplotlib import pyplot as plt
import time



lights1 =  [Instrument('port0/line3', 'ir'), Instrument('port0/line0', 'red'), Instrument('port0/line2', 'green'), Instrument('port0/line1', 'blue')]
stimuli1 = [Instrument('ao1', 'air-pump')]
camera1 =  Camera('img0', 'name')

other_daq = DAQ('dev1',lights1, stimuli1, camera1)

a = Stimulation(other_daq, 2, 0.2, 10, 0, delay=0, pulse_type='random-square')
b = Stimulation(other_daq, 1, 0.1, 8, 0.01, delay=0, pulse_type='random-square')
c = Blocks([a], iterations=2)
d = Blocks([b], iterations=3)
e = Blocks([c,d], delay=2, iterations=2)
a.run()


for frame in camera1.frames:
    plt.imshow(frame, interpolation='nearest')
    plt.show()
'''
cam1 = IMAQ.IMAQCamera('img0')
attributes = cam1.set_grabber_attribute_value("FRAMEWAIT_MSEC")
images = cam1.snap()
print(images)'''
#plt.imshow(images, interpolation='nearest')
#plt.show()