import sys
import time
import os
import matplotlib.pyplot as plt
from PyQt5.QtCore import QModelIndex, Qt, QLocale, qInstallMessageHandler
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
    QHeaderView,
    QDialog,
    QWizard,
)
from PyQt5.QtGui import (
    QIntValidator,
    QDoubleValidator,
    QFont,
    QIcon,
    QBrush,
    QColor,
    QPixmap,
)
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
)
import warnings

warnings.filterwarnings("ignore")


class App(QWidget):
    def __init__(self):
        """Initialize the application"""
        super().__init__()
        qInstallMessageHandler(self.handler)
        self.cwd = os.path.dirname(os.path.dirname(__file__))
        self.config = get_dictionary(os.path.join(self.cwd, "config.json"))
        self.ports = self.config["Ports"]
        self.elapsed_time = 0
        self.files_saved = False
        self.save_files_after_stop = False
        self.roi_extent = None
        self.max_exposure = 4096
        self.slider_values = {
            "Infrared": {"None": 4096, "Normal": 4096, "Logarithmic": 4096},
            "Red": {"None": 4096, "Normal": 4096, "Logarithmic": 4096},
            "Green": {"None": 4096, "Normal": 4096, "Logarithmic": 4096},
            "Blue": {"None": 4096, "Normal": 4096, "Logarithmic": 4096},
        }
        self.daq_generated = False
        self.onlyFloat = QDoubleValidator()
        self.onlyFloat.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.onlyFloat.setNotation(QDoubleValidator.StandardNotation)
        self.onlyFramerate = QIntValidator(1, 57, self)
        self.onlyExposure = QIntValidator(1, 900, self)
        self.start_container = QWidget()
        self.start_layout = QVBoxLayout()
        self.start_container.setLayout(self.start_layout)
        self.start_title = QLabel("Welcome to WideBrain!")
        self.start_title.setFont(QFont("IBM Plex Sans", 20, QFont.Bold))
        self.start_title.setAlignment(Qt.AlignCenter)
        self.start_image = QLabel()
        self.start_image.setPixmap(
            QPixmap(os.path.join(self.cwd, "assets", "logo-small.png"))
        )
        self.start_image.setAlignment(Qt.AlignCenter)
        self.start_description = QLabel("Choose the type of experiment you want to run")
        self.start_description.setFont(QFont("IBM Plex Sans", 14, QFont.Light))
        self.start_description.setWordWrap(True)
        self.start_description.setAlignment(Qt.AlignCenter)

        self.trigger_mode_button = QPushButton("Start in Trigger Mode")
        self.trigger_mode_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "bolt.png"))
        )
        self.trigger_mode_button.setFont(QFont("IBM Plex Sans", 15, QFont.Light))
        self.trigger_mode_button.clicked.connect(self.start_in_trigger_mode)

        self.acquisition_mode_button = QPushButton("Start in Acquisition Mode")
        self.acquisition_mode_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "camera.png"))
        )
        self.acquisition_mode_button.setFont(QFont("IBM Plex Sans", 15, QFont.Light))
        self.acquisition_mode_button.clicked.connect(self.start_in_acquisition_mode)

        self.start_buttons = QHBoxLayout()
        self.start_buttons.addWidget(self.trigger_mode_button)
        self.start_buttons.addWidget(self.acquisition_mode_button)

        self.start_layout.addWidget(self.start_title)
        self.start_layout.addWidget(self.start_image)
        self.start_layout.addWidget(self.start_description)
        self.start_layout.addLayout(self.start_buttons)

        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.start_container, 0, 0)

        self.setLayout(self.grid_layout)
        self.show()

    def start_in_trigger_mode(self):
        """Initialize the interface in trigger mode"""
        self.start_container.setParent(None)
        self.acquisition_mode = False
        self.initUI()

    def start_in_acquisition_mode(self):
        """Initialize the interface in acquisition mode"""
        self.start_container.setParent(None)
        self.acquisition_mode = True
        self.initUI()

    def closeEvent(self, *args, **kwargs):
        """Stop all processes when closing the application"""
        self.video_running = False
        try:
            self.camera.stop_signal = True
            self.camera.video_running = False
            self.daq.stop_signal = True
            self.daq.camera.cam.stop_acquisition()
            print("Program Closed")
        except Exception as err:
            pass
        self.check_if_thread_is_alive()

    def handler(*args, **kwargs):
        """Ignore Qt messages"""
        pass

    def initUI(self):
        """Initialize the user interface"""
        self.title = "Widefield Imaging Aquisition"
        self.dimensions = (10, 10, 640, 480)
        self.setWindowTitle(self.title)
        self.setGeometry(*self.dimensions)

        # self.grid_layout = QGridLayout()
        # self.setLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignTop)

        self.experiment_settings_label = QLabel("Experiment Settings")
        self.experiment_settings_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.experiment_settings_label, 0, 0)

        self.experiment_settings_main_window = QVBoxLayout()
        self.experiment_name_window = QHBoxLayout()
        self.experiment_name = QLabel("Experiment Name")
        self.experiment_name_window.addWidget(self.experiment_name)
        self.experiment_name_cell = QLineEdit()
        self.experiment_name_window.addWidget(self.experiment_name_cell)
        self.experiment_settings_main_window.addLayout(self.experiment_name_window)

        self.mouse_id_window = QHBoxLayout()
        self.mouse_id_label = QLabel("Mouse ID")
        self.mouse_id_window.addWidget(self.mouse_id_label)
        self.mouse_id_cell = QLineEdit()
        self.mouse_id_window.addWidget(self.mouse_id_cell)
        self.experiment_settings_main_window.addLayout(self.mouse_id_window)

        self.framerate_exposure_window = QHBoxLayout()
        self.exposure_window = QHBoxLayout()
        self.exposure_label = QLabel("Exposure (ms)")
        self.exposure_window.addWidget(self.exposure_label)
        self.exposure_cell = QLineEdit("10")
        self.exposure_cell.setValidator(self.onlyExposure)
        self.exposure_cell.textChanged.connect(self.verify_exposure)
        self.exposure_window.addWidget(self.exposure_cell)
        self.framerate_exposure_window.addLayout(self.exposure_window)
        self.framerate_window = QHBoxLayout()
        self.framerate_label = QLabel("Framerate")
        self.framerate_window.addWidget(self.framerate_label)
        self.framerate_cell = QLineEdit("30")
        self.framerate_cell.setValidator(self.onlyFramerate)
        self.framerate_cell.textChanged.connect(self.verify_exposure)
        self.framerate_window.addWidget(self.framerate_cell)
        self.framerate_exposure_window.addLayout(self.framerate_window)

        if self.acquisition_mode:
            self.experiment_settings_main_window.addLayout(
                self.framerate_exposure_window
            )

        self.exposure_warning_label = QLabel("Invalid Exposure / Frame Rate")
        if self.acquisition_mode:
            self.experiment_settings_main_window.addWidget(self.exposure_warning_label)
        self.exposure_warning_label.setStyleSheet("color: red")
        self.exposure_warning_label.setHidden(True)

        self.directory_window = QHBoxLayout()
        self.directory_save_files_checkbox = QCheckBox()
        self.directory_save_files_checkbox.setText("Save")
        self.directory_save_files_checkbox.stateChanged.connect(self.enable_directory)
        self.directory_window.addWidget(self.directory_save_files_checkbox)
        self.directory_choose_button = QPushButton("Select Directory")
        self.directory_choose_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "folder-plus.png"))
        )
        # self.directory_choose_button.setIcon(QIcon(os.path.join("gui", "icons", "folder-plus.png")))
        self.directory_choose_button.setDisabled(True)
        self.directory_choose_button.clicked.connect(self.choose_directory)
        self.directory_window.addWidget(self.directory_choose_button)
        self.directory_cell = QLineEdit("")
        self.directory_cell.setReadOnly(True)
        self.directory_window.addWidget(self.directory_cell)
        self.experiment_settings_main_window.addLayout(self.directory_window)
        self.trigger_checkbox = QCheckBox("Wait for Trigger")
        self.trigger_activated = False
        self.trigger_checkbox.stateChanged.connect(self.set_trigger)
        # self.experiment_settings_main_window.addWidget(self.trigger_checkbox)

        self.save_config_button = QPushButton("Save Config")
        self.save_config_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "save.png"))
        )
        self.save_config_button.clicked.connect(self.save_config)
        self.save_config_button.setEnabled(False)
        self.experiment_settings_main_window.addWidget(self.save_config_button)

        self.experiment_settings_main_window.addStretch()

        if self.acquisition_mode:
            self.grid_layout.addLayout(self.experiment_settings_main_window, 1, 0)
        else:
            self.grid_layout.addLayout(self.experiment_settings_main_window, 1, 0, 1, 2)

        self.image_settings_label = QLabel("Image Settings")
        self.image_settings_label.setFont(QFont("IBM Plex Sans", 17))
        if self.acquisition_mode:
            self.grid_layout.addWidget(self.image_settings_label, 0, 1)

        self.image_settings_main_window = QVBoxLayout()
        self.image_settings_main_window.setAlignment(Qt.AlignLeft)
        self.image_settings_main_window.setAlignment(Qt.AlignTop)

        self.image_settings_second_window = QHBoxLayout()
        self.ir_checkbox = QCheckBox("Infrared")
        self.ir_checkbox.stateChanged.connect(self.actualize_lights)
        self.image_settings_second_window.addWidget(self.ir_checkbox)
        self.red_checkbox = QCheckBox("Red")
        self.red_checkbox.stateChanged.connect(self.actualize_lights)
        self.image_settings_second_window.addWidget(self.red_checkbox)
        self.green_checkbox = QCheckBox("Green")
        self.green_checkbox.stateChanged.connect(self.actualize_lights)
        self.image_settings_second_window.addWidget(self.green_checkbox)
        self.fluorescence_checkbox = QCheckBox("Blue")
        self.fluorescence_checkbox.stateChanged.connect(self.actualize_lights)
        self.image_settings_second_window.addWidget(self.fluorescence_checkbox)

        self.light_channel_layout = QHBoxLayout()
        self.preview_light_label = QLabel("Light Channel Preview")
        self.light_channel_layout.addWidget(self.preview_light_label)
        self.preview_light_combo = QComboBox()
        self.preview_light_combo.setEnabled(False)
        self.preview_light_combo.currentIndexChanged.connect(
            self.change_preview_light_channel
        )
        self.light_channel_layout.addWidget(self.preview_light_combo)
        # self.activation_map_checkbox = QCheckBox("Show Activation Map")
        self.activation_map_window = QHBoxLayout()
        self.activation_map_label = QLabel("Activation Map")
        self.activation_map_window.addWidget(self.activation_map_label)
        self.activation_map_combo = QComboBox()
        self.activation_map_combo.addItem("None")
        self.activation_map_combo.addItem("Normal")
        self.activation_map_combo.addItem("Logarithmic")
        self.activation_map_combo.currentIndexChanged.connect(self.adjust_slider)
        self.activation_map_window.addWidget(self.activation_map_combo)

        self.image_settings_main_window.addLayout(self.image_settings_second_window)
        self.image_settings_main_window.addLayout(self.light_channel_layout)
        # self.image_settings_main_window.addWidget(self.activation_map_checkbox)
        self.image_settings_main_window.addLayout(self.activation_map_window)

        self.roi_buttons = QStackedLayout()

        self.roi_layout1 = QHBoxLayout()
        self.roi_layout1.setAlignment(Qt.AlignLeft)
        self.roi_layout1.setAlignment(Qt.AlignTop)
        self.roi_layout1.setContentsMargins(0, 0, 0, 0)
        self.reset_roi_button = QPushButton()
        self.reset_roi_button.setText("Reset ROI")
        self.reset_roi_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "zoom-out-area.png"))
        )
        # self.reset_roi_button.setIcon(QIcon("gui/icons/zoom-out-area.png"))
        self.reset_roi_button.setEnabled(False)
        self.reset_roi_button.clicked.connect(self.reset_roi)
        self.roi_layout1.addWidget(self.reset_roi_button)

        self.set_roi_button = QPushButton()
        self.set_roi_button.setText("Set ROI")
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
        self.roi_layout2.setContentsMargins(0, 0, 0, 0)
        self.cancel_roi_button = QPushButton()
        self.cancel_roi_button.setText("Cancel")
        self.cancel_roi_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "zoom-cancel.png"))
        )
        self.cancel_roi_button.clicked.connect(self.cancel_roi)
        self.roi_layout2.addWidget(self.cancel_roi_button)

        self.save_roi_button = QPushButton()
        self.save_roi_button.setText("Save ROI")
        self.save_roi_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "zoom-check.png"))
        )
        self.save_roi_button.clicked.connect(self.save_roi)
        self.roi_layout2.addWidget(self.save_roi_button)
        self.roi_layout2_container = QWidget()
        self.roi_layout2_container.setLayout(self.roi_layout2)

        if self.acquisition_mode:
            self.roi_buttons.addWidget(self.roi_layout1_container)
            self.roi_buttons.addWidget(self.roi_layout2_container)
            self.image_settings_main_window.addLayout(self.roi_buttons)

        self.exposure_slider = QSlider(Qt.Horizontal, self)
        self.exposure_slider.setRange(0, 4096)
        self.exposure_slider.setValue(4096)
        self.exposure_slider.valueChanged.connect(self.adjust_exposure)
        self.image_settings_main_window.addWidget(self.exposure_slider)
        self.image_settings_main_window.addStretch()

        self.activate_live_preview_button = QPushButton()
        self.activate_live_preview_button.setText("Start Live Preview")
        self.activate_live_preview_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "video.png"))
        )
        self.activate_live_preview_button.clicked.connect(self.open_live_preview_thread)

        self.deactivate_live_preview_button = QPushButton()
        self.deactivate_live_preview_button.setText("Stop Live Preview")
        self.deactivate_live_preview_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "video-off.png"))
        )
        self.deactivate_live_preview_button.clicked.connect(self.stop_live)

        self.image_settings_main_window.addStretch()

        if self.acquisition_mode:
            self.grid_layout.addLayout(self.image_settings_main_window, 1, 1)

        self.live_preview_label = QLabel("Live Preview")
        self.live_preview_label.setFont(QFont("IBM Plex Sans", 17))
        self.image_view = PlotWindow()
        self.plot_image = plt.imshow(
            np.zeros(
                (int(1024 / self.config["Binning"]), int(1024 / self.config["Binning"]))
            ),
            cmap="binary_r",
            vmin=0,
            vmax=4096,
            origin="lower",
        )
        self.plot_image.axes.get_xaxis().set_visible(False)
        self.plot_image.axes.axes.get_yaxis().set_visible(False)

        if self.acquisition_mode:
            self.grid_layout.addWidget(self.live_preview_label, 0, 2)
            self.grid_layout.addWidget(self.image_view, 1, 2)

        self.tree_label = QLabel("Stimulation Tree")
        self.tree_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.tree_label, 2, 0)

        self.tree_window = QVBoxLayout()
        self.tree = Tree()
        self.tree.setHeaderLabels(
            [
                "0 Name",
                "1 Iterations",
                "2 Delay",
                "3 Jitter",
                "4 Type",
                "5 Pulses",
                "6 Duration",
                "7 Jitter",
                "8 Width",
                "9 Frequency",
                "10 Duty",
                "11 Type2",
                "12 Pulses 2",
                "13 Jitter 2",
                "14 Width 2",
                "15 Frequency 2",
                "16 Duty 2",
                "17 Baseline",
                "18 Canal 1",
                "19 Canal 2",
                "20 Valid",
                "21 Heigth",
                "22 Heigth 2",
                "23 Type 3",
                "24 Pulses 3",
                "25 Jitter 3",
                "26 Width 3",
                "27 Frequency 3",
                "28 Duty 3",
                "29 Heigth 3",
                "30 Canal 3",
            ]
        )
        if not self.config["Debug"]:
            for i in range(1, 20):
                self.tree.header().hideSection(i)
            for i in range(21, 31):
                self.tree.header().hideSection(i)
            self.tree.setHeaderHidden(True)
            self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tree.header().setStretchLastSection(False)
        self.tree.currentItemChanged.connect(self.actualize_window)
        self.tree_window.addWidget(self.tree)

        self.tree_switch_window = QStackedLayout()
        self.tree_second_window = QHBoxLayout()
        self.stim_buttons_container = QWidget()
        self.delete_item_button = QPushButton("Delete")
        self.delete_item_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "trash.png"))
        )
        self.delete_item_button.clicked.connect(self.tree.delete_item)
        self.tree_second_window.addWidget(self.delete_item_button)
        self.add_brother_branch_button = QPushButton("Add Sibling")
        self.add_brother_branch_button.clicked.connect(self.tree.add_brother)
        self.add_brother_branch_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "arrow-bar-down.png"))
        )
        self.tree_second_window.addWidget(self.add_brother_branch_button)
        self.add_child_branch_button = QPushButton("Add Child")
        self.add_child_branch_button.clicked.connect(self.tree.add_child)
        self.add_child_branch_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "arrow-bar-right.png"))
        )
        self.tree_second_window.addWidget(self.add_child_branch_button)
        self.stim_buttons_container.setLayout(self.tree_second_window)
        self.tree_switch_window.addWidget(self.stim_buttons_container)

        self.tree_third_window = QHBoxLayout()
        self.import_button = QPushButton("Import Configuration")
        self.import_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "packge-import.png"))
        )
        self.import_button.clicked.connect(self.import_config)
        self.tree_third_window.addWidget(self.import_button)
        self.new_branch_button = QPushButton("New Stimulation")
        self.new_branch_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "square-plus.png"))
        )
        self.tree_third_window.addWidget(self.new_branch_button)
        self.stim_buttons_container2 = QWidget()
        self.stim_buttons_container2.setLayout(self.tree_third_window)
        self.tree_switch_window.addWidget(self.stim_buttons_container2)
        self.new_branch_button.clicked.connect(self.tree.first_stimulation)
        self.grid_layout.addLayout(self.tree_switch_window, 4, 0)

        self.tree_switch_window.setCurrentIndex(1)
        self.grid_layout.addLayout(self.tree_window, 3, 0)

        self.signal_adjust_label = QLabel("Signal Adjust")
        self.signal_adjust_label.setFont(QFont("IBM Plex Sans", 17))
        self.grid_layout.addWidget(self.signal_adjust_label, 2, 1)

        self.signal_adjust_superposed = QStackedLayout()
        self.stimulation_edit_layout = QVBoxLayout()
        self.stimulation_edit_layout.setContentsMargins(0, 0, 0, 0)

        self.canal_window = QVBoxLayout()
        self.canal_window.setAlignment(Qt.AlignLeft)
        self.canal_window.setAlignment(Qt.AlignTop)
        self.canal_window.setContentsMargins(0, 0, 0, 0)

        self.first_canal_check = QCheckBox()
        self.first_canal_check.stateChanged.connect(self.canals_to_tree)
        self.first_canal_check.setText("Canal 1")

        self.stim_type_cell = QComboBox()
        self.stim_type_cell.addItem("square")
        self.stim_type_cell.addItem("random-square")
        self.stim_type_cell.addItem("Third")
        self.stim_type_cell.currentIndexChanged.connect(self.type_to_tree)
        self.stimulation_type_window = QHBoxLayout()
        self.stimulation_type_window.addWidget(self.first_canal_check)
        self.stimulation_type_window.addWidget(self.stim_type_cell)
        self.canal_window.addLayout(self.stimulation_type_window)

        self.different_signals_window = QStackedLayout()
        self.canal_window.addLayout(self.different_signals_window)

        self.second_canal_check = QCheckBox()
        self.second_canal_check.stateChanged.connect(self.canals_to_tree)
        self.second_canal_check.setText("Canal 2")

        self.stim_type_cell2 = QComboBox()
        self.stim_type_cell2.addItem("square")
        self.stim_type_cell2.addItem("random-square")
        self.stim_type_cell2.addItem("Third")
        self.stim_type_cell2.currentIndexChanged.connect(self.type_to_tree)
        self.stimulation_type_window2 = QHBoxLayout()
        self.stimulation_type_window2.addWidget(self.second_canal_check)
        self.stimulation_type_window2.addWidget(self.stim_type_cell2)
        self.canal_window.addLayout(self.stimulation_type_window2)

        self.different_signals_window2 = QStackedLayout()
        self.canal_window.addLayout(self.different_signals_window2)

        self.third_canal_check = QCheckBox()
        self.third_canal_check.stateChanged.connect(self.canals_to_tree)
        self.third_canal_check.setText("Canal 3")
        # self.canal_window.addWidget(self.third_canal_check)

        self.stim_type_cell3 = QComboBox()
        self.stim_type_cell3.addItem("square")
        self.stim_type_cell3.addItem("random-square")
        self.stim_type_cell3.addItem("Third")
        self.stim_type_cell3.currentIndexChanged.connect(self.type_to_tree)
        self.stimulation_type_window3 = QHBoxLayout()
        self.stimulation_type_window3.addWidget(self.third_canal_check)
        # self.stimulation_type_window3.addWidget(self.stim_type_cell3)
        self.canal_window.addLayout(self.stimulation_type_window3)

        self.different_signals_window3 = QStackedLayout()
        self.canal_window.addLayout(self.different_signals_window3)

        self.stimulation_name_label = QLabel("Stimulation Name")
        self.stimulation_name_cell = QLineEdit()
        self.stimulation_name_cell.textEdited.connect(self.name_to_tree)
        self.stimulation_name_window = QHBoxLayout()
        self.stimulation_name_window.addWidget(self.stimulation_name_label)
        self.stimulation_name_window.addWidget(self.stimulation_name_cell)
        self.stimulation_edit_layout.addLayout(self.stimulation_name_window)

        self.duration_window = QHBoxLayout()
        self.first_signal_type_duration_label = QLabel("Duration (s)")
        self.duration_window.addWidget(self.first_signal_type_duration_label)
        self.duration_cell = QLineEdit()
        self.duration_window.addWidget(self.duration_cell)
        self.duration_cell.setValidator(self.onlyFloat)
        self.duration_cell.textEdited.connect(self.signal_to_tree)
        self.stimulation_edit_layout.addLayout(self.duration_window)

        self.baseline_checkbox = QCheckBox("Baseline")
        self.baseline_checkbox.stateChanged.connect(self.canals_to_tree)
        if self.acquisition_mode:
            self.stimulation_edit_layout.addWidget(self.baseline_checkbox)
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

        self.first_signal_type_window3 = QVBoxLayout()
        self.first_signal_type_window3.setAlignment(Qt.AlignLeft)
        self.first_signal_type_window3.setAlignment(Qt.AlignTop)
        self.first_signal_type_window3.setContentsMargins(0, 0, 0, 0)
        self.first_signal_type_container3 = QWidget()
        self.first_signal_type_container3.setLayout(self.first_signal_type_window3)

        self.pulses_window = QHBoxLayout()
        self.pulses_label = QLabel("Pulses")
        self.pulses_window.addWidget(self.pulses_label)
        self.pulses_cell = QLineEdit()
        self.pulses_cell.setValidator(QIntValidator())
        self.pulses_cell.textEdited.connect(self.signal_to_tree)
        self.pulses_window.addWidget(self.pulses_cell)

        self.pulses_window2 = QHBoxLayout()
        self.pulses_label2 = QLabel("Pulses")
        self.pulses_window2.addWidget(self.pulses_label2)
        self.pulses_cell2 = QLineEdit()
        self.pulses_cell2.setValidator(QIntValidator())
        self.pulses_cell2.textEdited.connect(self.signal_to_tree)
        self.pulses_window2.addWidget(self.pulses_cell2)

        self.pulses_window3 = QHBoxLayout()
        self.pulses_label3 = QLabel("Pulses")
        self.pulses_window3.addWidget(self.pulses_label3)
        self.pulses_cell3 = QLineEdit()
        self.pulses_cell3.setValidator(QIntValidator())
        self.pulses_cell3.textEdited.connect(self.signal_to_tree)
        self.pulses_window3.addWidget(self.pulses_cell3)

        self.jitter_window = QHBoxLayout()
        self.jitter_label = QLabel("Jitter (s)")
        self.jitter_window.addWidget(self.jitter_label)
        self.jitter_cell = QLineEdit()
        self.jitter_cell.setValidator(self.onlyFloat)
        self.jitter_cell.setText("0")
        self.jitter_cell.textEdited.connect(self.signal_to_tree)
        self.jitter_window.addWidget(self.jitter_cell)

        self.jitter_window2 = QHBoxLayout()
        self.jitter_window2 = QHBoxLayout()
        self.jitter_label2 = QLabel("Jitter (s)")
        self.jitter_window2.addWidget(self.jitter_label2)
        self.jitter_cell2 = QLineEdit()
        self.jitter_cell2.setValidator(self.onlyFloat)
        self.jitter_cell2.setText("0")
        self.jitter_cell2.textEdited.connect(self.signal_to_tree)
        self.jitter_window2.addWidget(self.jitter_cell2)

        self.jitter_window3 = QHBoxLayout()
        self.jitter_window3 = QHBoxLayout()
        self.jitter_label3 = QLabel("Jitter (s)")
        self.jitter_window3.addWidget(self.jitter_label3)
        self.jitter_cell3 = QLineEdit()
        self.jitter_cell3.setValidator(self.onlyFloat)
        self.jitter_cell3.setText("0")
        self.jitter_cell3.textEdited.connect(self.signal_to_tree)
        self.jitter_window3.addWidget(self.jitter_cell3)

        self.width_window = QHBoxLayout()
        self.width_label = QLabel("Width (s)")
        self.width_window.addWidget(self.width_label)
        self.width_cell = QLineEdit()
        self.width_cell.setValidator(self.onlyFloat)
        self.width_cell.setText("0")
        self.width_cell.textEdited.connect(self.signal_to_tree)
        self.width_window.addWidget(self.width_cell)

        self.width_window2 = QHBoxLayout()
        self.width_label2 = QLabel("Width (s)")
        self.width_window2.addWidget(self.width_label2)
        self.width_cell2 = QLineEdit()
        self.width_cell2.setValidator(self.onlyFloat)
        self.width_cell2.setText("0")
        self.width_cell2.textEdited.connect(self.signal_to_tree)
        self.width_window2.addWidget(self.width_cell2)

        self.width_window3 = QHBoxLayout()
        self.width_label3 = QLabel("Width (s)")
        self.width_window3.addWidget(self.width_label3)
        self.width_cell3 = QLineEdit()
        self.width_cell3.setValidator(self.onlyFloat)
        self.width_cell3.setText("0")
        self.width_cell3.textEdited.connect(self.signal_to_tree)
        self.width_window3.addWidget(self.width_cell3)

        self.first_signal_type_window.addLayout(self.pulses_window)
        self.first_signal_type_window.addLayout(self.width_window)
        self.first_signal_type_window.addLayout(self.jitter_window)

        self.first_signal_type_window2.addLayout(self.pulses_window2)
        self.first_signal_type_window2.addLayout(self.width_window2)
        self.first_signal_type_window2.addLayout(self.jitter_window2)

        self.first_signal_type_window3.addLayout(self.pulses_window3)
        self.first_signal_type_window3.addLayout(self.width_window3)
        self.first_signal_type_window3.addLayout(self.jitter_window3)
        # -------------------

        self.second_signal_type_window = QVBoxLayout()
        self.second_signal_type_container = QWidget()
        self.second_signal_type_window.setAlignment(Qt.AlignLeft)
        self.second_signal_type_window.setAlignment(Qt.AlignTop)
        self.second_signal_type_window.setContentsMargins(0, 0, 0, 0)
        self.second_signal_type_container.setLayout(self.second_signal_type_window)
        # self.stimulation_edit_layout.addLayout(self.different_signals_window)

        self.second_signal_type_window2 = QVBoxLayout()
        self.second_signal_type_container2 = QWidget()
        self.second_signal_type_window2.setAlignment(Qt.AlignLeft)
        self.second_signal_type_window2.setAlignment(Qt.AlignTop)
        self.second_signal_type_window2.setContentsMargins(0, 0, 0, 0)
        self.second_signal_type_container2.setLayout(self.second_signal_type_window2)

        self.second_signal_type_window3 = QVBoxLayout()
        self.second_signal_type_container3 = QWidget()
        self.second_signal_type_window3.setAlignment(Qt.AlignLeft)
        self.second_signal_type_window3.setAlignment(Qt.AlignTop)
        self.second_signal_type_window3.setContentsMargins(0, 0, 0, 0)
        self.second_signal_type_container3.setLayout(self.second_signal_type_window3)

        self.heigth_window = QHBoxLayout()
        self.heigth_label = QLabel("Heigth (V)")
        self.heigth_window.addWidget(self.heigth_label)
        self.heigth_cell = QLineEdit()
        self.heigth_cell.setValidator(self.onlyFloat)
        self.heigth_cell.textEdited.connect(self.signal_to_tree)
        self.heigth_window.addWidget(self.heigth_cell)

        self.heigth_window2 = QHBoxLayout()
        self.heigth_label2 = QLabel("Heigth (V)")
        self.heigth_window2.addWidget(self.heigth_label2)
        self.heigth_cell2 = QLineEdit()
        self.heigth_cell2.setValidator(self.onlyFloat)
        self.heigth_cell2.textEdited.connect(self.signal_to_tree)
        self.heigth_window2.addWidget(self.heigth_cell2)

        self.heigth_window3 = QHBoxLayout()
        self.heigth_label3 = QLabel("Heigth (V)")
        self.heigth_window3.addWidget(self.heigth_label3)
        self.heigth_cell3 = QLineEdit()
        self.heigth_cell3.setValidator(self.onlyFloat)
        self.heigth_cell3.textEdited.connect(self.signal_to_tree)
        self.heigth_window3.addWidget(self.heigth_cell3)

        self.frequency_window = QHBoxLayout()
        self.frequency_label = QLabel("Frequency (Hz)")
        self.frequency_window.addWidget(self.frequency_label)
        self.frequency_cell = QLineEdit()
        self.frequency_cell.setValidator(self.onlyFloat)
        self.frequency_cell.textEdited.connect(self.signal_to_tree)
        self.frequency_window.addWidget(self.frequency_cell)

        self.frequency_window2 = QHBoxLayout()
        self.frequency_label2 = QLabel("Frequency (Hz)")
        self.frequency_window2.addWidget(self.frequency_label2)
        self.frequency_cell2 = QLineEdit()
        self.frequency_cell2.setValidator(self.onlyFloat)
        self.frequency_cell2.textEdited.connect(self.signal_to_tree)
        self.frequency_window2.addWidget(self.frequency_cell2)

        self.frequency_window3 = QHBoxLayout()
        self.frequency_label3 = QLabel("Frequency (Hz)")
        self.frequency_window3.addWidget(self.frequency_label3)
        self.frequency_cell3 = QLineEdit()
        self.frequency_cell3.setValidator(self.onlyFloat)
        self.frequency_cell3.textEdited.connect(self.signal_to_tree)
        self.frequency_window3.addWidget(self.frequency_cell3)

        self.duty_window = QHBoxLayout()
        self.duty_label = QLabel("Duty (%)")
        self.duty_window.addWidget(self.duty_label)
        self.duty_cell = QLineEdit()
        self.duty_cell.setValidator(self.onlyFloat)
        self.duty_cell.textEdited.connect(self.signal_to_tree)
        self.duty_window.addWidget(self.duty_cell)

        self.duty_window2 = QHBoxLayout()
        self.duty_label2 = QLabel("Duty (%)")
        self.duty_window2.addWidget(self.duty_label2)
        self.duty_cell2 = QLineEdit()
        self.duty_cell2.setValidator(self.onlyFloat)
        self.duty_cell2.textEdited.connect(self.signal_to_tree)
        self.duty_window2.addWidget(self.duty_cell2)

        self.duty_window3 = QHBoxLayout()
        self.duty_label3 = QLabel("Duty (%)")
        self.duty_window3.addWidget(self.duty_label3)
        self.duty_cell3 = QLineEdit()
        self.duty_cell3.setValidator(self.onlyFloat)
        self.duty_cell3.textEdited.connect(self.signal_to_tree)
        self.duty_window3.addWidget(self.duty_cell3)

        self.second_signal_type_window.addLayout(self.heigth_window)
        self.second_signal_type_window.addLayout(self.frequency_window)
        self.second_signal_type_window.addLayout(self.duty_window)

        self.second_signal_type_window2.addLayout(self.heigth_window2)
        self.second_signal_type_window2.addLayout(self.frequency_window2)
        self.second_signal_type_window2.addLayout(self.duty_window2)

        # self.second_signal_type_window3.addLayout(self.heigth_window3)
        self.second_signal_type_window3.addLayout(self.frequency_window3)
        self.second_signal_type_window3.addLayout(self.duty_window3)

        # -------------------

        self.third_signal_type_window = QVBoxLayout()
        self.third_signal_type_container = QWidget()
        self.third_signal_type_container.setLayout(self.third_signal_type_window)

        self.third_signal_type_window2 = QVBoxLayout()
        self.third_signal_type_container2 = QWidget()
        self.third_signal_type_container2.setLayout(self.third_signal_type_window2)

        self.third_signal_type_window3 = QVBoxLayout()
        self.third_signal_type_container3 = QWidget()
        self.third_signal_type_container3.setLayout(self.third_signal_type_window3)

        self.third_signal_type_name = QLabel("signal3")
        self.third_signal_type_window.addWidget(self.third_signal_type_name)

        self.third_signal_type_name2 = QLabel("signal3")
        self.third_signal_type_window2.addWidget(self.third_signal_type_name2)

        self.third_signal_type_name3 = QLabel("signal3")
        self.third_signal_type_window3.addWidget(self.third_signal_type_name3)

        self.different_signals_window.addWidget(self.second_signal_type_container)
        self.different_signals_window.addWidget(self.first_signal_type_container)
        self.different_signals_window.addWidget(self.third_signal_type_container)

        self.different_signals_window2.addWidget(self.second_signal_type_container2)
        self.different_signals_window2.addWidget(self.first_signal_type_container2)
        self.different_signals_window2.addWidget(self.third_signal_type_container2)

        self.different_signals_window3.addWidget(self.second_signal_type_container3)
        self.different_signals_window3.addWidget(self.first_signal_type_container3)
        self.different_signals_window3.addWidget(self.third_signal_type_container3)

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
        self.block_iterations_cell.setValidator(QIntValidator())
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

        self.signal_preview_label = QLabel("Signal Preview")
        self.signal_preview_label.setFont(QFont("IBM Plex Sans", 17))
        if self.acquisition_mode:
            self.grid_layout.addWidget(self.signal_preview_label, 2, 2)
        else:
            self.grid_layout.addWidget(self.signal_preview_label, 0, 2)

        self.buttons_main_window = QHBoxLayout()
        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "player-stop.png"))
        )
        self.stop_button.clicked.connect(self.stop_while_running)
        self.stop_button.setEnabled(False)
        self.buttons_main_window.addWidget(self.stop_button)
        self.run_button = QPushButton("Run")
        self.run_button.setIcon(
            QIcon(os.path.join(self.cwd, "gui", "icons", "player-play.png"))
        )
        self.run_button.clicked.connect(self.run)
        self.run_button.setEnabled(False)
        self.buttons_main_window.addWidget(self.run_button)
        self.plot_window = PlotWindow(subplots=True)
        if self.acquisition_mode:
            self.grid_layout.addWidget(self.plot_window, 3, 2)
        else:
            self.grid_layout.addWidget(self.plot_window, 1, 2, 3, 1)
        self.grid_layout.addLayout(self.buttons_main_window, 4, 2)
        self.open_daq_generation_thread()
        self.initialize_buttons()
        self.show()

    def deactivate_channels(self):
        """Deactivate canal checkboxes if the baseline checkbox is checked"""
        if self.baseline_checkbox.isChecked():
            self.deactivate_buttons(
                [
                    self.first_canal_check,
                    self.second_canal_check,
                ]
            )
        else:
            self.activate_buttons(
                [
                    self.first_canal_check,
                    self.second_canal_check,
                ]
            )

    def adjust_exposure(self):
        """Match the exposure of the image preview to the slider value"""
        try:
            self.max_exposure = self.exposure_slider.value()
            self.slider_values[self.preview_light_combo.currentText()][
            self.activation_map_combo.currentText()
            ] = self.max_exposure
        except Exception:
            pass

    def set_trigger(self):
        """Set the trigger for the DAQ"""
        if not self.acquisition_mode:
            self.run_button.setText("Run at Trigger")
            self.daq.set_trigger(self.ports["trigger"])
        else:
            self.run_button.setText("Run")
            self.daq.remove_trigger()

    def import_config(self):
        """Import a configuration file"""
        file = QFileDialog.getOpenFileName()[0]
        try:
            dictionary = get_dictionary(file)
            self.framerate_cell.setText(str(dictionary["Framerate"]))
            self.exposure_cell.setText(str(dictionary["Exposition"]))
            self.set_lights(dictionary["Lights"])
            self.tree.create_tree_item(dictionary["Blocks"])
            self.enable_run(self.tree.check_global_validity())
            self.tree.graph(self.tree.invisibleRootItem())
            self.draw()
        except Exception as err:
            print(err)

    def set_lights(self, lights):
        """Set the lights"""
        for light in lights:
            if light == "infrared":
                self.ir_checkbox.setChecked(True)
            elif light == "red":
                self.red_checkbox.setChecked(True)
            elif light == "green":
                self.green_checkbox.setChecked(True)
            elif light == "blue":
                self.fluorescence_checkbox.setChecked(True)

    def run(self):
        """Run the experiment"""
        if self.check_override():
            self.deactivate_buttons(buttons=self.enabled_buttons)
            self.master_block = self.tree.create_blocks()
            self.tree.baseline_values = []
            self.tree.graph(item=self.tree.invisibleRootItem())
            self.root_time, self.root_signal = (
                self.tree.x_values,
                [
                    self.tree.stim1_values,
                    self.tree.stim2_values,
                    self.tree.stim3_values,
                ],
            )
            self.draw(root=True)
            if self.acquisition_mode:
                self.actualize_daq()
                self.open_live_saving_thread()
                self.open_live_preview_thread()
                self.open_baseline_check_thread()
            else:
                self.daq.stop_signal = False
            self.open_signal_preview_thread()
            self.open_start_experiment_thread()

    def check_override(self):
        """Check if experiment with the same name already exists"""
        if os.path.isfile(
            os.path.join(
                self.directory_cell.text(),
                self.experiment_name_cell.text(),
                f"{self.experiment_name_cell.text()}-light_signal.npy",
            )
        ) and self.directory_save_files_checkbox.isChecked():
            button = QMessageBox.question(
                self,
                "Files already exist",
                "Files already exist. \n Do you want to override the existing files?",
            )
            if button == QMessageBox.Yes:
                return True
            else:
                return False
        else:
            return True

    def open_baseline_check_thread(self):
        """Open the thread for the baseline check"""
        self.baseline_check_thread = Thread(target=self.check_baseline)
        self.baseline_check_thread.start()

    def check_baseline(self):
        """Monitor the incoming frames and check if the baseline is reached"""
        if len(self.daq.lights) > 0:
            self.camera.baseline_data = []
            self.camera.adding_frames = False
            self.camera.completed_baseline = False
            while self.daq.camera_signal is None:
                pass
            frames_acquired = frames_acquired_from_camera_signal(self.daq.camera_signal)
            baseline_indices = get_baseline_frame_indices(
                self.tree.baseline_values, frames_acquired
            )
            for baseline_pair in baseline_indices:
                while not self.daq.stop_signal:
                    try:
                        if (
                            not self.camera.adding_frames
                            and self.camera.frames_read >= baseline_pair[0]
                        ):
                            self.camera.adding_frames = True
                        elif (
                            self.camera.adding_frames
                            and self.camera.frames_read >= baseline_pair[1]
                        ):
                            self.camera.baseline_read_list = []
                            self.camera.average_baseline = average_baseline(
                                self.camera.baseline_data,
                                len(self.daq.lights),
                                self.camera.frames_read_list[0] % len(self.daq.lights),
                            )
                            self.camera.adding_frames = False
                            self.camera.baseline_frames = []
                            self.camera.baseline_completed = True
                            self.camera.frames_read_list = []
                            self.camera.baseline_data = []
                            break
                    except Exception as err:
                        pass
                    time.sleep(0.01)

    def open_start_experiment_thread(self):
        """Open the thread for the start of the experiment"""
        self.start_experiment_thread = Thread(target=self.run_stimulation)
        self.start_experiment_thread.start()

    def save_config(self):
        """Save the current configuration to a JSON file"""
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder != "":
            self.master_block = self.tree.create_blocks()
            self.experiment = Experiment(
                self.master_block,
                int(self.framerate_cell.text()),
                int(self.exposure_cell.text()),
                self.mouse_id_cell.text(),
                folder,
                self.daq,
                name=self.experiment_name_cell.text(),
                config=self.config,
            )
            self.experiment.save_config(
                [int(1024 / self.config["Binning"]), int(1024 / self.config["Binning"])]
            )

    def run_stimulation(self):
        """Run the stimulation in parallel with the lights"""
        self.experiment = Experiment(
            self.master_block,
            int(self.framerate_cell.text()),
            int(self.exposure_cell.text()),
            self.mouse_id_cell.text(),
            self.directory_cell.text(),
            self.daq,
            name=self.experiment_name_cell.text(),
            config=self.config,
        )
        self.save_files_after_stop = True
        self.daq.launch(self.experiment.name, self.root_time, self.root_signal)
        # if (
        #    not self.daq.stop_signal
        #    and self.save_files_after_stop
        #    and self.directory_save_files_checkbox.isChecked()
        # ):
        if (
            self.save_files_after_stop
            and self.directory_save_files_checkbox.isChecked()
        ):
            try:
                self.experiment.save(self.roi_extent)
            except Exception as err:
                self.experiment.save()
        self.stop()

    def open_live_saving_thread(self):
        """Open the thread for the live saving"""
        self.live_save_thread = Thread(target=self.live_save)
        self.live_save_thread.start()

    def live_save(self):
        """Save NPY chunked files when the number of frames is over 1200"""
        self.camera.file_index = 0
        self.camera.is_saving = False
        if self.directory_save_files_checkbox.isChecked():
            try:
                os.mkdir(
                    os.path.join(
                        self.directory_cell.text(), self.experiment_name_cell.text()
                    )
                )
                os.mkdir(
                    os.path.join(
                        self.directory_cell.text(),
                        self.experiment_name_cell.text(),
                        "data",
                    )
                )
            except Exception as err:
                pass
            while self.camera.video_running is False and not self.camera.stop_signal:
                time.sleep(0.01)
                pass
            while self.camera.video_running is True:
                if len(self.camera.frames) > 1200:
                    self.memory = self.camera.frames[:1200]
                    self.camera.frames = self.camera.frames[1200:]
                    if self.directory_save_files_checkbox.isChecked():
                        try:
                            self.memory = shrink_array(self.memory, self.roi_extent)
                        except Exception:
                            pass
                        self.camera.is_saving = True
                        np.save(
                            os.path.join(
                                self.directory_cell.text(),
                                self.experiment_name_cell.text(),
                                "data",
                                f"{self.camera.file_index}.npy",
                            ),
                            self.memory,
                        )
                        self.memory = None
                        self.camera.file_index += 1
                        self.camera.is_saving = False
                time.sleep(0.01)

    def open_live_preview_thread(self):
        """Open the thread for the live preview"""
        self.live_preview_thread = Thread(target=self.start_live)
        self.live_preview_thread.start()

    def start_live(self):
        """Start the live preview"""
        plt.ion()
        self.memory = []
        self.camera.baseline_completed = False
        if len(self.daq.lights) > 0:
            try:
                while self.camera.video_running is False:
                    time.sleep(0.01)
                    pass
                while self.camera.video_running is True:
                    try:
                        if (
                            not self.camera.baseline_completed
                            or self.activation_map_combo.currentIndex() == 0
                        ):
                            self.plot_image.set(
                                array=self.camera.frames[
                                    self.live_preview_light_index :: len(
                                        self.daq.lights
                                    )
                                ][-1],
                                clim=(0, self.max_exposure),
                                cmap="binary_r",
                            )
                        elif self.activation_map_combo.currentIndex() == 1:
                            start_index = (
                                self.camera.baseline_read_list[0]
                                + self.live_preview_light_index
                            ) % len(self.daq.lights)
                            activation_map = (
                                self.camera.baseline_frames[
                                    start_index :: len(self.daq.lights)
                                ][-1]
                                - self.camera.average_baseline[
                                    self.live_preview_light_index
                                ]
                            ) / self.camera.average_baseline[
                                self.live_preview_light_index
                            ]
                            self.plot_image.set(
                                array=activation_map,
                                clim=(
                                    -self.max_exposure / 200,
                                    self.max_exposure / 200,
                                ),
                                cmap="seismic",
                            )
                        else:
                            start_index = (
                                self.camera.baseline_read_list[0]
                                + self.live_preview_light_index
                            ) % len(self.daq.lights)
                            activation_map = np.log(
                                (
                                    (
                                        self.camera.baseline_frames[
                                            start_index :: len(self.daq.lights)
                                        ][-1]
                                    )
                                    / self.camera.average_baseline[
                                        self.live_preview_light_index
                                    ]
                                )
                            )
                            self.plot_image.set(
                                array=activation_map,
                                clim=(
                                    -self.max_exposure / 2000,
                                    self.max_exposure / 2000,
                                ),
                                cmap="seismic",
                            )

                    except Exception as err:
                        print("Live Preview error")
                        print(err)
                        pass
                    time.sleep(0.04)
            except Exception as err:
                pass

    def stop_live(self):
        """Stop the live preview"""
        self.camera.video_running = False

    def open_signal_preview_thread(self):
        """Open the thread for the signal preview"""
        self.signal_preview_thread = Thread(target=self.actualize_progression)
        self.signal_preview_thread.start()

    def actualize_progression(self):
        """Actualize the position of the progress bar"""
        plt.ion()
        start = time.time()
        if not self.config["Widefield Computer"]:
            self.daq.start_time = time.time()
        while self.daq.stop_signal is False:
            try:
                position = time.time() - self.daq.start_time
                self.plot_window.actualize(position)
                time.sleep(1)
            except Exception as err:
                print(err)
                time.sleep(1)
                pass

    def change_preview_light_channel(self):
        """Change the light channel for the live preview"""
        self.live_preview_light_index = self.preview_light_combo.currentIndex()
        self.adjust_slider()

    def adjust_slider(self):
        """Adjust the saturation slider using corresponding value in dictionary"""
        try:
            value = self.slider_values[self.preview_light_combo.currentText()][
                self.activation_map_combo.currentText()
            ]
            self.exposure_slider.setValue(value)
        except Exception:
            pass

    def open_daq_generation_thread(self):
        """Open the thread for the DAQ generation"""
        self.daq_generation_thread = Thread(target=self.generate_daq)
        self.daq_generation_thread.start()

    def generate_daq(self):
        """Generate the DAQ"""
        try:
            self.camera = Camera(self.ports["camera"], "name")
        except Exception:
            self.camera = None
        self.stimuli = [
            Instrument(self.ports["analog0"], "air-pump"),
            Instrument(self.ports["analog1"], "air-pump2"),
            Instrument(self.ports["co2"], "air-pump3"),
        ]
        self.daq = DAQ(
            "dev1",
            [],
            self.stimuli,
            self.camera,
            int(self.framerate_cell.text()),
            int(self.exposure_cell.text()) / 1000,
        )
        self.daq.close_all_lights(self.ports)
        self.daq_generated = True
        self.enable_run(self.tree.check_global_validity())

    def actualize_daq(self):
        """Actualize the DAQ with the current settings"""
        try:
            self.daq.lights = []
            if self.ir_checkbox.isChecked():
                self.daq.lights.append(Instrument(self.ports["infrared"], "ir"))
            if self.red_checkbox.isChecked():
                self.daq.lights.append(Instrument(self.ports["red"], "red"))
            if self.green_checkbox.isChecked():
                self.daq.lights.append(Instrument(self.ports["green"], "green"))
            if self.fluorescence_checkbox.isChecked():
                self.daq.lights.append(Instrument(self.ports["blue"], "blue"))
            self.daq.framerate = int(self.framerate_cell.text())
            self.daq.exposure = int(self.exposure_cell.text()) / 1000
            self.camera.frames = []
            self.daq.stop_signal = False
        except Exception:
            pass

    def stop(self):
        """Stop the experiment and reactivate the interface"""

        print("Things have stopped")
        self.stop_live()
        self.activate_buttons(buttons=self.enabled_buttons)
        self.tree.setCurrentItem(self.tree.topLevelItem(0))
        try:
            self.daq.stop_signal = True
        except Exception:
            pass

    def stop_while_running(self):
        """Stop the experiment while it is running"""
        if self.directory_save_files_checkbox.isChecked():
            self.stop_stimulation_dialog()
        self.stop()

    def stop_stimulation_dialog(self):
        """Ask if user wants to keep the files after experiment is stopped"""
        button = QMessageBox.question(
            self, "Save Files", "Do you want to save the current files?"
        )
        if button == QMessageBox.Yes:
            self.save_files_after_stop = True
        else:
            self.save_files_after_stop = False

    def show_buttons(self, buttons):
        """Show the buttons in a list"""
        for button in buttons:
            button.setVisible(True)

    def hide_buttons(self, buttons):
        """Hide the buttons in a list"""
        for button in buttons:
            button.setVisible(False)

    def activate_buttons(self, buttons):
        """Activate the buttons in a list"""
        for button in buttons:
            button.setEnabled(True)
        if buttons == self.enabled_buttons:
            if self.directory_save_files_checkbox.isChecked():
                self.directory_choose_button.setEnabled(True)
            if self.roi_extent is None:
                self.reset_roi_button.setEnabled(False)
            else:
                self.set_roi_button.setEnabled(False)
            self.stop_button.setDisabled(True)

    def deactivate_buttons(self, buttons):
        """Deactivate the buttons in a list"""
        if buttons == self.enabled_buttons:
            self.stop_button.setEnabled(True)
            self.tree.clearSelection()
        for button in buttons:
            button.setDisabled(True)

    def choose_directory(self):
        """Choose the directory where to save the files"""
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory_cell.setText(folder)

    def enable_directory(self):
        """Enable the directory cell"""
        self.files_saved = self.directory_save_files_checkbox.isChecked()
        self.directory_choose_button.setEnabled(self.files_saved)
        self.directory_cell.setEnabled(self.files_saved)

    def actualize_window(self):
        """Actualize the 'Stimulation Edit' and 'Signal Preview' windows"""
        self.activate_buttons(
            [self.add_child_branch_button, self.add_brother_branch_button]
        )
        if self.tree.currentItem():
            self.tree_switch_window.setCurrentIndex(0)
        else:
            self.tree_switch_window.setCurrentIndex(1)
        try:
            if self.tree.currentItem().childCount() > 0:
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
        self.tree.graph(self.tree.currentItem(), current=True)
        self.draw()

    def name_to_tree(self):
        """Transfer the name of the current item from the cell to the tree"""
        branch = self.tree.currentItem()
        branch.setForeground(0, QBrush(QColor(0, 0, 0)))
        if branch.childCount() > 0:
            branch.setText(0, self.block_name_cell.text())
        else:
            branch.setText(0, self.stimulation_name_cell.text())

    def tree_to_name(self):
        """Transfer the name of the current item from the tree to the cell"""
        try:
            if self.tree.currentItem().childCount() > 0:
                if self.tree.currentItem().text(0) != "No Name":
                    self.block_name_cell.setText(self.tree.currentItem().text(0))
                else:
                    self.block_name_cell.setText("")
            else:
                if self.tree.currentItem().text(0) != "No Name":
                    self.stimulation_name_cell.setText(self.tree.currentItem().text(0))
                else:
                    self.stimulation_name_cell.setText("")
        except AttributeError:
            pass

    def type_to_tree(self):
        """Transfer the type of the current item from the cell to the tree"""
        self.enable_run(self.tree.check_global_validity())
        self.different_signals_window.setCurrentIndex(
            self.stim_type_cell.currentIndex()
        )
        self.different_signals_window2.setCurrentIndex(
            self.stim_type_cell2.currentIndex()
        )
        self.different_signals_window3.setCurrentIndex(
            self.stim_type_cell3.currentIndex()
        )
        try:
            self.tree.currentItem().setText(4, str(self.stim_type_cell.currentText()))
        except Exception:
            pass
        try:
            self.tree.currentItem().setText(11, str(self.stim_type_cell2.currentText()))
        except Exception:
            pass
        try:
            self.tree.currentItem().setText(23, str(self.stim_type_cell3.currentText()))
        except Exception:
            pass
        try:
            self.tree.graph(self.tree.currentItem(), current=True)
            self.draw()
        except Exception:
            pass

    def tree_to_type(self):
        """Transfer the type of the current item from the tree to the cell"""
        dico = {"square": 0, "random-square": 1, "Third": 2}
        try:
            self.stim_type_cell.setCurrentIndex(dico[self.tree.currentItem().text(4)])
        except Exception:
            self.stim_type_cell.setCurrentIndex(0)

        try:
            self.stim_type_cell2.setCurrentIndex(dico[self.tree.currentItem().text(11)])
        except Exception:
            self.stim_type_cell2.setCurrentIndex(0)

        try:
            self.stim_type_cell3.setCurrentIndex(dico[self.tree.currentItem().text(23)])
        except Exception:
            self.stim_type_cell3.setCurrentIndex(0)

    def signal_to_tree(self):
        """Transfer the signal of the current item from the cell to the tree"""
        self.tree.currentItem().setText(6, self.duration_cell.text())
        self.tree.currentItem().setText(5, self.pulses_cell.text())
        self.tree.currentItem().setText(7, self.jitter_cell.text())
        self.tree.currentItem().setText(8, self.width_cell.text())
        self.tree.currentItem().setText(9, self.frequency_cell.text())
        self.tree.currentItem().setText(10, self.duty_cell.text())
        self.tree.currentItem().setText(21, self.heigth_cell.text())
        self.tree.currentItem().setText(12, self.pulses_cell2.text())
        self.tree.currentItem().setText(13, self.jitter_cell2.text())
        self.tree.currentItem().setText(14, self.width_cell2.text())
        self.tree.currentItem().setText(15, self.frequency_cell2.text())
        self.tree.currentItem().setText(16, self.duty_cell2.text())
        self.tree.currentItem().setText(22, self.heigth_cell2.text())
        self.tree.currentItem().setText(24, self.pulses_cell3.text())
        self.tree.currentItem().setText(25, self.jitter_cell3.text())
        self.tree.currentItem().setText(26, self.width_cell3.text())
        self.tree.currentItem().setText(27, self.frequency_cell3.text())
        self.tree.currentItem().setText(28, self.duty_cell3.text())
        self.enable_run(self.tree.check_global_validity())
        self.tree.graph(self.tree.currentItem(), current=True)
        self.draw()

    def tree_to_signal(self):
        """Transfer the signal of the current item from the tree to the cell"""
        try:
            self.pulses_cell.setText(self.tree.currentItem().text(5))
            self.duration_cell.setText(self.tree.currentItem().text(6))
            self.jitter_cell.setText(self.tree.currentItem().text(7))
            self.width_cell.setText(self.tree.currentItem().text(8))
            self.frequency_cell.setText(self.tree.currentItem().text(9))
            self.heigth_cell.setText(self.tree.currentItem().text(21))
            self.duty_cell.setText(self.tree.currentItem().text(10))
            self.pulses_cell2.setText(self.tree.currentItem().text(12))
            self.jitter_cell2.setText(self.tree.currentItem().text(13))
            self.width_cell2.setText(self.tree.currentItem().text(14))
            self.frequency_cell2.setText(self.tree.currentItem().text(15))
            self.heigth_cell2.setText(self.tree.currentItem().text(22))
            self.duty_cell2.setText(self.tree.currentItem().text(16))
            self.pulses_cell3.setText(self.tree.currentItem().text(24))
            self.jitter_cell3.setText(self.tree.currentItem().text(25))
            self.width_cell3.setText(self.tree.currentItem().text(26))
            self.frequency_cell3.setText(self.tree.currentItem().text(27))
            self.duty_cell3.setText(self.tree.currentItem().text(28))
        except Exception as err:
            pass

    def tree_to_block(self):
        """Transfer the block attributes from the tree to the cells"""
        try:
            self.block_iterations_cell.setText(self.tree.currentItem().text(1))
            self.block_delay_cell.setText(self.tree.currentItem().text(2))
            self.block_jitter_cell.setText(self.tree.currentItem().text(3))
        except Exception:
            pass

    def block_to_tree(self):
        """Transfer the block attributes from the cells to the tree"""
        self.tree.currentItem().setText(1, self.block_iterations_cell.text())
        self.tree.currentItem().setText(2, self.block_delay_cell.text())
        self.tree.currentItem().setText(3, self.block_jitter_cell.text())
        self.enable_run(self.tree.check_global_validity())
        self.tree.graph(self.tree.currentItem(), current=True)
        self.draw()

    def tree_to_canal(self):
        """Transfer the canals attributes from the tree to the cells"""
        self.canal_running = True
        try:
            self.baseline_checkbox.setChecked(
                self.boolean(self.tree.currentItem().text(17))
            )
            self.first_canal_check.setChecked(
                self.boolean(self.tree.currentItem().text(18))
            )
            self.second_canal_check.setChecked(
                self.boolean(self.tree.currentItem().text(19))
            )
            self.third_canal_check.setChecked(
                self.boolean(self.tree.currentItem().text(30))
            )
            if self.baseline_checkbox.isChecked():
                self.deactivate_buttons(self.canal1buttons + [self.first_canal_check])
                self.deactivate_buttons(self.canal2buttons + [self.second_canal_check])
                self.deactivate_buttons(self.canal3buttons + [self.third_canal_check])
            else:
                self.activate_buttons(
                    [
                        self.first_canal_check,
                        self.second_canal_check,
                        self.third_canal_check,
                    ]
                )
            if self.first_canal_check.isChecked():
                self.activate_buttons(self.canal1buttons)
            else:
                self.deactivate_buttons(self.canal1buttons)
            if self.second_canal_check.isChecked():
                self.activate_buttons(self.canal2buttons)
            else:
                self.deactivate_buttons(self.canal2buttons)
            if self.third_canal_check.isChecked():
                self.activate_buttons(self.canal3buttons)
            else:
                self.deactivate_buttons(self.canal3buttons)
        except Exception as err:
            pass
        self.canal_running = False

    def canals_to_tree(self):
        """Transfer the canals attributes from the cells to the tree"""
        self.baseline_checkbox.setEnabled(True)
        if not self.canal_running:
            if self.baseline_checkbox.isChecked():
                self.deactivate_buttons(self.canal1buttons + [self.first_canal_check])
                self.deactivate_buttons(self.canal2buttons + [self.second_canal_check])
                self.deactivate_buttons(self.canal3buttons + [self.third_canal_check])
            else:
                self.activate_buttons(self.canal1buttons + [self.first_canal_check])
                self.activate_buttons(self.canal2buttons + [self.second_canal_check])
                self.activate_buttons(self.canal3buttons + [self.third_canal_check])
            if self.first_canal_check.isChecked():
                self.baseline_checkbox.setEnabled(False)
                self.activate_buttons(self.canal1buttons)
            else:
                self.deactivate_buttons(self.canal1buttons)
            if self.second_canal_check.isChecked():
                self.baseline_checkbox.setEnabled(False)
                self.activate_buttons(self.canal2buttons)
            else:
                self.deactivate_buttons(self.canal2buttons)
            if self.third_canal_check.isChecked():
                self.baseline_checkbox.setEnabled(False)
                self.activate_buttons(self.canal3buttons)
            else:
                self.deactivate_buttons(self.canal3buttons)
            if (
                self.first_canal_check.isChecked()
                or self.second_canal_check.isChecked()
                or self.third_canal_check.isChecked()
            ):
                self.deactivate_buttons([self.baseline_checkbox])
            else:
                self.activate_buttons([self.baseline_checkbox])
            self.tree.currentItem().setText(17, str(self.baseline_checkbox.isChecked()))
            self.tree.currentItem().setText(18, str(self.first_canal_check.isChecked()))
            self.tree.currentItem().setText(
                19, str(self.second_canal_check.isChecked())
            )
            self.tree.currentItem().setText(30, str(self.third_canal_check.isChecked()))
            self.enable_run(self.tree.check_global_validity())
            self.tree.graph(self.tree.currentItem(), current=True)
            self.draw()

    def enable_run(self, boolean):
        """Enable the run button"""
        if not self.daq_generated:
            boolean = False
        self.save_config_button.setEnabled(boolean)
        self.run_button.setEnabled(boolean)

    def disable_run(self):
        """Disable the run button"""
        self.save_config_button.setDisabled(True)
        self.run_button.setDisabled(True)

    def count_lights(self):
        """Return the number of lights and a list of their names"""
        count = 0
        text = []
        for checkbox in [
            self.ir_checkbox,
            self.red_checkbox,
            self.green_checkbox,
            self.fluorescence_checkbox,
        ]:
            if checkbox.isChecked():
                count += 1
                text.append(checkbox.text())
        return (count, text)

    def actualize_lights(self):
        """Update the lights list in the combo box"""
        self.preview_light_combo.clear()
        if self.count_lights()[0] == 0:
            self.preview_light_combo.setEnabled(False)
        else:
            self.preview_light_combo.setEnabled(True)
        for i in range(4):
            if i < self.count_lights()[0]:
                self.preview_light_combo.addItem(self.count_lights()[1][i])

    def boolean(self, string):
        """Return a boolean from a string"""
        if string == "True":
            return True
        return False

    def draw(self, root=False):
        """Draw the sitmulation channels graph
        
        Args:
            root (bool, optional): If True, the graph includes a progress bar"""
        try:
            self.plot_window.clear()
            self.plot_window.plot(
                self.tree.x_values, self.tree.stim1_values, root, index=0
            )
            self.plot_window.plot(
                self.tree.x_values,
                self.tree.stim2_values, root,
                index=1,
            )
            self.plot_window.plot(
                self.tree.x_values,
                self.tree.stim3_values, root,
                index=2,
            )
            self.tree.x_values = []
            self.tree.stim1_values = []
            self.tree.stim2_values = []
            self.tree.stim3_values = []
            self.elapsed_time = 0
        except Exception as err:
            pass

    def set_roi(self):
        """Set the ROI"""
        self.deactivate_buttons(buttons=self.enabled_buttons)
        self.stop_button.setEnabled(False)
        self.save_roi_button.setEnabled(False)
        self.roi_buttons.setCurrentIndex(1)

        def onselect_function(eclick, erelease):
            """Save the ROI dimensions as attributes"""
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
        """Reset the ROI"""
        plt.figure(self.image_view.figure.number)
        plt.xlim(0, int(1024 / self.config["Binning"]))
        plt.ylim(0, int(1024 / self.config["Binning"]))
        self.roi_extent = None
        self.reset_roi_button.setEnabled(False)

    def cancel_roi(self):
        """Cancel the ROI selection"""
        self.activate_buttons(buttons=self.enabled_buttons)
        self.roi_buttons.setCurrentIndex(0)
        self.rect_selector.clear()
        self.rect_selector = None

    def save_roi(self):
        """Save the ROI"""
        self.activate_buttons(buttons=self.enabled_buttons)
        self.roi_buttons.setCurrentIndex(0)
        plt.figure(self.image_view.figure.number)
        plt.ion()
        plt.xlim(self.roi_extent[0], self.roi_extent[1])
        plt.ylim(self.roi_extent[2], self.roi_extent[3])
        self.rect_selector.clear()
        self.rect_selector = None
        self.reset_roi_button.setEnabled(True)

    def verify_exposure(self):
        """Verify if the exposure/framerate combination is valid"""
        try:
            boolean_check = (int(self.exposure_cell.text()) / 1000 + 0.0015) * int(
                self.framerate_cell.text()
            ) < 1 and int(self.framerate_cell.text()) <= 57
        except Exception:
            boolean_check = False
        self.exposure_warning_label.setHidden(boolean_check)

    def check_if_thread_is_alive(self):
        """Check what threads are alive"""
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

        try:
            if self.live_save_thread.is_alive():
                print("Live Save thread is alive")
            else:
                print("Live Save thread is dead")
        except Exception as err:
            print(err)

        try:
            if self.baseline_check_thread.is_alive():
                print("Baseline check thread is alive")
            else:
                print("Baseline check thread is dead")
        except Exception as err:
            print(err)

    def initialize_buttons(self):
        """Define list of buttons to activate/deactivate"""
        self.canal1buttons = [
            self.stim_type_cell,
            self.pulses_label,
            self.pulses_cell,
            self.width_label,
            self.width_cell,
            self.jitter_label,
            self.jitter_cell,
            self.frequency_label,
            self.frequency_cell,
            self.duty_label,
            self.duty_cell,
            self.heigth_cell,
            self.heigth_label,
        ]
        self.canal2buttons = [
            self.stim_type_cell2,
            self.pulses_label2,
            self.pulses_cell2,
            self.width_label2,
            self.width_cell2,
            self.jitter_label2,
            self.jitter_cell2,
            self.frequency_label2,
            self.frequency_cell2,
            self.duty_label2,
            self.duty_cell2,
            self.heigth_cell2,
            self.heigth_label2,
        ]
        self.canal3buttons = [
            self.stim_type_cell3,
            self.pulses_label3,
            self.pulses_cell3,
            self.width_label3,
            self.width_cell3,
            self.jitter_label3,
            self.jitter_cell3,
            self.frequency_label3,
            self.frequency_cell3,
            self.duty_label3,
            self.duty_cell3,
            self.heigth_cell3,
            self.heigth_label3,
        ]
        self.enabled_buttons = [
            self.run_button,
            self.experiment_name_cell,
            self.mouse_id_cell,
            self.directory_choose_button,
            self.set_roi_button,
            self.reset_roi_button,
            self.experiment_name,
            self.mouse_id_label,
            self.framerate_label,
            self.framerate_cell,
            self.exposure_cell,
            self.exposure_label,
            self.add_brother_branch_button,
            self.add_child_branch_button,
            self.delete_item_button,
            self.red_checkbox,
            self.ir_checkbox,
            self.green_checkbox,
            self.fluorescence_checkbox,
            self.stimulation_name_label,
            self.directory_save_files_checkbox,
            self.stimulation_name_cell,
            self.stim_type_cell,
            self.stim_type_cell2,
            self.first_canal_check,
            self.second_canal_check,
            self.first_signal_type_duration_label,
            self.duration_cell,
            self.pulses_label,
            self.pulses_cell,
            self.width_label,
            self.width_cell,
            self.jitter_label,
            self.jitter_cell,
            self.frequency_label,
            self.frequency_cell,
            self.heigth_label,
            self.heigth_cell,
            self.duty_label,
            self.duty_cell,
            self.pulses_label2,
            self.pulses_cell2,
            self.width_label2,
            self.width_cell2,
            self.jitter_label2,
            self.jitter_cell2,
            self.frequency_label2,
            self.frequency_cell2,
            self.heigth_label2,
            self.heigth_cell2,
            self.duty_label2,
            self.duty_cell2,
            self.third_canal_check,
            self.stim_type_cell3,
            self.pulses_label3,
            self.pulses_cell3,
            self.width_label3,
            self.width_cell3,
            self.jitter_label3,
            self.jitter_cell3,
            self.frequency_label3,
            self.frequency_cell3,
            self.duty_label3,
            self.duty_cell3,
            self.heigth_cell3,
            self.heigth_label3,
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
            self.tree,
        ]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("IBM Plex Sans")
    app.setFont(font)
    ex = App()
    sys.exit(app.exec_())
