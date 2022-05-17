
from curses.panel import top_panel
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 file system view - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.model = QFileSystemModel()
        self.model.setRootPath('')
        self.tree = QTreeWidget()
        self.item = QTreeWidgetItem()
        self.item.setText(0,"Test")
        self.tree.addTopLevelItem(self.item)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignTop)

        self.experiment_settings_label = QLabel('Experiment Settings')
        self.grid_layout.addWidget(self.experiment_settings_label, 0,0)

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
        self.directory_label = QLabel('Directory')
        self.directory_window.addWidget(self.directory_label)
        self.directory_cell = QLineEdit()
        self.directory_window.addWidget(self.directory_cell)
        self.experiment_settings_main_window.addLayout(self.directory_window)

        self.grid_layout.addLayout(self.experiment_settings_main_window, 1, 0)

        self.image_settings_label = QLabel('Image Settings')
        self.grid_layout.addWidget(self.image_settings_label, 0,1)

        self.image_settings_main_window = QVBoxLayout()

        self.framerate_window = QHBoxLayout()
        self.framerate_label = QLabel('Framerate')
        self.framerate_window.addWidget(self.framerate_label)
        self.framerate_cell = QLineEdit('30')
        self.framerate_window.addWidget(self.framerate_cell)
        self.image_settings_main_window.addLayout(self.framerate_window)

        self.exposure_window = QHBoxLayout()
        self.exposure_label = QLabel('Exposure')
        self.exposure_window.addWidget(self.exposure_label)
        self.exposure_cell = QLineEdit('10')
        self.exposure_window.addWidget(self.exposure_cell)
        self.image_settings_main_window.addLayout(self.exposure_window)

        self.image_settings_second_window = QHBoxLayout()
        self.speckle_button = QCheckBox('Speckle')
        self.image_settings_second_window.addWidget(self.speckle_button)
        self.intrinsic_button = QCheckBox('Intrinsic')
        self.image_settings_second_window.addWidget(self.intrinsic_button)
        self.fluorescence_button = QCheckBox('Fluorescence')
        self.image_settings_second_window.addWidget(self.fluorescence_button)
        self.image_settings_main_window.addLayout(self.image_settings_second_window)
        
        self.grid_layout.addLayout(self.image_settings_main_window, 1, 1)

        self.live_preview_label = QLabel('Live Preview')
        self.grid_layout.addWidget(self.live_preview_label, 0, 2)

        self.live_preview_pixmap = QPixmap('mouse.jpg')
        self.live_preview_image = QLabel(self)
        self.live_preview_image.setPixmap(self.live_preview_pixmap)
        self.live_preview_image.resize(self.live_preview_pixmap.width(),
                          self.live_preview_pixmap.height())
        self.grid_layout.addWidget(self.live_preview_image, 1, 2)

        self.stimulation_tree_label = QLabel('Stimulation Tree')
        self.grid_layout.addWidget(self.stimulation_tree_label, 2, 0)

        self.signal_adjust_label = QLabel('Signal Adjust')
        self.grid_layout.addWidget(self.signal_adjust_label, 2, 1)

        self.signal_preview_label = QLabel('Signal Preview')
        self.grid_layout.addWidget(self.signal_preview_label, 2, 2)

        self.buttons_main_window = QHBoxLayout()
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop)
        self.buttons_main_window.addWidget(self.stop_button)
        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.run)
        self.buttons_main_window.addWidget(self.run_button)
        self.grid_layout.addLayout(self.buttons_main_window, 3, 2)

        self.show()

    def run(self):
        lights = []
        if self.speckle_button.isChecked():
            lights.append('ir')
        if self.intrinsic_button.isChecked():
            lights.append('red')
            lights.append('green')
        if self.fluorescence_button.isChecked():
            lights.append('blue')
        print('\n'.join(lights))

    def stop(self):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())