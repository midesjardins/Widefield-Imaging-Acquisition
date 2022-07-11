import scipy.signal as signal
import numpy as np
import matplotlib.pyplot as plt

def find_rising_indices(array):
    dy = np.diff(array)
    return np.concatenate(([0], np.where(abs(dy) > 0)[0]))


x = np.linspace(0, 10, 1000)
y = signal.square(2*np.pi*x,duty=0.3).clip(min=0)
new_x = np.linspace(0,10, 1000)
new_y = np.copy(y)
x_indices = find_rising_indices(y)
difference = x_indices[2] - x_indices[1] # difference of camera signal
extend = round(0.4*difference)
for index in x_indices:
    new_y[index-extend:index+extend] = 1


plt.plot(x, y)
plt.plot(new_x, new_y)
plt.show()

