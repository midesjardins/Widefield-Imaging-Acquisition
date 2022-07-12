from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import sys
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class PlotWindow(QDialog):
    def __init__(self, subplots=False, parent=None):
        super(PlotWindow, self).__init__(parent)
        if subplots:
            self.figure, self.axis = plt.subplots(2, sharex=True)
            self.axis[0].get_yaxis().set_visible(False)
            self.axis[1].get_yaxis().set_visible(False)
        else:
            self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.vertical_lines = []
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.i = 0

    def clear(self):
        plt.figure(self.figure.number)
        plt.ion()
        self.axis[0].clear()
        self.axis[1].clear()
        self.vertical_lines = []

    def plot(self, x, y, root, color="#1CFFFB", subplots=False, index=0):
        plt.figure(self.figure.number)
        self.axis[index].plot(x, y)
        if root:
            self.vertical_lines.append(self.axis[index].axvline(x=0))