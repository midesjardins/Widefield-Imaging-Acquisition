from operator import truediv
import sys
import time
import random
import os
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt, QLocale
import numpy as np
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QGridLayout, QLabel, QHBoxLayout, QLineEdit, QCheckBox, QPushButton, QStackedLayout, QTreeWidget, QComboBox, QMessageBox, QFileDialog, QTreeWidgetItem, QApplication, QAction, QMenuBar
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QIcon, QBrush, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import RectangleSelector
from threading import Thread
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.signal_generator import make_signal, random_square
from src.controls import DAQ, Instrument, Camera
from src.blocks import Stimulation, Block, Experiment


class PlotWindow(QDialog):
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def get_data(self, time_values, pulses, jitter, width=0.2):
        y_values = random_square(time_values, pulses, width, jitter)
        return y_values

    def clear(self):
        plt.figure(self.figure.number)
        plt.ion()
        plt.clf()

    def plot(self, x, y, root, color="b"):
        plt.figure(self.figure.number)
        plt.ion()
        plt.plot(x,y, color=color)
        if root:
            try:
                self.vertical_line
            except Exception:
                self.vertical_line = plt.axvline(0, ls='-', color='r', lw=1, zorder=10)
        else:
            try:
                self.vertical_line.remove()
            except Exception:
                pass
        #self.canvas.draw()


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Widefield Imaging Aquisition'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def closeEvent(self, *args, **kwargs):
        self.daq.stop_signal = True
        self.video_running = False
        self.daq.camera.cam.stop_acquisition()
        print("Closed")

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.plot_x_values = []
        self.plot_stim1_values = []
        self.plot_stim2_values = []
        self.elapsed_time = 0
        self.files_saved = False
        locale = QLocale(QLocale.English, QLocale.UnitedStates)
        self.onlyInt = QIntValidator()
        self.onlyFloat = QDoubleValidator()
        self.onlyFloat.setLocale(locale)
        self.onlyFloat.setNotation(QDoubleValidator.StandardNotation)

        self.onlyFramerate = QIntValidator()
        self.onlyFramerate.setRange(1, 57)
        self.onlyExposure = QIntValidator()
        self.onlyExposure.setRange(1,900)

        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignTop)

        self.experiment_settings_label = QLabel('Experiment Settings')
        self.experiment_settings_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.experiment_settings_label, 0, 0)

        self.experiment_settings_main_window = QVBoxLayout()
        self.experiment_name_window = QHBoxLayout()
        self.experiment_name = QLabel('Experiment Name')
        self.experiment_name_window.addWidget(self.experiment_name)
        self.experiment_name_cell = QLineEdit()
        self.experiment_name_window.addWidget(self.experiment_name_cell)
        self.experiment_settings_main_window.addLayout(self.experiment_name_window)

        self.mouse_id_window = QHBoxLayout()
        self.mouse_id_label = QLabel('Mouse ID')
        self.mouse_id_window.addWidget(self.mouse_id_label)
        self.mouse_id_cell = QLineEdit()
        self.mouse_id_window.addWidget(self.mouse_id_cell)
        self.experiment_settings_main_window.addLayout(self.mouse_id_window)

        self.directory_window = QHBoxLayout()
        self.directory_save_files_checkbox = QCheckBox()
        self.directory_save_files_checkbox.setText("Save")
        self.directory_save_files_checkbox.stateChanged.connect(self.enable_directory)
        #TODO Change for real function
        self.directory_window.addWidget(self.directory_save_files_checkbox)
        self.directory_choose_button = QPushButton("Select Directory")
        self.directory_choose_button.setIcon(QIcon("gui/icons/folder-plus.png"))
        #self.directory_choose_button.setIcon(QIcon(os.path.join("gui", "icons", "folder-plus.png")))
        self.directory_choose_button.setDisabled(True)
        self.directory_choose_button.clicked.connect(self.choose_directory)
        self.directory_window.addWidget(self.directory_choose_button)
        self.directory_cell = QLineEdit("")
        self.directory_cell.setReadOnly(True)
        self.directory_window.addWidget(self.directory_cell)
        self.experiment_settings_main_window.addLayout(self.directory_window)

        self.experiment_settings_main_window.addStretch()

        self.grid_layout.addLayout(self.experiment_settings_main_window, 1, 0)

        self.image_settings_label = QLabel('Image Settings')
        self.image_settings_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.image_settings_label, 0, 1)

        self.image_settings_main_window = QVBoxLayout()
        self.image_settings_main_window.setAlignment(Qt.AlignLeft)
        self.image_settings_main_window.setAlignment(Qt.AlignTop)

        self.framerate_window = QHBoxLayout()
        self.framerate_label = QLabel('Framerate')
        self.framerate_window.addWidget(self.framerate_label)
        self.framerate_cell = QLineEdit('30')
        self.framerate_cell.setValidator(self.onlyFramerate)
        self.framerate_cell.textChanged.connect(self.verify_exposure)
        self.framerate_window.addWidget(self.framerate_cell)
        self.image_settings_main_window.addLayout(self.framerate_window)

        self.exposure_window = QHBoxLayout()
        self.exposure_label = QLabel('Exposure (ms)')
        self.exposure_window.addWidget(self.exposure_label)
        self.exposure_cell = QLineEdit('10')
        self.exposure_cell.setValidator(self.onlyExposure)
        self.exposure_cell.textChanged.connect(self.verify_exposure)
        self.exposure_window.addWidget(self.exposure_cell)
        self.image_settings_main_window.addLayout(self.exposure_window)

        self.exposure_warning_label = QLabel("Invalid Exposure / Frame Rate")
        self.image_settings_main_window.addWidget(self.exposure_warning_label)
        self.exposure_warning_label.setStyleSheet("color: red")
        self.exposure_warning_label.setHidden(True)

        self.image_settings_second_window = QHBoxLayout()
        self.ir_checkbox = QCheckBox('Infrared')
        self.ir_checkbox.stateChanged.connect(self.check_lights)
        self.image_settings_second_window.addWidget(self.ir_checkbox)
        self.red_checkbox = QCheckBox('Red')
        self.red_checkbox.stateChanged.connect(self.check_lights)
        self.image_settings_second_window.addWidget(self.red_checkbox)
        self.green_checkbox = QCheckBox('Green')
        self.green_checkbox.stateChanged.connect(self.check_lights)
        self.image_settings_second_window.addWidget(self.green_checkbox)
        self.fluorescence_checkbox = QCheckBox('Blue')
        self.fluorescence_checkbox.stateChanged.connect(self.check_lights)
        self.image_settings_second_window.addWidget(self.fluorescence_checkbox)

        self.light_channel_layout = QHBoxLayout()
        self.preview_light_label = QLabel("Light Channel Preview")
        self.light_channel_layout.addWidget(self.preview_light_label)
        self.preview_light_combo = QComboBox()
        self.preview_light_combo.setEnabled(False)
        self.preview_light_combo.currentIndexChanged.connect(self.change_preview_light_channel)
        self.light_channel_layout.addWidget(self.preview_light_combo)

        self.image_settings_main_window.addLayout(self.image_settings_second_window)
        self.image_settings_main_window.addLayout(self.light_channel_layout)

        self.roi_buttons = QStackedLayout()

        self.roi_layout1 = QHBoxLayout()
        self.roi_layout1.setAlignment(Qt.AlignLeft)
        self.roi_layout1.setAlignment(Qt.AlignTop)
        self.roi_layout1.setContentsMargins(0, 0, 0, 0)
        self.reset_roi_button = QPushButton()
        self.reset_roi_button.setText("Reset ROI")
        self.reset_roi_button.setIcon(QIcon("gui/icons/zoom-out-area.png"))
        self.reset_roi_button.setEnabled(False)
        self.reset_roi_button.clicked.connect(self.reset_roi)
        self.roi_layout1.addWidget(self.reset_roi_button)

        self.set_roi_button = QPushButton()
        self.set_roi_button.setText("Set ROI")
        self.set_roi_button.setIcon(QIcon("gui/icons/zoom-in-area.png"))
        self.set_roi_button.clicked.connect(self.set_roi)
        self.roi_layout1.addWidget(self.set_roi_button)
        self.roi_layout1_container = QWidget()
        self.roi_layout1_container.setLayout(self.roi_layout1)

        self.roi_layout2 = QHBoxLayout()
        self.roi_layout2.setAlignment(Qt.AlignLeft)
        self.roi_layout2.setAlignment(Qt.AlignTop)
        self.roi_layout2.setContentsMargins(0, 0, 0, 0)
        self.cancel_roi_button = QPushButton()
        self.cancel_roi_button.setText("Cancel")
        self.cancel_roi_button.setIcon(QIcon("gui/icons/zoom-cancel.png"))
        self.cancel_roi_button.clicked.connect(self.cancel_roi)
        self.roi_layout2.addWidget(self.cancel_roi_button)

        self.save_roi_button = QPushButton()
        self.save_roi_button.setText("Save ROI")
        self.save_roi_button.setIcon(QIcon("gui/icons/zoom-check.png"))
        self.save_roi_button.clicked.connect(self.save_roi)
        self.roi_layout2.addWidget(self.save_roi_button)
        self.roi_layout2_container = QWidget()
        self.roi_layout2_container.setLayout(self.roi_layout2)

        self.roi_buttons.addWidget(self.roi_layout1_container)
        self.roi_buttons.addWidget(self.roi_layout2_container)

        self.image_settings_main_window.addLayout(self.roi_buttons)
        self.image_settings_main_window.addStretch()

        self.activate_live_preview_button = QPushButton()
        self.activate_live_preview_button.setText("Start Live Preview")
        self.activate_live_preview_button.setIcon(QIcon("gui/icons/video"))
        self.activate_live_preview_button.clicked.connect(self.open_live_preview_thread)

        self.deactivate_live_preview_button = QPushButton()
        self.deactivate_live_preview_button.setText("Stop Live Preview")
        self.deactivate_live_preview_button.setIcon(QIcon("gui/icons/video-off"))
        self.deactivate_live_preview_button.clicked.connect(self.stop_live)

        self.image_settings_main_window.addStretch()

        self.grid_layout.addLayout(self.image_settings_main_window, 1, 1)

        self.live_preview_label = QLabel('Live Preview')
        self.live_preview_label.setFont(QFont("IBM Plex Sans", 17))
        self.numpy = np.random.rand(1024, 1024)
        self.image_view = PlotWindow()
        self.plot_image = plt.imshow(self.numpy, cmap="binary_r", vmin=0, vmax=4096)
        self.plot_image.axes.get_xaxis().set_visible(False)
        self.plot_image.axes.axes.get_yaxis().set_visible(False)

        self.grid_layout.addWidget(self.live_preview_label, 0, 2)
        self.grid_layout.addWidget(self.image_view, 1, 2)

        self.stimulation_tree_label = QLabel('Stimulation Tree')
        self.stimulation_tree_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.stimulation_tree_label, 2, 0)

        self.stimulation_tree_window = QVBoxLayout()
        self.stimulation_tree = QTreeWidget()
        self.stimulation_tree.setHeaderLabels(["0 Name", "1 Iterations", "2 Delay", "3 Jitter", "4 Type", "5 Pulses",
                                              "6 Duration", "7 Jitter", "8 Width", "9 Frequency", "10 Duty", "11 Type2", "12 Pulses 2", "13 Jitter 2", "14 Width 2", "15 Frequency 2", "16 Duty 2", "17 Blank", "18 Canal 1", "19 Canal 2", "20 Valid"])
        for i in range(19):
            self.stimulation_tree.header().hideSection(i+1)
            pass
        self.stimulation_tree.setHeaderHidden(True)
        self.stimulation_tree.setColumnWidth(0, 330)
        self.stimulation_tree.currentItemChanged.connect(self.actualize_window)
        self.stimulation_tree_window.addWidget(self.stimulation_tree)

        self.stimulation_tree_switch_window = QStackedLayout()
        self.stimulation_tree_second_window = QHBoxLayout()
        self.stim_buttons_container = QWidget()
        self.delete_branch_button = QPushButton('Delete')
        self.delete_branch_button.setIcon(QIcon("gui/icons/trash.png"))
        self.delete_branch_button.clicked.connect(self.delete_branch)
        self.stimulation_tree_second_window.addWidget(self.delete_branch_button)
        self.add_brother_branch_button = QPushButton('Add Sibling')
        self.add_brother_branch_button.clicked.connect(self.add_brother)
        self.add_brother_branch_button.setIcon(QIcon("gui/icons/arrow-bar-down.png"))
        self.stimulation_tree_second_window.addWidget(self.add_brother_branch_button)
        self.add_child_branch_button = QPushButton('Add Child')
        self.add_child_branch_button.clicked.connect(self.add_child)
        self.add_child_branch_button.setIcon(QIcon("gui/icons/arrow-bar-right.png"))
        self.stimulation_tree_second_window.addWidget(self.add_child_branch_button)
        self.stim_buttons_container.setLayout(self.stimulation_tree_second_window)
        self.stimulation_tree_switch_window.addWidget(self.stim_buttons_container)

        self.new_branch_button = QPushButton("New Stimulation")
        self.new_branch_button.setIcon(QIcon("gui/icons/square-plus.png"))
        self.stimulation_tree_third_window = QHBoxLayout()
        self.stimulation_tree_third_window.addWidget(self.new_branch_button)
        self.stim_buttons_container2 = QWidget()
        self.stim_buttons_container2.setLayout(self.stimulation_tree_third_window)
        self.stimulation_tree_switch_window.addWidget(self.stim_buttons_container2)
        self.new_branch_button.clicked.connect(self.first_stimulation)
        self.grid_layout.addLayout(self.stimulation_tree_switch_window, 4, 0)

        self.stimulation_tree_switch_window.setCurrentIndex(1)
        self.grid_layout.addLayout(self.stimulation_tree_window, 3, 0)

        self.signal_adjust_label = QLabel('Signal Adjust')
        self.signal_adjust_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.signal_adjust_label, 2, 1)

        self.signal_adjust_superposed = QStackedLayout()
        self.stimulation_edit_layout = QVBoxLayout()
        self.stimulation_edit_layout.setContentsMargins(0, 0, 0, 0)

        self.canal_window = QVBoxLayout()
        self.canal_window.setAlignment(Qt.AlignLeft)
        self.canal_window.setAlignment(Qt.AlignTop)
        self.canal_window.setContentsMargins(0, 0, 0, 0)



        self.first_signal_first_canal_check = QCheckBox()
        self.first_signal_first_canal_check.stateChanged.connect(self.canals_to_tree)
        self.first_signal_first_canal_check.setText("Canal 1")
        self.canal_window.addWidget(self.first_signal_first_canal_check)



        self.stimulation_type_label = QLabel("Stimulation Type")
        self.stimulation_type_cell = QComboBox()
        self.stimulation_type_cell.addItem("square")
        self.stimulation_type_cell.addItem("random-square")
        self.stimulation_type_cell.addItem("Third")
        self.stimulation_type_cell.currentIndexChanged.connect(self.type_to_tree)
        self.stimulation_type_window = QHBoxLayout()
        self.stimulation_type_window.addWidget(self.stimulation_type_label)
        self.stimulation_type_window.addWidget(self.stimulation_type_cell)
        self.canal_window.addLayout(self.stimulation_type_window)

        self.different_signals_window = QStackedLayout()
        self.canal_window.addLayout(self.different_signals_window)

        self.first_signal_second_canal_check = QCheckBox()
        self.first_signal_second_canal_check.stateChanged.connect(self.canals_to_tree)
        self.first_signal_second_canal_check.setText("Canal 2")
        self.canal_window.addWidget(self.first_signal_second_canal_check)

        self.stimulation_type_label2 = QLabel("Stimulation Type")
        self.stimulation_type_cell2 = QComboBox()
        self.stimulation_type_cell2.addItem("square")
        self.stimulation_type_cell2.addItem("random-square")
        self.stimulation_type_cell2.addItem("Third")
        self.stimulation_type_cell2.currentIndexChanged.connect(self.type_to_tree)
        self.stimulation_type_window2 = QHBoxLayout()
        self.stimulation_type_window2.addWidget(self.stimulation_type_label2)
        self.stimulation_type_window2.addWidget(self.stimulation_type_cell2)
        self.canal_window.addLayout(self.stimulation_type_window2)

        self.different_signals_window2 = QStackedLayout()
        self.canal_window.addLayout(self.different_signals_window2)

        self.stimulation_name_label = QLabel("Stimulation Name")
        self.stimulation_name_cell = QLineEdit()
        self.stimulation_name_cell.textEdited.connect(self.name_to_tree)
        self.stimulation_name_window = QHBoxLayout()
        self.stimulation_name_window.addWidget(self.stimulation_name_label)
        self.stimulation_name_window.addWidget(self.stimulation_name_cell)
        self.stimulation_edit_layout.addLayout(self.stimulation_name_window)

        self.first_signal_duration_window = QHBoxLayout()
        self.first_signal_type_duration_label = QLabel("Duration (s)")
        self.first_signal_duration_window.addWidget(self.first_signal_type_duration_label)
        self.first_signal_type_duration_cell = QLineEdit()
        self.first_signal_duration_window.addWidget(self.first_signal_type_duration_cell)
        self.first_signal_type_duration_cell.setValidator(self.onlyFloat)
        self.first_signal_type_duration_cell.textEdited.connect(self.signal_to_tree)
        self.stimulation_edit_layout.addLayout(self.first_signal_duration_window)

        #self.stimulation_edit_layout.addLayout(self.stimulation_type_window)
        self.stimulation_edit_layout.addLayout(self.canal_window)



        self.first_signal_type_window = QVBoxLayout()
        self.first_signal_type_window.setAlignment(Qt.AlignLeft)
        self.first_signal_type_window.setAlignment(Qt.AlignTop)
        self.first_signal_type_window.setContentsMargins(0, 0, 0, 0)
        self.first_signal_type_container = QWidget()
        self.first_signal_type_container.setLayout(self.first_signal_type_window)

        self.first_signal_type_window2 = QVBoxLayout()
        self.first_signal_type_window2.setAlignment(Qt.AlignLeft)
        self.first_signal_type_window2.setAlignment(Qt.AlignTop)
        self.first_signal_type_window2.setContentsMargins(0, 0, 0, 0)
        self.first_signal_type_container2 = QWidget()
        self.first_signal_type_container2.setLayout(self.first_signal_type_window2)
        #self.stimulation_edit_layout.addLayout(self.first_signal_duration_window)
        #self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.first_signal_pulses_window = QHBoxLayout()
        self.first_signal_type_pulses_label = QLabel("Pulses")
        self.first_signal_pulses_window.addWidget(self.first_signal_type_pulses_label)
        self.first_signal_type_pulses_cell = QLineEdit()
        self.first_signal_type_pulses_cell.setValidator(self.onlyInt)
        self.first_signal_type_pulses_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_pulses_window.addWidget(self.first_signal_type_pulses_cell)

        self.first_signal_pulses_window2 = QHBoxLayout()
        self.first_signal_type_pulses_label2 = QLabel("Pulses")
        self.first_signal_pulses_window2.addWidget(self.first_signal_type_pulses_label2)
        self.first_signal_type_pulses_cell2 = QLineEdit()
        self.first_signal_type_pulses_cell2.setValidator(self.onlyInt)
        self.first_signal_type_pulses_cell2.textEdited.connect(self.signal_to_tree)
        self.first_signal_pulses_window2.addWidget(self.first_signal_type_pulses_cell2)

        self.first_signal_jitter_window = QHBoxLayout()
        self.first_signal_type_jitter_label = QLabel("Jitter (s)")
        self.first_signal_jitter_window.addWidget(self.first_signal_type_jitter_label)
        self.first_signal_type_jitter_cell = QLineEdit()
        self.first_signal_type_jitter_cell.setValidator(self.onlyFloat)
        self.first_signal_type_jitter_cell.setText("0")
        self.first_signal_type_jitter_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_jitter_window.addWidget(self.first_signal_type_jitter_cell)

        self.first_signal_jitter_window2 = QHBoxLayout()
        self.first_signal_type_jitter_label2 = QLabel("Jitter (s)")
        self.first_signal_jitter_window2.addWidget(self.first_signal_type_jitter_label2)
        self.first_signal_type_jitter_cell2 = QLineEdit()
        self.first_signal_type_jitter_cell2.setValidator(self.onlyFloat)
        self.first_signal_type_jitter_cell2.setText("0")
        self.first_signal_type_jitter_cell2.textEdited.connect(self.signal_to_tree)
        self.first_signal_jitter_window2.addWidget(self.first_signal_type_jitter_cell2)

        self.first_signal_width_window = QHBoxLayout()
        self.first_signal_type_width_label = QLabel("Width (s)")
        self.first_signal_width_window.addWidget(self.first_signal_type_width_label)
        self.first_signal_type_width_cell = QLineEdit()
        self.first_signal_type_width_cell.setValidator(self.onlyFloat)
        self.first_signal_type_width_cell.setText("0")
        self.first_signal_type_width_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_width_window.addWidget(self.first_signal_type_width_cell)

        self.first_signal_width_window2 = QHBoxLayout()
        self.first_signal_type_width_label2 = QLabel("Width (s)")
        self.first_signal_width_window2.addWidget(self.first_signal_type_width_label2)
        self.first_signal_type_width_cell2 = QLineEdit()
        self.first_signal_type_width_cell2.setValidator(self.onlyFloat)
        self.first_signal_type_width_cell2.setText("0")
        self.first_signal_type_width_cell2.textEdited.connect(self.signal_to_tree)
        self.first_signal_width_window2.addWidget(self.first_signal_type_width_cell2)

        self.first_signal_type_window.addLayout(self.first_signal_pulses_window)
        self.first_signal_type_window.addLayout(self.first_signal_width_window)
        self.first_signal_type_window.addLayout(self.first_signal_jitter_window)

        self.first_signal_type_window2.addLayout(self.first_signal_pulses_window2)
        self.first_signal_type_window2.addLayout(self.first_signal_width_window2)
        self.first_signal_type_window2.addLayout(self.first_signal_jitter_window2)
# -------------------

        self.second_signal_type_window = QVBoxLayout()
        self.second_signal_type_container = QWidget()
        self.second_signal_type_window.setAlignment(Qt.AlignLeft)
        self.second_signal_type_window.setAlignment(Qt.AlignTop)
        self.second_signal_type_window.setContentsMargins(0, 0, 0, 0)
        self.second_signal_type_container.setLayout(self.second_signal_type_window)
        #self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.second_signal_type_window2 = QVBoxLayout()
        self.second_signal_type_container2 = QWidget()
        self.second_signal_type_window2.setAlignment(Qt.AlignLeft)
        self.second_signal_type_window2.setAlignment(Qt.AlignTop)
        self.second_signal_type_window2.setContentsMargins(0, 0, 0, 0)
        self.second_signal_type_container2.setLayout(self.second_signal_type_window2)

        self.second_signal_frequency_window = QHBoxLayout()
        self.second_signal_type_frequency_label = QLabel("Frequency (Hz)")
        self.second_signal_frequency_window.addWidget(self.second_signal_type_frequency_label)
        self.second_signal_type_frequency_cell = QLineEdit()
        self.second_signal_type_frequency_cell.setValidator(self.onlyFloat)
        self.second_signal_type_frequency_cell.textEdited.connect(self.signal_to_tree)
        self.second_signal_frequency_window.addWidget(self.second_signal_type_frequency_cell)

        self.second_signal_frequency_window2 = QHBoxLayout()
        self.second_signal_type_frequency_label2 = QLabel("Frequency (Hz)")
        self.second_signal_frequency_window2.addWidget(self.second_signal_type_frequency_label2)
        self.second_signal_type_frequency_cell2 = QLineEdit()
        self.second_signal_type_frequency_cell2.setValidator(self.onlyFloat)
        self.second_signal_type_frequency_cell2.textEdited.connect(self.signal_to_tree)
        self.second_signal_frequency_window2.addWidget(self.second_signal_type_frequency_cell2)

        self.second_signal_duty_window = QHBoxLayout()
        self.second_signal_type_duty_label = QLabel("Duty (%)")
        self.second_signal_duty_window.addWidget(self.second_signal_type_duty_label)
        self.second_signal_type_duty_cell = QLineEdit()
        self.second_signal_type_duty_cell.setValidator(self.onlyFloat)
        self.second_signal_type_duty_cell.textEdited.connect(self.signal_to_tree)
        self.second_signal_duty_window.addWidget(self.second_signal_type_duty_cell)

        self.second_signal_duty_window2 = QHBoxLayout()
        self.second_signal_type_duty_label2 = QLabel("Duty (%)")
        self.second_signal_duty_window2.addWidget(self.second_signal_type_duty_label2)
        self.second_signal_type_duty_cell2 = QLineEdit()
        self.second_signal_type_duty_cell2.setValidator(self.onlyFloat)
        self.second_signal_type_duty_cell2.textEdited.connect(self.signal_to_tree)
        self.second_signal_duty_window2.addWidget(self.second_signal_type_duty_cell2)

        self.second_signal_type_window.addLayout(self.second_signal_frequency_window)
        self.second_signal_type_window.addLayout(self.second_signal_duty_window)

        self.second_signal_type_window2.addLayout(self.second_signal_frequency_window2)
        self.second_signal_type_window2.addLayout(self.second_signal_duty_window2)

# -------------------

        self.third_signal_type_window = QVBoxLayout()
        self.third_signal_type_container = QWidget()
        self.third_signal_type_container.setLayout(self.third_signal_type_window)

        self.third_signal_type_window2 = QVBoxLayout()
        self.third_signal_type_container2 = QWidget()
        self.third_signal_type_container2.setLayout(self.third_signal_type_window2)
        #self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.third_signal_type_name = QLabel("signal3")
        self.third_signal_type_window.addWidget(self.third_signal_type_name)

        self.third_signal_type_name2 = QLabel("signal3")
        self.third_signal_type_window2.addWidget(self.third_signal_type_name2)

        self.different_signals_window.addWidget(self.second_signal_type_container)
        self.different_signals_window.addWidget(self.first_signal_type_container)
        self.different_signals_window.addWidget(self.third_signal_type_container)

        self.different_signals_window2.addWidget(self.second_signal_type_container2)
        self.different_signals_window2.addWidget(self.first_signal_type_container2)
        self.different_signals_window2.addWidget(self.third_signal_type_container2)

        self.stimulation_edit_container = QWidget()
        self.stimulation_edit_container.setLayout(self.stimulation_edit_layout)
        self.block_edit_layout = QVBoxLayout()
        self.block_edit_layout.setContentsMargins(0, 0, 0, 0)
        self.block_edit_layout.setAlignment(Qt.AlignLeft)
        self.block_edit_layout.setAlignment(Qt.AlignTop)

        self.block_name_label = QLabel("Block Name")
        self.block_name_cell = QLineEdit()
        self.block_name_cell.textEdited.connect(self.name_to_tree)
        self.block_name_window = QHBoxLayout()
        self.block_name_window.addWidget(self.block_name_label)
        self.block_name_window.addWidget(self.block_name_cell)
        self.block_edit_layout.addLayout(self.block_name_window)

        self.block_iterations_window = QHBoxLayout()
        self.block_iterations_label = QLabel("Iterations")
        self.block_iterations_cell = QLineEdit()
        self.block_iterations_cell.setValidator(self.onlyInt)
        self.block_iterations_cell.textEdited.connect(self.block_to_tree)
        self.block_iterations_window.addWidget(self.block_iterations_label)
        self.block_iterations_window.addWidget(self.block_iterations_cell)
        self.block_edit_layout.addLayout(self.block_iterations_window)

        self.block_delay_window = QHBoxLayout()
        self.block_delay_label = QLabel("Delay")
        self.block_delay_cell = QLineEdit()
        self.block_delay_cell.setValidator(self.onlyFloat)
        self.block_delay_cell.textEdited.connect(self.block_to_tree)
        self.block_delay_window = QHBoxLayout()
        self.block_delay_window.addWidget(self.block_delay_label)
        self.block_delay_window.addWidget(self.block_delay_cell)
        self.block_edit_layout.addLayout(self.block_delay_window)

        self.block_jitter_window = QHBoxLayout()
        self.block_jitter_label = QLabel("Jitter")
        self.block_jitter_cell = QLineEdit()
        self.block_jitter_cell.setValidator(self.onlyFloat)
        self.block_jitter_cell.textEdited.connect(self.block_to_tree)
        self.block_jitter_window = QHBoxLayout()
        self.block_jitter_window.addWidget(self.block_jitter_label)
        self.block_jitter_window.addWidget(self.block_jitter_cell)
        self.block_edit_layout.addLayout(self.block_jitter_window)

        self.block_edit_container = QWidget()
        self.block_edit_container.setLayout(self.block_edit_layout)
        self.signal_adjust_superposed.addWidget(self.stimulation_edit_container)
        self.signal_adjust_superposed.addWidget(self.block_edit_container)
        self.signal_adjust_superposed.addWidget(QLabel())
        self.signal_adjust_superposed.setCurrentIndex(2)
        self.grid_layout.addLayout(self.signal_adjust_superposed, 3, 1)

        self.signal_preview_label = QLabel('Signal Preview')
        self.signal_preview_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.signal_preview_label, 2, 2)

        self.buttons_main_window = QHBoxLayout()
        self.stop_button = QPushButton('Stop')
        self.stop_button.setIcon(QIcon("gui/icons/player-stop.png"))
        self.stop_button.clicked.connect(self.stop_while_running)
        self.stop_button.setEnabled(False)
        self.buttons_main_window.addWidget(self.stop_button)
        self.run_button = QPushButton('Run')
        self.run_button.setIcon(QIcon("gui/icons/player-play.png"))
        self.run_button.clicked.connect(self.run)
        self.run_button.setEnabled(False)
        self.buttons_main_window.addWidget(self.run_button)
        self.plot_window = PlotWindow()
        self.grid_layout.addWidget(self.plot_window, 3, 2)
        self.grid_layout.addLayout(self.buttons_main_window, 4, 2)
        self.open_daq_generation_thread()
        self.initialize_buttons()
        self.show()

    def run(self):
        self.daq.start_runtime = time.time()
        self.deactivate_buttons(buttons=self.enabled_buttons)
        print(str(time.time()-self.daq.start_runtime) + "to deactivate buttons")
        self.master_block = self.create_blocks()
        print(str(time.time()-self.daq.start_runtime) + "to generate master block")
        self.plot(item=self.stimulation_tree.invisibleRootItem())
        print(str(time.time()-self.daq.start_runtime) + "to plot the signal")
        self.root_time, self.root_signal = self.plot_x_values, [self.plot_stim1_values, self.plot_stim2_values]
        self.draw(root=True)
        print(str(time.time()-self.daq.start_runtime) + "to draw the signal")
        #self.open_signal_preview_thread()
        self.open_live_preview_thread()
        self.open_start_experiment_thread()

    def open_start_experiment_thread(self):
        self.start_experiment_thread = Thread(target=self.run_stimulation)
        self.start_experiment_thread.start()

    def run_stimulation(self):
        self.actualize_daq()
        self.experiment = Experiment(self.master_block, int(self.framerate_cell.text()), int(self.exposure_cell.text(
        )), self.mouse_id_cell.text(), self.directory_cell.text(), self.daq, name=self.experiment_name_cell.text())
        print(str(time.time()-self.daq.start_runtime) + "to intialize the experiment")
        self.daq.launch(self.experiment.name, self.root_time, self.root_signal)
        try:
            self.experiment.save(self.files_saved, self.roi_extent)
        except Exception:
            self.experiment.save(self.directory_save_files_checkbox.isChecked())
        self.stop()
        
    def open_live_preview_thread(self):
        self.live_preview_thread = Thread(target=self.start_live)
        self.live_preview_thread.start()

    def start_live(self):
        plt.ion()
        while self.camera.video_running is False:
            pass
        while self.camera.video_running is True:
            self.plot_image.set_array(self.camera.frames[self.live_preview_light_index::len(self.daq.lights)][-1])

    def stop_live(self):
        self.video_running = False

    def open_signal_preview_thread(self):
        self.signal_preview_thread = Thread(target=self.preview_signal)
        self.signal_preview_thread.start()

    def preview_signal(self):
        plt.ion()
        while self.stop_signal is False and self.daq.control_task.is_task_done() is False:
            try:
                self.plot_window.vertical_line.set_xdata([self.daq.current_signal_time,self.daq.current_signal_time])
                time.sleep(0.5)
            except Exception:
                time.sleep(0.5)
                pass

    def change_preview_light_channel(self):
        self.live_preview_light_index = self.preview_light_combo.currentIndex()

    def open_daq_generation_thread(self):
        self.daq_generation_thread = Thread(target=self.generate_daq)
        self.daq_generation_thread.start()

    def generate_daq(self):
        self.stimuli = [Instrument('ao0', 'air-pump'), Instrument('ao1', 'air-pump2')]
        self.camera = Camera('port0/line4', 'name')
        self.daq = DAQ('dev1', [], self.stimuli, self.camera, int(self.framerate_cell.text()), int(self.exposure_cell.text())/1000)

    def actualize_daq(self):
        lights = []
        if self.ir_checkbox.isChecked():
            lights.append(Instrument('port0/line3', 'ir'))
        if self.red_checkbox.isChecked():
            lights.append( Instrument('port0/line0', 'red'))
        if self.green_checkbox.isChecked():
            lights.append(Instrument('port0/line2', 'green'))
        if self.fluorescence_checkbox.isChecked():
            lights.append(Instrument('port0/line1', 'blue'))
        self.daq.lights = lights
        self.daq.framerate = int(self.framerate_cell.text())
        self.daq.exposure = int(self.exposure_cell.text())/1000
        self.camera.frames = []
        self.daq.stop_signal = False


        # TODO divide by 1000

    def create_blocks(self, item=None):
        try:
            if item is None:
                item = self.stimulation_tree.invisibleRootItem()
            if item.childCount() > 0:
                children = []
                for index in range(item.childCount()):
                    children.append(self.create_blocks(item=item.child(index)))
                if item == self.stimulation_tree.invisibleRootItem():
                    return Block("root", children)
                return Block(item.text(0), children, delay=int(item.text(2)), iterations=int(item.text(1)))
            else:
                duration = int(item.text(6))
                if item.text(18) == "True":
                    canal1 = True
                    sign_type, pulses, jitter, width, frequency, duty = self.get_tree_item_attributes(item, canal=1)
                else:
                    canal1=False
                    sign_type, pulses, jitter, width, frequency, duty = 0, 0, 0, 0, 0,0

                if item.text(19) == "True":
                    canal2 =True
                    sign_type2, pulses2, jitter2, width2, frequency2, duty2 = self.get_tree_item_attributes(item, canal=2)
                else:
                    sign_type2, pulses2, jitter2, width2, frequency2, duty2 = 0,0,0,0,0,0
                    canal2 = False
                return Stimulation(self.daq, duration, canal1=canal1, canal2=canal2, pulses=pulses, pulses2=pulses2, jitter=jitter, jitter2=jitter2, width=width, width2=width2, frequency=frequency, frequency2=frequency2, duty=duty, duty2=duty2, pulse_type1=sign_type, pulse_type2=sign_type2, name=item.text(0))
        except Exception as err:
            pass

    def get_tree_item_attributes(self, item, canal=1):
        if canal ==1:
            sign_type = item.text(4)
            duration = float(item.text(6))
            try:
                pulses = int(item.text(5))
                jitter = float(item.text(7))
                width = float(item.text(8))
            except Exception:
                pulses, jitter, width = 0, 0, 0
            try:
                frequency = float(item.text(9))
                duty = float(item.text(10))/100
            except Exception:
                frequency, duty = 0, 0
            return [sign_type, pulses, jitter, width, frequency, duty]

        elif canal ==2:
            sign_type = item.text(11)
            duration = float(item.text(6))
            try:
                pulses = int(item.text(12))
                jitter = float(item.text(13))
                width = float(item.text(14))
            except Exception:
                pulses, jitter, width = 0, 0, 0
            try:
                frequency = float(item.text(15))
                duty = float(item.text(16))/100
            except Exception:
                frequency, duty = 0, 0
            return [sign_type, pulses, jitter, width, frequency, duty]

    def stop(self):
        self.daq.stop_signal = True
        self.daq.stop_signal = True
        self.stop_live()
        self.activate_buttons(buttons = self.enabled_buttons)

    def stop_while_running(self):
        self.stop()
        if self.directory_save_files_checkbox.isChecked():
            self.stop_stimulation_dialog()

    def stop_stimulation_dialog(self):
        button = QMessageBox.question(self, "Save Files", "Do you want to save the current files?")
        if button == QMessageBox.Yes:
            print("Yes!")
        else:
            print("No!")


    def show_buttons(self, buttons):
        for button in buttons:
            button.setVisible(True)

    def hide_buttons(self, buttons):
        for button in buttons:
            button.setVisible(False)

    def activate_buttons(self, buttons):
        if buttons == self.enabled_buttons:
            if self.directory_save_files_checkbox.isChecked():
                self.directory_choose_button.setEnabled(True)
            self.stop_button.setDisabled(True)
        for button in buttons:
            button.setEnabled(True)

    def deactivate_buttons(self, buttons):
        if buttons == self.enabled_buttons:
            self.stop_button.setEnabled(True)
            self.stimulation_tree.clearSelection()
        for button in buttons:
            button.setDisabled(True)

    def choose_directory(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory_cell.setText(folder)

    def enable_directory(self):
        self.files_saved = self.directory_save_files_checkbox.isChecked()
        self.directory_choose_button.setEnabled(self.files_saved)
        self.directory_cell.setEnabled(self.files_saved)

    def first_stimulation(self):
        #self.run_button.setEnabled(True)
        stimulation_tree_item = QTreeWidgetItem()
        self.style_tree_item(stimulation_tree_item)
        self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
        self.stimulation_tree_switch_window.setCurrentIndex(0)
        self.stimulation_tree.setCurrentItem(stimulation_tree_item)
        self.canals_to_tree(first=True)
        self.type_to_tree(first=True)
        self.check_global_validity()

    def add_brother(self):
        if self.stimulation_tree.currentItem():
            stimulation_tree_item = QTreeWidgetItem()
            self.style_tree_item(stimulation_tree_item)
            parent = self.stimulation_tree.selectedItems()[0].parent()
            if parent:
                index = parent.indexOfChild(self.stimulation_tree.selectedItems()[0])
                parent.insertChild(index+1, stimulation_tree_item)
            else:
                self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
            self.type_to_tree(first=True)
            self.canals_to_tree(first=True)
            self.check_global_validity()

    def add_child(self):
        if self.stimulation_tree.currentItem():
            self.stimulation_tree.currentItem().setIcon(0, QIcon("gui/icons/package.png"))
            self.stimulation_tree.currentItem().setIcon(20, QIcon("gui/icons/alert-triangle.png"))
            stimulation_tree_item = QTreeWidgetItem()
            self.style_tree_item(stimulation_tree_item)
            self.stimulation_tree.selectedItems()[0].addChild(stimulation_tree_item)
            self.stimulation_tree.selectedItems()[0].setExpanded(True)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
            self.type_to_tree(first=True)
            self.canals_to_tree(first=True)
            self.check_global_validity()

    def delete_branch(self):
        try:
            parent = self.stimulation_tree.currentItem().parent()
            if parent.childCount() == 1:
                parent.setIcon(0, QIcon("gui/icons/wave-square.png"))
        except Exception:
            parent = self.stimulation_tree.invisibleRootItem()
        parent.removeChild(self.stimulation_tree.currentItem())
        self.check_global_validity()


    def style_tree_item(self, item):
        item.setIcon(20, QIcon("gui/icons/alert-triangle.png"))
        item.setForeground(0, QBrush(QColor(211, 211, 211)))
        item.setIcon(0, QIcon("gui/icons/wave-square.png"))
        item.setText(0, "No Name")


    def actualize_window(self):
        if self.stimulation_tree.currentItem():
            self.stimulation_tree_switch_window.setCurrentIndex(0)
        else:
            self.stimulation_tree_switch_window.setCurrentIndex(1)
        try:
            if self.stimulation_tree.currentItem().childCount() > 0:
                self.signal_adjust_superposed.setCurrentIndex(1)
            else:
                self.signal_adjust_superposed.setCurrentIndex(0)
        except AttributeError:
            self.signal_adjust_superposed.setCurrentIndex(2)
        self.tree_to_name()
        self.tree_to_block()
        self.tree_to_type()
        self.tree_to_signal()
        self.tree_to_canal()
        self.plot()
        self.draw()

    def name_to_tree(self):
        branch = self.stimulation_tree.currentItem()
        branch.setForeground(0, QBrush(QColor(0, 0, 0)))
        if branch.childCount() > 0:
            branch.setText(0, self.block_name_cell.text())
        else:
            branch.setText(0, self.stimulation_name_cell.text())

    def tree_to_name(self):
        try:
            if self.stimulation_tree.currentItem().childCount() > 0:
                if self.stimulation_tree.currentItem().text(0) != "No Name":
                    self.block_name_cell.setText(
                        self.stimulation_tree.currentItem().text(0))
                else:
                    self.block_name_cell.setText("")
            else:
                if self.stimulation_tree.currentItem().text(0) != "No Name":
                    self.stimulation_name_cell.setText(
                        self.stimulation_tree.currentItem().text(0))
                else:
                    self.stimulation_name_cell.setText("")
        except AttributeError:
            pass

    def type_to_tree(self, first=False):
        if first is True:
            self.stimulation_type_cell.setCurrentIndex(0)
            self.stimulation_type_cell2.setCurrentIndex(0)
        else:
            self.check_global_validity()
        self.different_signals_window.setCurrentIndex(self.stimulation_type_cell.currentIndex())
        self.different_signals_window2.setCurrentIndex(self.stimulation_type_cell2.currentIndex())
        #self.check_stim_validity()
        try:
            self.stimulation_tree.currentItem().setText(4, str(self.stimulation_type_cell.currentText()))
        except Exception:
            pass
        try:
            self.stimulation_tree.currentItem().setText(11, str(self.stimulation_type_cell2.currentText()))
        except Exception:
            pass
        try:
            self.plot()
            self.draw()
        except Exception:
            pass

    def tree_to_type(self):
        dico = {
            "square": 0,
            "random-square": 1,
            "Third": 2
        }
        try:
            self.stimulation_type_cell.setCurrentIndex(dico[self.stimulation_tree.currentItem().text(4)])
        except Exception:
            self.stimulation_type_cell.setCurrentIndex(0)

        try:
            self.stimulation_type_cell2.setCurrentIndex(dico[self.stimulation_tree.currentItem().text(11)])
        except Exception:
            self.stimulation_type_cell2.setCurrentIndex(0)

    def signal_to_tree(self):
        self.stimulation_tree.currentItem().setText(6, self.first_signal_type_duration_cell.text())

        self.stimulation_tree.currentItem().setText(5, self.first_signal_type_pulses_cell.text())
        self.stimulation_tree.currentItem().setText(7, self.first_signal_type_jitter_cell.text())
        self.stimulation_tree.currentItem().setText(8, self.first_signal_type_width_cell.text())
        self.stimulation_tree.currentItem().setText(9, self.second_signal_type_frequency_cell.text())
        self.stimulation_tree.currentItem().setText(10, self.second_signal_type_duty_cell.text())

        self.stimulation_tree.currentItem().setText(12, self.first_signal_type_pulses_cell2.text())
        self.stimulation_tree.currentItem().setText(13, self.first_signal_type_jitter_cell2.text())
        self.stimulation_tree.currentItem().setText(14, self.first_signal_type_width_cell2.text())
        self.stimulation_tree.currentItem().setText(15, self.second_signal_type_frequency_cell2.text())
        self.stimulation_tree.currentItem().setText(16, self.second_signal_type_duty_cell2.text())


        self.check_global_validity()
        self.plot()
        self.draw()


    def tree_to_signal(self):
        try:
            self.first_signal_type_pulses_cell.setText(self.stimulation_tree.currentItem().text(5))
            self.first_signal_type_duration_cell.setText(self.stimulation_tree.currentItem().text(6))
            self.first_signal_type_jitter_cell.setText(self.stimulation_tree.currentItem().text(7))
            self.first_signal_type_width_cell.setText(self.stimulation_tree.currentItem().text(8))
            self.second_signal_type_frequency_cell.setText(self.stimulation_tree.currentItem().text(9))
            self.second_signal_type_duty_cell.setText(self.stimulation_tree.currentItem().text(10))
            self.first_signal_type_pulses_cell2.setText(self.stimulation_tree.currentItem().text(12))
            self.first_signal_type_jitter_cell2.setText(self.stimulation_tree.currentItem().text(13))
            self.first_signal_type_width_cell2.setText(self.stimulation_tree.currentItem().text(14))
            self.second_signal_type_frequency_cell2.setText(self.stimulation_tree.currentItem().text(15))
            self.second_signal_type_duty_cell2.setText(self.stimulation_tree.currentItem().text(16))
        except Exception as err:
            pass

    def tree_to_block(self):
        try:
            self.block_iterations_cell.setText(self.stimulation_tree.currentItem().text(1))
            self.block_delay_cell.setText(self.stimulation_tree.currentItem().text(2))
            self.block_jitter_cell.setText(self.stimulation_tree.currentItem().text(3))
        except Exception:
            pass

    def block_to_tree(self):
        self.stimulation_tree.currentItem().setText(1, self.block_iterations_cell.text())
        self.stimulation_tree.currentItem().setText(2, self.block_delay_cell.text())
        self.stimulation_tree.currentItem().setText(3, self.block_jitter_cell.text())
        self.check_global_validity()
        self.plot()
        self.draw()

    def tree_to_canal(self):
        self.canal_running = True
        try:
            self.first_signal_first_canal_check.setChecked(self.boolean(self.stimulation_tree.currentItem().text(18)))
            self.first_signal_second_canal_check.setChecked(self.boolean(self.stimulation_tree.currentItem().text(19)))
            if self.first_signal_first_canal_check.isChecked():
                    self.activate_buttons(self.canal1buttons)
            else:
                self.deactivate_buttons(self.canal1buttons)
            if self.first_signal_second_canal_check.isChecked():
                self.activate_buttons(self.canal2buttons)
            else:
                self.deactivate_buttons(self.canal2buttons)
        except Exception:
            pass
        self.canal_running = False

    def canals_to_tree(self, int=0, first=False):
        if not self.canal_running:
            if first:
                self.stimulation_tree.currentItem().setText(18, "False")
                self.stimulation_tree.currentItem().setText(19, "False")
                self.deactivate_buttons(self.canal1buttons)
                self.deactivate_buttons(self.canal2buttons)
            else:
                self.stimulation_tree.currentItem().setText(18, str(self.first_signal_first_canal_check.isChecked()))
                if self.first_signal_first_canal_check.isChecked():
                    self.activate_buttons(self.canal1buttons)
                else:
                    self.deactivate_buttons(self.canal1buttons)
                if self.first_signal_second_canal_check.isChecked():
                    self.activate_buttons(self.canal2buttons)
                else:
                    self.deactivate_buttons(self.canal2buttons)
                self.stimulation_tree.currentItem().setText(19, str(self.first_signal_second_canal_check.isChecked()))
                self.first_signal_type_pulses_cell2.setEnabled(self.first_signal_second_canal_check.isChecked())
                self.check_global_validity()

    def enable_run(self):
        self.run_button.setDisabled(False)

    def disable_run(self):
        self.run_button.setDisabled(True)

    def count_lights(self):
        count = 0
        text = []
        for checkbox in [self.ir_checkbox, self.red_checkbox, self.green_checkbox, self.fluorescence_checkbox]:
            if checkbox.isChecked():
                count += 1
                text.append(checkbox.text())
        return (count, text)

    def check_lights(self):
        self.preview_light_combo.clear()
        if self.count_lights()[0] == 0:
            self.preview_light_combo.setEnabled(False)
        else:
            self.preview_light_combo.setEnabled(True)
        for i in range(4):
            if i < self.count_lights()[0]:
                self.preview_light_combo.addItem(self.count_lights()[1][i])
        self.check_global_validity()
    
    def check_global_validity(self, item=None):
        if item is None:
            item = self.stimulation_tree.invisibleRootItem()
            if self.check_block_validity(item) is True and (self.ir_checkbox.isChecked() or self.red_checkbox.isChecked() or self.green_checkbox.isChecked() or self.fluorescence_checkbox.isChecked()):
                self.enable_run()
            else:
                self.disable_run()
        elif item.childCount() > 0:
            self.set_icon(item, self.check_block_validity(item))
        else:
            self.set_icon(item, self.check_stim_validity(item))
        for child_index in range(item.childCount()):
            self.check_global_validity(item.child(child_index))

    def check_stim_validity(self, item=None):
        valid = True
        if item is None:
            item == self.stimulation_tree.currentItem()
        if item.text(6) == "":
            valid = False

        if item.text(18) == "True":
            if item.text(4) == "square" and item.text(9) != "" and item.text(10) != "":
                pass
            elif item.text(4) == "random-square" and item.text(5) != "" and item.text(7) != "" and item.text(8) != "":
                pass
            else:
                valid = False

        if item.text(19) == "True":
            if item.text(11) == "square" and item.text(15) != "" and item.text(16) != "":
                pass
            elif item.text(11) == "random-square" and item.text(12) != "" and item.text(13) != "" and item.text(4) != "":
                pass
            else:
                valid = False
        return valid

    def check_block_validity(self, item=None):
        valid = True
        if item is None:
            item = self.stimulation_tree.currentItem()
        if item.childCount() == 0:
            return self.check_stim_validity(item=item)
        if item == self.stimulation_tree.invisibleRootItem():
            if item.childCount() == 0:
                valid = False
        elif item.childCount() > 0:
            valid = item.text(1) != "" and item.text(2) != "" and item.text(3) != ""
        for child_index in range(item.childCount()):
            if not self.check_block_validity(item.child(child_index)):
                valid = False
        return valid

    def set_icon(self, item, valid):
        try:
            if valid:
                item.setIcon(20, QIcon("gui/icons/circle-check.png"))
            else:
                item.setIcon(20, QIcon("gui/icons/alert-triangle.png"))
        except Exception:
            pass


    def boolean(self, string):
        if string == "True":
            return True
        return False

    def clear_plot(self):
        self.plot_window.clear()

    def plot(self, item=None):
        try:
            if item is None:
                item = self.stimulation_tree.currentItem()
            if item.childCount() > 0:
                if item == self.stimulation_tree.invisibleRootItem():
                    jitter, block_delay, iterations_number = 0, 0, 1
                else:
                    jitter = float(item.text(3))
                    iterations_number = int(item.text(1))
                    block_delay = float(item.text(2))

                for iteration in range(iterations_number):
                    for index in range(item.childCount()):
                        child = item.child(index)
                        self.plot(child)
                    delay = round(block_delay + random.random()*jitter, 3)
                    time_values = np.linspace(0, delay, int(round(delay))*3000)
                    data = np.zeros(len(time_values))
                    time_values += self.elapsed_time
                    self.elapsed_time += delay
                    self.plot_x_values = np.concatenate((self.plot_x_values, time_values))
                    self.plot_stim1_values = np.concatenate((self.plot_stim1_values, data))
                    self.plot_stim2_values = np.concatenate((self.plot_stim2_values, data))
            else:
                duration = float(item.text(6))
                time_values = np.linspace(0, duration, int(round(duration))*3000)
                time_values += self.elapsed_time
                self.elapsed_time += duration
                self.plot_x_values = np.concatenate((self.plot_x_values, time_values))
                if item.text(18) == "True":
                    sign_type, pulses, jitter, width, frequency, duty = self.get_tree_item_attributes(item, canal=1)
                    data = make_signal(time_values, sign_type, width, pulses, jitter, frequency, duty)
                    self.plot_stim1_values = np.concatenate((self.plot_stim1_values, data))
                else:
                    self.plot_stim1_values = np.concatenate((self.plot_stim1_values, np.zeros(len(time_values))))

                if item.text(19) == "True":
                    sign_type2, pulses2, jitter2, width2, frequency2, duty2 = self.get_tree_item_attributes(item, canal=2)
                    data2 = make_signal(time_values, sign_type2, width2, pulses2, jitter2, frequency2, duty2)
                    self.plot_stim2_values = np.concatenate((self.plot_stim2_values, data2))
                else:
                    self.plot_stim2_values = np.concatenate((self.plot_stim2_values, np.zeros(len(time_values))))
        except Exception as err:
            self.plot_x_values = []
            self.plot_y_values = []
            self.elapsed_time = 0

    def draw(self, root=False):
        new_x_values = []
        new_stim1_values = []
        new_stim2_values = []
        try:
            time_start = time.time()
            sampling_indexes = np.linspace(0, len(self.plot_x_values)-1, round(3000+len(self.plot_x_values)/10), dtype=int)
            new_x_values = np.take(self.plot_x_values, sampling_indexes, 0)
            new_stim1_values = np.take(self.plot_stim1_values, sampling_indexes, 0)
            new_stim2_values = np.take(self.plot_stim2_values, sampling_indexes, 0)
            #self.plot_window.plot(new_x_values, new_stim1_values, root)
            #self.plot_window.plot(new_x_values, new_stim2_values, root, color="g")
            self.plot_window.plot(self.plot_x_values, self.plot_stim1_values, root)
            self.plot_window.plot(self.plot_x_values, self.plot_stim2_values, root, color="g")
            #print(f"plot time:{time.time()-time_start}")
            self.plot_x_values = []
            self.plot_stim1_values = []
            self.plot_stim2_values = []
            self.elapsed_time = 0
        except Exception as err:
            pass

    def set_roi(self):
        self.deactivate_buttons(buttons = self.enabled_buttons)
        self.stop_button.setEnabled(False)
        self.save_roi_button.setEnabled(False)
        self.roi_buttons.setCurrentIndex(1)

        def onselect_function(eclick, erelease):
            self.roi_extent = self.rect_selector.extents
            self.save_roi_button.setEnabled(True)

        self.rect_selector = RectangleSelector(self.plot_image.axes, onselect_function,
                                               drawtype='box', useblit=True,
                                               button=[1, 3],
                                               minspanx=5, minspany=5,
                                               spancoords='pixels',
                                               interactive=True)

    def reset_roi(self):
        plt.xlim(0, 1024)
        plt.ylim(0, 1024)
        self.roi_extent = None
        self.reset_roi_button.setEnabled(False)

    def cancel_roi(self):
        self.activate_buttons(buttons = self.enabled_buttons)
        self.roi_buttons.setCurrentIndex(0)
        self.rect_selector.clear()
        self.rect_selector = None

    def save_roi(self):
        self.activate_buttons(buttons = self.enabled_buttons)
        self.roi_buttons.setCurrentIndex(0)
        plt.ion()
        plt.xlim(self.roi_extent[0], self.roi_extent[1])
        plt.ylim(self.roi_extent[2], self.roi_extent[3])
        self.rect_selector.clear()
        self.rect_selector = None
        self.reset_roi_button.setEnabled(True)

    def verify_exposure(self):
        try:
            boolean_check = (int(self.exposure_cell.text())/1000+0.0015)*int(self.framerate_cell.text()) < 1
        except Exception:
            boolean_check = False
        self.exposure_warning_label.setHidden(boolean_check)
        self.check_run()

    def check_run(self):
        pass

    def check_if_thread_is_alive(self):
        try:
            if self.live_preview_thread.is_alive():
                print("Live preview thread is alive")
            else:
                print("Live preview thread is dead")
        except Exception as err:
            print(err)

        try:
            if self.start_experiment_thread.is_alive():
                print("Start Experiment thread is alive")
            else:
                print("Start experiment thread is dead")
        except Exception as err:
            print(err)

        try:
            if self.daq_generation_thread.is_alive():
                print("Daq Generation thread is alive")
            else:
                print("Daq generation thread is dead")
        except Exception as err:
            print(err)

        try:
            if self.signal_preview_thread.is_alive():
                print("Signal Preview thread is alive")
            else:
                print("Signal Preview thread is dead")
        except Exception as err:
            print(err)

    def initialize_buttons(self):
        self.canal1buttons = [self.stimulation_type_label, self.stimulation_type_cell, self.first_signal_type_pulses_label, self.first_signal_type_pulses_cell, self.first_signal_type_width_label, self.first_signal_type_width_cell, self.first_signal_type_jitter_label, self.first_signal_type_jitter_cell, self.second_signal_type_frequency_label, self.second_signal_type_frequency_cell, self.second_signal_type_duty_label, self.second_signal_type_duty_cell]
        self.canal2buttons = [self.stimulation_type_label2, self.stimulation_type_cell2, self.first_signal_type_pulses_label2, self.first_signal_type_pulses_cell2, self.first_signal_type_width_label2, self.first_signal_type_width_cell2, self.first_signal_type_jitter_label2, self.first_signal_type_jitter_cell2, self.second_signal_type_frequency_label2, self.second_signal_type_frequency_cell2, self.second_signal_type_duty_label2, self.second_signal_type_duty_cell2]
        self.enabled_buttons = [
            self.run_button,
            self.experiment_name_cell,
            self.mouse_id_cell,
            #self.directory_save_files_checkbox,
            self.directory_choose_button,
            self.set_roi_button,
            self.experiment_name,
            self.mouse_id_label,
            self.framerate_label,
            self.framerate_cell,
            self.exposure_cell,
            self.exposure_label,
            self.add_brother_branch_button,
            self.add_child_branch_button,
            self.delete_branch_button,
            self.red_checkbox,
            self.ir_checkbox,
            self.green_checkbox,
            self.fluorescence_checkbox,
            self.stimulation_name_label,
            self.stimulation_name_cell,
            self.stimulation_type_label,
            self.stimulation_type_cell,
            self.first_signal_first_canal_check,
            self.first_signal_second_canal_check,
            self.first_signal_type_duration_label,
            self.first_signal_type_duration_cell,
            self.first_signal_type_pulses_label,
            self.first_signal_type_pulses_cell,
            self.first_signal_type_width_label,
            self.first_signal_type_width_cell,
            self.first_signal_type_jitter_label,
            self.first_signal_type_jitter_cell,
            self.second_signal_type_frequency_label,
            self.second_signal_type_frequency_cell,
            self.second_signal_type_duty_label,
            self.second_signal_type_duty_cell,
            self.block_iterations_label,
            self.block_iterations_cell,
            self.block_delay_label,
            self.block_delay_cell,
            self.block_jitter_label,
            self.block_jitter_cell,
            self.block_name_label,
            self.block_name_cell,
            self.activate_live_preview_button,
            self.deactivate_live_preview_button,
            self.stimulation_tree
        ]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("IBM Plex Sans")
    app.setFont(font)
    ex = App()
    sys.exit(app.exec_())
