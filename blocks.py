import time
import random

class stimulation:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return str(self.data)

    def run(self):
        print(self.data)



class blocks:
    def __init__(self, data, delay=0, iterations=1, jitter=0):
        self.data = data
        self.iterations = iterations
        self.delay = delay
        self.jitter = jitter

    def run(self):
        for item in self.data:
                item.run()
                print(self.delay + round(random.random(), 2) * self.jitter)
                time.sleep(self.delay + round(random.random(), 2) * self.jitter)