from blocks import Blocks, Stimulation


a = Stimulation(100, 4, 4, 1, delay=200, type='random-square')
b = Stimulation(200, 4, 8, 1, delay=50, type='random-square')
c = Blocks([a], iterations=2)
d = Blocks([b], iterations=3)
e = Blocks([c,d], delay=2, iterations=2)
e.run()
