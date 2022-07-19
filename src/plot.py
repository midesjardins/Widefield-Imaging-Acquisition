from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import sys
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QCheckBox, QTabWidget

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class PlotWindow(QDialog):
    def __init__(self, subplots=False, parent=None):
        """ Initialize the plot window 
        
        Args:
            subplots (bool): Whether to use subplots or not
            parent (QWidget): The parent widget
        """
        super(PlotWindow, self).__init__(parent)
        if subplots:
            self.figure, self.axis = plt.subplots(3, sharex=True)
            for axis in range(3):
                self.axis[axis].get_yaxis().set_visible(False)
        else:
            self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.vertical_lines = []

    def clear(self):
        """ Clear each axis of the plot """
        plt.figure(self.figure.number)
        plt.ion()
        try:
            for axis in range(3):
                self.axis[axis].clear()
        except Exception:
            plt.clf()
        self.vertical_lines = []

    def plot(self, x, y, root, index=0):
        """ Plot the given data on the plot window 
        
        Args:
            x (array): The x-values of the data
            y (array): The y-values of the data
            root (bool): If the plotted block is the root block
            index (int): The index of the axis to plot on
            """
        plt.figure(self.figure.number)
        try:
            self.axis[index].plot(x, y)
        except Exception:
            plt.plot(x, y)
        if root:
            self.vertical_lines.append(self.axis[index].axvline(x=0, color="red"))
