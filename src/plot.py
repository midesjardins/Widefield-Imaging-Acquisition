from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import sys
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget

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
            self.axis[0].get_yaxis().set_visible(False)
            self.axis[1].get_yaxis().set_visible(False)
            self.axis[2].get_yaxis().set_visible(False)
        else:
            self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.vertical_lines = []
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def clear(self):
        """ Clear each axis of the plot """
        plt.figure(self.figure.number)
        plt.ion()
        self.axis[0].clear()
        self.axis[1].clear()
        self.axis[2].clear()
        self.vertical_lines = []

    def plot(self, x, y, root, index=0):
        """ Plot the given data on the plot window 
        
        Args:
            x (array): The x-values of the data
            y (array): The y-values of the data
            root (bool): If the plotted block is the root block
            index (int): The index of the axis to plot on
            """
        try:
            plt.figure(self.figure.number)
            self.axis[index].plot(x, y)
        except Exception as err:
            pass
        if root:
            self.vertical_lines.append(self.axis[index].axvline(x=0, color="red"))
