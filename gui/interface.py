import sys
import time
import random
import os
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QGridLayout, QLabel, QHBoxLayout, QLineEdit, QCheckBox, QPushButton, QStackedLayout, QTreeWidget, QComboBox, QMessageBox, QFileDialog, QTreeWidgetItem, QApplication
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

    def plot(self, x, y):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y)
        self.canvas.draw()


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
        self.video_running = False

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.plot_x_values = []
        self.plot_y_values = []
        self.elapsed_time = 0
        self.files_saved = False
        self.onlyInt = QIntValidator()
        self.onlyFloat = QDoubleValidator()

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
        self.directory_window.addWidget(self.directory_save_files_checkbox)
        self.directory_choose_button = QPushButton("Select Directory")
        self.directory_choose_button.setIcon(QIcon("gui/icons/folder-plus.png"))
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
        self.framerate_cell.setValidator(self.onlyInt)
        self.framerate_cell.textChanged.connect(self.verify_exposure)
        self.framerate_window.addWidget(self.framerate_cell)
        self.image_settings_main_window.addLayout(self.framerate_window)

        self.exposure_window = QHBoxLayout()
        self.exposure_label = QLabel('Exposure (ms)')
        self.exposure_window.addWidget(self.exposure_label)
        self.exposure_cell = QLineEdit('10')
        self.exposure_cell.setValidator(self.onlyInt)
        self.exposure_cell.textChanged.connect(self.verify_exposure)
        self.exposure_window.addWidget(self.exposure_cell)
        self.image_settings_main_window.addLayout(self.exposure_window)

        self.exposure_warning_label = QLabel("Invalid Exposure / Frame Rate Combination")
        self.image_settings_main_window.addWidget(self.exposure_warning_label)
        self.exposure_warning_label.setStyleSheet("color: red")
        self.exposure_warning_label.setHidden(True)

        self.image_settings_second_window = QHBoxLayout()
        self.speckle_button = QCheckBox('Infrared')
        self.image_settings_second_window.addWidget(self.speckle_button)
        self.red_button = QCheckBox('Red')
        self.image_settings_second_window.addWidget(self.red_button)
        self.green_button = QCheckBox('Green')
        self.image_settings_second_window.addWidget(self.green_button)
        self.fluorescence_button = QCheckBox('Blue')
        self.image_settings_second_window.addWidget(self.fluorescence_button)
        self.image_settings_main_window.addLayout(self.image_settings_second_window)

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
        self.plot_image = plt.imshow(self.numpy, vmin=0, vmax=1000)
        self.plot_image.axes.get_xaxis().set_visible(False)
        self.plot_image.axes.axes.get_yaxis().set_visible(False)

        self.grid_layout.addWidget(self.live_preview_label, 0, 2)
        self.grid_layout.addWidget(self.image_view, 1, 2)

        self.stimulation_tree_label = QLabel('Stimulation Tree')
        self.stimulation_tree_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.stimulation_tree_label, 2, 0)

        self.stimulation_tree_window = QVBoxLayout()
        self.stimulation_tree = QTreeWidget()
        self.stimulation_tree.setHeaderLabels(["Name", "Iterations", "Delay", "Jitter", "Type", "Pulses",
                                              "Duration", "Jitter", "Width", "Frequency", "Duty", "Canal 1", "Canal 2", "Valid"])
        for i in range(12):
            self.stimulation_tree.header().hideSection(i+1)
        self.stimulation_tree.setHeaderHidden(True)
        self.stimulation_tree.setColumnWidth(0, 330)
        self.stimulation_tree.currentItemChanged.connect(self.actualize_tree)
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

        self.stimulation_name_label = QLabel("Stimulation Name")
        self.stimulation_name_cell = QLineEdit()
        self.stimulation_name_cell.textEdited.connect(self.name_to_tree)
        self.stimulation_name_window = QHBoxLayout()
        self.stimulation_name_window.addWidget(self.stimulation_name_label)
        self.stimulation_name_window.addWidget(self.stimulation_name_cell)
        self.stimulation_edit_layout.addLayout(self.stimulation_name_window)

        self.stimulation_type_label = QLabel("Stimulation Type")
        self.stimulation_type_cell = QComboBox()
        self.stimulation_type_cell.addItem("square")
        self.stimulation_type_cell.addItem("random-square")
        self.stimulation_type_cell.addItem("Third")
        self.stimulation_type_cell.currentIndexChanged.connect(self.type_to_tree)
        self.stimulation_type_window = QHBoxLayout()
        self.stimulation_type_window.addWidget(self.stimulation_type_label)
        self.stimulation_type_window.addWidget(self.stimulation_type_cell)
        self.stimulation_edit_layout.addLayout(self.stimulation_type_window)
        self.different_signals_window = QStackedLayout()

        self.first_signal_duration_window = QHBoxLayout()
        self.first_signal_type_duration_label = QLabel("Duration (s)")
        self.first_signal_duration_window.addWidget(self.first_signal_type_duration_label)
        self.first_signal_type_duration_cell = QLineEdit()
        self.first_signal_type_duration_cell.setValidator(self.onlyFloat)
        self.first_signal_type_duration_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_duration_window.addWidget(self.first_signal_type_duration_cell)

        self.canal_window = QHBoxLayout()
        self.first_signal_first_canal_check = QCheckBox()
        self.first_signal_first_canal_check.stateChanged.connect(self.canals_to_tree)
        self.first_signal_first_canal_check.setText("Canal 1")
        self.canal_window.addWidget(self.first_signal_first_canal_check)
        self.first_signal_second_canal_check = QCheckBox()
        self.first_signal_second_canal_check.stateChanged.connect(self.canals_to_tree)
        self.first_signal_second_canal_check.setText("Canal 2")
        self.canal_window.addWidget(self.first_signal_second_canal_check)
        self.stimulation_edit_layout.addLayout(self.canal_window)

        self.first_signal_type_window = QVBoxLayout()
        self.first_signal_type_window.setAlignment(Qt.AlignLeft)
        self.first_signal_type_window.setAlignment(Qt.AlignTop)
        self.first_signal_type_window.setContentsMargins(0, 0, 0, 0)
        self.first_signal_type_container = QWidget()
        self.first_signal_type_container.setLayout(self.first_signal_type_window)
        self.stimulation_edit_layout.addLayout(self.first_signal_duration_window)
        self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.first_signal_pulses_window = QHBoxLayout()
        self.first_signal_type_pulses_label = QLabel("Pulses")
        self.first_signal_pulses_window.addWidget(self.first_signal_type_pulses_label)
        self.first_signal_type_pulses_cell = QLineEdit()
        self.first_signal_type_pulses_cell.setValidator(self.onlyInt)
        self.first_signal_type_pulses_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_pulses_window.addWidget(self.first_signal_type_pulses_cell)

        self.first_signal_jitter_window = QHBoxLayout()
        self.first_signal_type_jitter_label = QLabel("Jitter (s)")
        self.first_signal_jitter_window.addWidget(self.first_signal_type_jitter_label)
        self.first_signal_type_jitter_cell = QLineEdit()
        self.first_signal_type_jitter_cell.setValidator(self.onlyFloat)
        self.first_signal_type_jitter_cell.setText("0")
        self.first_signal_type_jitter_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_jitter_window.addWidget(self.first_signal_type_jitter_cell)

        self.first_signal_width_window = QHBoxLayout()
        self.first_signal_type_width_label = QLabel("Width (s)")
        self.first_signal_width_window.addWidget(self.first_signal_type_width_label)
        self.first_signal_type_width_cell = QLineEdit()
        self.first_signal_type_width_cell.setValidator(self.onlyFloat)
        self.first_signal_type_width_cell.setText("0")
        self.first_signal_type_width_cell.textEdited.connect(self.signal_to_tree)
        self.first_signal_width_window.addWidget(self.first_signal_type_width_cell)

        self.first_signal_type_window.addLayout(self.first_signal_duration_window)
        self.first_signal_type_window.addLayout(self.first_signal_pulses_window)
        self.first_signal_type_window.addLayout(self.first_signal_width_window)
        self.first_signal_type_window.addLayout(self.first_signal_jitter_window)
# -------------------

        self.second_signal_type_window = QVBoxLayout()
        self.second_signal_type_container = QWidget()
        self.second_signal_type_window.setAlignment(Qt.AlignLeft)
        self.second_signal_type_window.setAlignment(Qt.AlignTop)
        self.second_signal_type_window.setContentsMargins(0, 0, 0, 0)
        self.second_signal_type_container.setLayout(self.second_signal_type_window)
        self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.second_signal_frequency_window = QHBoxLayout()
        self.second_signal_type_frequency_label = QLabel("Frequency (Hz)")
        self.second_signal_frequency_window.addWidget(self.second_signal_type_frequency_label)
        self.second_signal_type_frequency_cell = QLineEdit()
        self.second_signal_type_frequency_cell.setValidator(self.onlyFloat)
        self.second_signal_type_frequency_cell.textEdited.connect(self.signal_to_tree)
        self.second_signal_frequency_window.addWidget(self.second_signal_type_frequency_cell)

        self.second_signal_duty_window = QHBoxLayout()
        self.second_signal_type_duty_label = QLabel("Duty (%)")
        self.second_signal_duty_window.addWidget(self.second_signal_type_duty_label)
        self.second_signal_type_duty_cell = QLineEdit()
        self.second_signal_type_duty_cell.setValidator(self.onlyFloat)
        self.second_signal_type_duty_cell.textEdited.connect(self.signal_to_tree)
        self.second_signal_duty_window.addWidget(self.second_signal_type_duty_cell)

        self.second_signal_type_window.addLayout(self.second_signal_frequency_window)
        self.second_signal_type_window.addLayout(self.second_signal_duty_window)

# -------------------

        self.third_signal_type_window = QVBoxLayout()
        self.third_signal_type_container = QWidget()
        self.third_signal_type_container.setLayout(self.third_signal_type_window)
        self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.third_signal_type_name = QLabel("signal3")
        self.third_signal_type_window.addWidget(self.third_signal_type_name)

        self.different_signals_window.addWidget(self.second_signal_type_container)
        self.different_signals_window.addWidget(self.first_signal_type_container)
        self.different_signals_window.addWidget(self.third_signal_type_container)

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
        self.stop_button.clicked.connect(self.stop)
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
        self.generate_daq()
        self.initialize_buttons()
        self.show()

    def run(self):
        self.deactivate_buttons()
        self.master_block = self.create_blocks()
        self.plot(item=self.stimulation_tree.invisibleRootItem())
        self.root_time, self.root_signal = self.plot_x_values, self.plot_y_values
        self.draw()
        self.open_start_experiment_thread()

    def open_start_experiment_thread(self):
        self.open_live_preview_thread()
        self.start_experiment_thread = Thread(target=self.run_stimulation)
        self.start_experiment_thread.start()

    def run_stimulation(self):
        self.generate_daq()
        self.experiment = Experiment(self.master_block, int(self.framerate_cell.text()), int(self.exposure_cell.text(
        )), self.mouse_id_cell.text(), self.directory_cell.text(), self.daq, name=self.experiment_name_cell.text())
        self.experiment.start(self.root_time, self.root_signal, save=self.files_saved)
        self.stop(save=True)

    def generate_daq(self):
        self.lights = []
        if self.speckle_button.isChecked():
            self.lights.append(Instrument('port0/line3', 'ir'))
        if self.red_button.isChecked():
            self.lights.append( Instrument('port0/line0', 'red'))
        if self.green_button.isChecked():
            self.lights.append(Instrument('port0/line2', 'green'))
        if self.fluorescence_button.isChecked():
            self.lights.append(Instrument('port0/line1', 'blue'))
        self.stimuli = [Instrument('ao1', 'air-pump')]
        self.camera = Camera('img0', 'name')
        self.daq = DAQ('dev1', self.lights, self.stimuli, self.camera, int(
            self.framerate_cell.text()), int(self.exposure_cell.text())/1000, self)

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
                sign_type, duration, pulses, jitter, width, frequency, duty = self.get_tree_item_attributes(item) 
                return Stimulation(self.daq, duration, width=width, pulses=pulses, jitter=jitter, frequency=frequency, duty=duty, delay=0, pulse_type=sign_type, name=item.text(0))
        except Exception as err:
            print(err)
            pass

    def get_tree_item_attributes(self, item):
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
        return [sign_type, duration, pulses, jitter, width, frequency, duty]

    def stop(self, save=True):
        self.activate_buttons()
        self.stop_live()
        if save is not True and self.directory_save_files_checkbox.isChecked() is True:
            self.stop_stimulation_dialog()

    def stop_stimulation_dialog(self):
        button = QMessageBox.question(
            self, "Save Files", "Do you want to save the current files?")
        if button == QMessageBox.Yes:
            print("Yes!")
        else:
            print("No!")

    def deactivate_buttons(self):
        for button in self.enabled_buttons:
            button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.stimulation_tree.clearSelection()

    def activate_buttons(self):
        for button in self.enabled_buttons:
            button.setEnabled(True)
        if self.directory_save_files_checkbox.isChecked():
            self.directory_choose_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def choose_directory(self):
        folder = str(QFileDialog.getExistingDirectory(
            self, "Select Directory"))
        self.directory_cell.setText(folder)

    def enable_directory(self):
        boolean_result = self.directory_save_files_checkbox.isChecked()
        self.files_saved = boolean_result
        self.directory_choose_button.setDisabled(not boolean_result)
        self.directory_cell.setDisabled(not boolean_result)

    def delete_branch(self):
        try:
            root = self.stimulation_tree.invisibleRootItem()
            parent = self.stimulation_tree.currentItem().parent()
            if parent.childCount() == 1:
                parent.setIcon(0, QIcon("gui/icons/wave-square.png"))
            parent.removeChild(self.stimulation_tree.currentItem())
        except Exception:
            root.removeChild(self.stimulation_tree.currentItem())
            if root.childCount() == 0:
                self.run_button.setEnabled(False)
        self.actualize_tree()

    def add_brother(self):
        if self.stimulation_tree.currentItem():
            stimulation_tree_item = QTreeWidgetItem()
            self.style_tree_item(stimulation_tree_item)
            parent = self.stimulation_tree.selectedItems()[0].parent()
            if parent:
                index = parent.indexOfChild(
                    self.stimulation_tree.selectedItems()[0])
                parent.insertChild(index+1, stimulation_tree_item)
            else:
                self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
            self.type_to_tree(first=True)
            self.canals_to_tree(first=True)
        else:
            pass

    def add_child(self):
        if self.stimulation_tree.currentItem():
            self.stimulation_tree.currentItem().setIcon(0, QIcon("gui/icons/package.png"))
            self.stimulation_tree.currentItem().setText(1, "1")
            self.stimulation_tree.currentItem().setIcon(13, QIcon("gui/icons/alert-triangle.png"))
            stimulation_tree_item = QTreeWidgetItem()
            self.style_tree_item(stimulation_tree_item)
            self.stimulation_tree.selectedItems()[0].addChild(stimulation_tree_item)
            self.stimulation_tree.selectedItems()[0].setExpanded(True)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
            self.type_to_tree(first=True)
            self.canals_to_tree(first=True)
        else:
            pass

    def first_stimulation(self):
        self.run_button.setEnabled(True)
        stimulation_tree_item = QTreeWidgetItem()
        self.style_tree_item(stimulation_tree_item)
        self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
        self.stimulation_tree_switch_window.setCurrentIndex(0)
        self.stimulation_tree.setCurrentItem(stimulation_tree_item)
        self.canals_to_tree(first=True)
        self.type_to_tree(first=True)

    def style_tree_item(self, item):
        item.setIcon(13, QIcon("gui/icons/alert-triangle.png"))
        item.setForeground(0, QBrush(QColor(211, 211, 211)))
        item.setIcon(0, QIcon("gui/icons/wave-square.png"))
        item.setText(0, "No Name")


    def actualize_tree(self):
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
        self.actualize_colors()
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
        self.different_signals_window.setCurrentIndex(
            self.stimulation_type_cell.currentIndex())
        try:
            self.stimulation_tree.currentItem().setText(
                4, str(self.stimulation_type_cell.currentText()))
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
            self.stimulation_type_cell.setCurrentIndex(
                dico[self.stimulation_tree.currentItem().text(4)])
        except Exception:
            self.stimulation_type_cell.setCurrentIndex(0)

    def signal_to_tree(self):
        self.stimulation_tree.currentItem().setText(5, self.first_signal_type_pulses_cell.text())
        self.stimulation_tree.currentItem().setText(6, self.first_signal_type_duration_cell.text())
        self.stimulation_tree.currentItem().setText(7, self.first_signal_type_jitter_cell.text())
        self.stimulation_tree.currentItem().setText(8, self.first_signal_type_width_cell.text())
        self.stimulation_tree.currentItem().setText(9, self.second_signal_type_frequency_cell.text())
        self.stimulation_tree.currentItem().setText(10, self.second_signal_type_duty_cell.text())

        if self.stimulation_type_cell.currentText() == "square":
            if self.first_signal_type_duration_cell.text() != "" and self.second_signal_type_frequency_cell.text() != "" and self.second_signal_type_duty_cell.text() != "":
                self.stimulation_tree.currentItem().setIcon(13, QIcon("gui/icons/circle-check.png"))
            else:
                self.stimulation_tree.currentItem().setIcon(13, QIcon("gui/icons/alert-triangle.png"))

        elif self.stimulation_type_cell.currentText() == "random-square":
            if self.first_signal_type_duration_cell.text() != "" and self.first_signal_type_pulses_cell.text() != "" and self.first_signal_type_jitter_cell.text() != "" and self.first_signal_type_width_cell.text() != "":
                self.stimulation_tree.currentItem().setIcon(13, QIcon("gui/icons/circle-check.png"))
            else:
                self.stimulation_tree.currentItem().setIcon(13, QIcon("gui/icons/alert-triangle.png"))
        self.actualize_colors()
        self.plot()
        self.draw()

    def tree_to_signal(self):
        try:
            self.second_signal_type_duty_cell.setText(self.stimulation_tree.currentItem().text(10))
            self.second_signal_type_frequency_cell.setText(self.stimulation_tree.currentItem().text(9))
            self.first_signal_type_pulses_cell.setText(self.stimulation_tree.currentItem().text(5))
            self.first_signal_type_duration_cell.setText(self.stimulation_tree.currentItem().text(6))
            self.first_signal_type_jitter_cell.setText(self.stimulation_tree.currentItem().text(7))
            self.first_signal_type_width_cell.setText(self.stimulation_tree.currentItem().text(8))
        except Exception:
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
        self.actualize_colors()
        self.plot()
        self.draw()

    def tree_to_canal(self):
        self.canal_running = True
        try:
            self.first_signal_first_canal_check.setChecked(self.boolean(self.stimulation_tree.currentItem().text(11)))
            self.first_signal_second_canal_check.setChecked(self.boolean(self.stimulation_tree.currentItem().text(12)))
        except Exception:
            pass
        self.canal_running = False

    def canals_to_tree(self, first=False):
        if not self.canal_running:
            if first:
                self.stimulation_tree.currentItem().setText(11, "False")
                self.stimulation_tree.currentItem().setText(12, "False")
            else:
                self.stimulation_tree.currentItem().setText(11, str(self.first_signal_first_canal_check.isChecked()))
                self.stimulation_tree.currentItem().setText(12, str(self.first_signal_second_canal_check.isChecked()))
            self.actualize_tree()

    def actualize_colors(self, item=None):
        if item == None:
            self.run_button.setEnabled(True)
            item = self.stimulation_tree.invisibleRootItem()
        for child_index in range(item.childCount()):
            if item.text(1) != "" and item.text(2) != "" and item.text(3) != "" and item != self.stimulation_tree.invisibleRootItem():
                item.setIcon(13, QIcon("gui/icons/circle-check.png"))
            elif item != self.stimulation_tree.invisibleRootItem():
                item.setIcon(13, QIcon("gui/icons/alert-triangle.png"))
                self.run_button.setEnabled(False)
            self.actualize_colors(item.child(child_index))
        if item.icon(13).pixmap(100).toImage() == QIcon("gui/icons/alert-triangle.png").pixmap(100).toImage():
            self.run_button.setEnabled(False)
            try:
                item.parent().setIcon(13, QIcon("gui/icons/alert-triangle.png"))
            except Exception as err:
                pass

    def boolean(self, string):
        if string == "True":
            return True
        return False

    def plot(self, item=None):
        try:
            if item is None:
                item = self.stimulation_tree.currentItem()
            if item.childCount() > 0:
                if item == self.stimulation_tree.invisibleRootItem():
                    jitter, delay, iterations_number = 0, 0, 1
                else:
                    jitter = float(item.text(7))
                    delay = round(float(self.block_delay_cell.text()) + random.random()*jitter, 3)
                    iterations_number = int(item.text(1))

                for iteration in range(iterations_number):
                    for index in range(item.childCount()):
                        child = item.child(index)
                        self.plot(child)
                        time_values = np.linspace(0, delay, int(round(delay))*3000)
                        data = np.zeros(len(time_values))
                        time_values += self.elapsed_time
                        self.elapsed_time += delay
                        self.plot_x_values = np.concatenate((self.plot_x_values, time_values))
                        self.plot_y_values = np.concatenate((self.plot_y_values, data))
            else:
                sign_type, duration, pulses, jitter, width, frequency, duty = self.get_tree_item_attributes(item)
                time_values = np.linspace(0, duration, int(round(duration))*3000)
                data = make_signal(time_values, sign_type, width, pulses, jitter, frequency, duty)
                if sign_type == "square":
                    data *= 5
                time_values += self.elapsed_time
                self.elapsed_time += duration
                self.plot_x_values = np.concatenate((self.plot_x_values, time_values))
                self.plot_y_values = np.concatenate((self.plot_y_values, data))
        except Exception as err:
            print(err)
            self.plot_x_values = []
            self.plot_y_values = []
            self.elapsed_time = 0

    def draw(self):
        new_x_values = []
        new_y_values = []
        try:
            sampling_indexes = np.linspace(0, len(self.plot_x_values)-1, 3000, dtype=int)
            new_x_values = np.take(self.plot_x_values, sampling_indexes, 0)
            new_y_values = np.take(self.plot_y_values, sampling_indexes, 0)
            self.plot_window.plot(new_x_values, new_y_values)
            self.plot_x_values = []
            self.plot_y_values = []
            self.elapsed_time = 0
        except Exception:
            pass


    def open_live_preview_thread(self):
        self.live_preview_thread = Thread(target=self.start_live)
        self.live_preview_thread.start()

    def start_live(self):
        plt.ion()
        self.video_running = True
        while self.video_running is True:
            try:
                self.plot_image.set_array(self.camera.frames[-1])
            except Exception as err:
                pass

    def stop_live(self):
        self.video_running = False

    def set_roi(self):
        self.deactivate_buttons()
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
        self.reset_roi_button.setEnabled(False)

    def cancel_roi(self):
        self.activate_buttons()
        self.roi_buttons.setCurrentIndex(0)
        self.rect_selector.clear()
        self.rect_selector = None

    def save_roi(self):
        self.activate_buttons()
        self.roi_buttons.setCurrentIndex(0)
        plt.ion()
        plt.xlim(self.roi_extent[0], self.roi_extent[1])
        plt.ylim(self.roi_extent[2], self.roi_extent[3])
        self.rect_selector.clear()
        self.rect_selector = None
        self.reset_roi_button.setEnabled(True)

    def verify_exposure(self):
        try:
            boolean_check =  (int(self.exposure_cell.text())/1000+0.0015)*int(self.framerate_cell.text()) < 1
        except Exception:
            boolean_check = False
        self.exposure_warning_label.setHidden(boolean_check)
        self.check_run()

    def check_run(self):
        pass

    def initialize_buttons(self):
        self.enabled_buttons = [
            self.run_button,
            self.experiment_name_cell,
            self.mouse_id_cell,
            self.directory_save_files_checkbox,
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
            self.red_button,
            self.speckle_button,
            self.green_button,
            self.fluorescence_button,
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
