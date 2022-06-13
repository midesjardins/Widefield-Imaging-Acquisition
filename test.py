import numpy as np
import time

first_array = np.random.randint(0,4096,(200,200))
second_array = np.random.randint(0,4096,(1024,1024))
show_array = np.zeros((1024,1024))
list = []

start_time = time.time()
for i in range(60):
    resized_array = second_array[0:200,0:200]
    new_array = np.divide(resized_array, first_array)
    list.append(new_array)
    show_array = np.zeros((1024,1024))
    show_array[0:200, 0:200] = new_array

print(time.time()-start_time)
