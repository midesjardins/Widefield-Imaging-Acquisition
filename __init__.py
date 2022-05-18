from pylablib.devices import IMAQ
from src.blocks import Experiment, Block, Stimulation
from src.controls import DAQ, Instrument, Camera
from PIL import Image as im
from matplotlib import pyplot as plt
import time



lights1 =  [Instrument('port0/line3', 'ir'), Instrument('port0/line0', 'red'), Instrument('port0/line2', 'green'), Instrument('port0/line1', 'blue')]
stimuli1 = [Instrument('ao1', 'air-pump')]
camera1 =  Camera('img0', 'name')

other_daq = DAQ('dev1',lights1, stimuli1, camera1)

a = Stimulation(other_daq, 1, 0.2, 3, 0, delay=0, pulse_type='random-square')
b = Stimulation(other_daq, 1, 0.1, 8, 0.01, delay=0, pulse_type='random-square')
c = Block([a], iterations=10)
d = Block([b], iterations=3)
e = Block([c,d], delay=2, iterations=2)
f = Experiment(a, 40, 10, "Lola", "data", other_daq)
f.start()


errors = 0
for i, frame in enumerate(camera1.frames):
    print(i)
    try:
        plt.imshow(frame, interpolation='nearest')
        plt.show()
    except Exception:
        errors +=1
        print(f"# of Errors: {errors}")
'''
cam1 = IMAQ.IMAQCamera('img0')
attributes = cam1.set_grabber_attribute_value("FRAMEWAIT_MSEC")
images = cam1.snap()
print(images)'''
#plt.imshow(images, interpolation='nearest')
#plt.show()