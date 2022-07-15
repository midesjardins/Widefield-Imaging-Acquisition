import sys
import time
import os
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt, QLocale
import numpy as np
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QStackedLayout,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QApplication,
    QSlider,
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QIcon, QBrush, QColor
from matplotlib.widgets import RectangleSelector
from threading import Thread

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.controls import DAQ, Instrument, Camera
from src.blocks import Experiment
from src.tree import Tree
from src.plot import PlotWindow
from src.calculations import (
    get_dictionary,
    shrink_array,
    frames_acquired_from_camera_signal,
    get_baseline_frame_indices,
    average_baseline,
    get_timecourse,
    get_dask_array
)


class App(QWidget):
    def __init__(self):
        """ Initialize the application """
        super().__init__()
        self.cwd = os.path.dirname(os.path.dirname(__file__))

        #self.frames = np.random.randint(0, 4096, (50, 1024, 1024))
        #self.frame_number = self.frames.shape[0]
        self.roi_extent = None
        self.image_index = 0
        self.previous_index = 0
        self.files_to_read = True

        self.initUI()

    def closeEvent(self, *args, **kwargs):
        """ Stop all processes when closing the application """
        self.files_to_read = False

    def initUI(self):
        """ Initialize the user interface """
        self.setWindowTitle("Brain Scout")
        self.setGeometry(10, 10, 640, 480)
        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignLeft)
        self.grid_layout.setAlignment(Qt.AlignTop)
        #self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.grid_layout)

        self.settings_window = QVBoxLayout()
        self.settings_window.setAlignment(Qt.AlignLeft)
        self.settings_window.setAlignment(Qt.AlignTop)
        self.grid_layout.addLayout(self.settings_window, 0, 0)

        self.settings_window2 = QVBoxLayout()
        self.settings_window2.setAlignment(Qt.AlignLeft)
        self.settings_window2.setAlignment(Qt.AlignTop)
        self.grid_layout.addLayout(self.settings_window2, 0, 1)

# ----
        self.directory_window = QHBoxLayout()
        self.directory_window.setAlignment(Qt.AlignLeft)
        self.directory_window.setAlignment(Qt.AlignTop)
        self.choose_directory_button = QPushButton("Select Directory")
        self.choose_directory_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "folder-plus.png"))
        )
        self.choose_directory_button.clicked.connect(self.choose_directory)
        self.directory_window.addWidget(self.choose_directory_button)
        self.directory_cell = QLineEdit("")
        self.directory_cell.setReadOnly(True)
        self.directory_window.addWidget(self.directory_cell)

        self.settings_window.addLayout(self.directory_window)

        #self.import_window = QHBoxLayout()
        #self.import_progress = QLabel("0% Imported")
        #self.import_window.addWidget(self.import_progress)
        #self.settings_window.addLayout(self.import_window)

# ----

        self.roi_buttons = QStackedLayout()
        self.roi_buttons.setAlignment(Qt.AlignLeft)
        self.roi_buttons.setAlignment(Qt.AlignTop)
        #self.roi_buttons.setContentsMargins(0, 0, 0, 0)
        self.roi_layout1 = QHBoxLayout()
        self.roi_layout1.setAlignment(Qt.AlignLeft)
        self.roi_layout1.setAlignment(Qt.AlignTop)
        #self.roi_layout1.setContentsMargins(0, 0, 0, 0)
        self.reset_roi_button = QPushButton("Reset ROI")
        self.reset_roi_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "zoom-out-area.png"))
        )
        self.reset_roi_button.setEnabled(False)
        self.reset_roi_button.clicked.connect(self.reset_roi)
        self.roi_layout1.addWidget(self.reset_roi_button)

        self.set_roi_button = QPushButton("Set ROI")
        self.set_roi_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "zoom-in-area.png"))
        )
        self.set_roi_button.clicked.connect(self.set_roi)
        self.roi_layout1.addWidget(self.set_roi_button)

        self.roi_layout1_container = QWidget()
        self.roi_layout1_container.setLayout(self.roi_layout1)

        self.roi_layout2 = QHBoxLayout()
        self.roi_layout2.setAlignment(Qt.AlignLeft)
        self.roi_layout2.setAlignment(Qt.AlignTop)
        #self.roi_layout2.setContentsMargins(0, 0, 0, 0)
        self.cancel_roi_button = QPushButton("Cancel")
        self.cancel_roi_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "zoom-cancel.png"))
        )
        self.cancel_roi_button.clicked.connect(self.cancel_roi)
        self.roi_layout2.addWidget(self.cancel_roi_button)

        self.save_roi_button = QPushButton("Save ROI")
        self.save_roi_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "zoom-check.png"))
        )
        self.save_roi_button.clicked.connect(self.save_roi)
        self.roi_layout2.addWidget(self.save_roi_button)
        self.roi_layout2_container = QWidget()
        self.roi_layout2_container.setLayout(self.roi_layout2)

        self.roi_buttons.addWidget(self.roi_layout1_container)
        self.roi_buttons.addWidget(self.roi_layout2_container)

        self.grid_layout.addLayout(self.roi_buttons, 2, 0)

        # -------------
        
        self.index_window = QVBoxLayout()
        self.current_index_window = QHBoxLayout()
        self.current_index_label = QLabel("Current Index:")
        self.current_index_window.addWidget(self.current_index_label)
        self.current_index = QLineEdit("0")
        self.current_index.textChanged.connect(self.adjust_index)
        self.current_index_window.addWidget(self.current_index)
        self.index_window.addLayout(self.current_index_window)
        self.start_index_window = QHBoxLayout()
        self.start_index_label = QLabel("Start Index:")
        self.start_index_window.addWidget(self.start_index_label)
        self.start_index = QLineEdit("0")
        self.start_index_window.addWidget(self.start_index)
        self.index_window.addLayout(self.start_index_window)
        self.end_index_window = QHBoxLayout()
        self.end_index_label = QLabel("End Index:")
        self.end_index_window.addWidget(self.end_index_label)
        self.end_index = QLineEdit("0")
        self.end_index_window.addWidget(self.end_index)
        self.index_window.addLayout(self.end_index_window)
        self.settings_window2.addLayout(self.index_window)
        #self.settings_window.addStretch()

        self.make_time_course_button = QPushButton("Generate Time Course")
        self.make_time_course_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "chart-line.png"))
        )
        self.make_time_course_button.clicked.connect(self.make_time_course)
        self.grid_layout.addWidget(self.make_time_course_button, 2 ,1)

   # -------
        self.slider_layout = QHBoxLayout()
        self.slider_layout.setAlignment(Qt.AlignLeft)
        self.slider_layout.setAlignment(Qt.AlignTop)
        #self.slider_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_layout.addWidget(QLabel("Start"))

        self.time_slider = QSlider(Qt.Horizontal, self)
        self.time_slider.setRange(0, 0)
        self.time_slider.setValue(0)
        self.time_slider.valueChanged.connect(self.adjust_time)
        self.slider_layout.addWidget(self.time_slider)
        self.slider_layout.addWidget(QLabel("End"))

        self.settings_window.addLayout(self.slider_layout)

    # -------------
        #self.graphics_layout =QHBoxLayout()
        self.image_view = PlotWindow()
        self.plot_image = plt.imshow(np.zeros((4096, 4096)), cmap="binary_r", vmin=0, vmax=4096)
        self.plot_image.axes.get_xaxis().set_visible(False)
        self.plot_image.axes.axes.get_yaxis().set_visible(False)
        self.grid_layout.addWidget(self.image_view, 1, 0)

        #self.graphics_layout.addWidget(self.image_view)

        self.time_course = PlotWindow(subplots=False)
        self.time_course.plot([1,2,3], [1,2,3], root=False)
        self.grid_layout.addWidget(self.time_course, 1, 1)
        #self.grid_layout.addLayout(self.graphics_layout, 1, 0)

    # -------------


        self.open_live_preview_thread()
        self.show()

    def choose_directory(self):
        """ Choose the directory where to save the files"""
        self.directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory_cell.setText(self.directory)
        self.frames = []
        self.open_import_thread()

    def open_import_thread(self):
        """ Open the thread that will import the frames"""
        self.import_thread = Thread(target=self.import_frames)
        self.import_thread.start()
    
    def import_frames(self):
        potential_files = os.listdir(self.directory)
        for file in potential_files:
            if ".npy" in file:
                self.concatenate_frames(file)
        self.frame_number = self.frames.shape[0]
        self.end_index.setText(f"{self.frame_number-1}")
        self.time_slider.setRange(0, self.frame_number-1)

    def concatenate_frames(self, file): 
        """ Concatenate the frames in the directory"""
        if len(self.frames) == 0:
            self.frames = np.load(os.path.join(self.directory, file))
        else:
            self.frames = np.concatenate((self.frames, np.load(os.path.join(self.directory, file))))

    def set_roi(self):
        """ Set the ROI"""
        self.roi_buttons.setCurrentIndex(1)
        self.cancel_roi_button.setEnabled(True)
        self.save_roi_button.setEnabled(False)

        def onselect_function(eclick, erelease):
            """ Save the ROI dimensions as attributes"""
            self.roi_extent = self.rect_selector.extents
            self.save_roi_button.setEnabled(True)

        self.rect_selector = RectangleSelector(
            self.plot_image.axes,
            onselect_function,
            drawtype="box",
            useblit=True,
            button=[1, 3],
            minspanx=5,
            minspany=5,
            spancoords="pixels",
            interactive=True,
        )

    def reset_roi(self):
        """ Reset the ROI"""
        plt.figure(self.image_view.figure.number)
        plt.xlim(0, 1024)
        plt.ylim(0, 1024)
        self.roi_extent = None
        self.reset_roi_button.setEnabled(False)
        self.set_roi_button.setEnabled(True)
        self.reset_roi_button.setEnabled(False)

    def cancel_roi(self):
        """ Cancel the ROI selection"""
        #self.activate_buttons(buttons=self.enabled_buttons)
        self.roi_buttons.setCurrentIndex(0)
        self.rect_selector.clear()
        self.rect_selector = None

    def save_roi(self):
        """ Save the ROI"""
        #self.activate_buttons(buttons=self.enabled_buttons)
        self.roi_buttons.setCurrentIndex(0)
        plt.figure(self.image_view.figure.number)
        plt.ion()
        plt.xlim(self.roi_extent[0], self.roi_extent[1])
        plt.ylim(self.roi_extent[2], self.roi_extent[3])
        self.rect_selector.clear()
        self.rect_selector = None
        self.reset_roi_button.setEnabled(True)
        self.set_roi_button.setEnabled(True)

    def adjust_index(self):
        """ Adjust the index"""
        try:
            self.time_slider.setValue(int(self.current_index.text()))
        except Exception:
            pass

    def adjust_time(self):
        self.image_index = self.time_slider.value()
        self.current_index.setText(str(self.image_index))

    def open_live_preview_thread(self):
        self.live_preview_thread = Thread(target=self.live_preview)
        self.live_preview_thread.start()

    def live_preview(self):
        plt.ion()
        while self.files_to_read:
            if self.image_index != self.previous_index:
                self.previous_index = self.image_index
                self.plot_image.set(array=self.frames[self.image_index])
            time.sleep(0.1)

    def make_time_course(self):
        try:
            if self.roi_extent:
                y_values = get_timecourse(shrink_array(self.frames, self.roi_extent), int(self.start_index.text()), int(self.end_index.text()))
            else:
                y_values = get_timecourse(self.frames, int(self.start_index.text()), int(self.end_index.text()))
            plt.figure(self.time_course.figure.number)
            plt.ion()
            plt.clf()
            plt.plot(y_values)
        except Exception as err:
            print(err)
            pass

    def activate_buttons(self, buttons):
        """ Activate the buttons in a list"""
        for button in buttons:
            button.setEnabled(True)

    def deactivate_buttons(self, buttons):
        """ Deactivate the buttons in a list"""
        for button in buttons:
            button.setDisabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("IBM Plex Sans")
    app.setFont(font)
    ex = App()
    sys.exit(app.exec_())