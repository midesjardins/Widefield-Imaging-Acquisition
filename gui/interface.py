
from curses.panel import top_panel
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import *

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Widefield Imaging Aquisition'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignTop)

        self.experiment_settings_label = QLabel('Experiment Settings')
        self.experiment_settings_label.setFont(QFont("Helvetica", 16))
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
        self.directory_cell = QLineEdit("")
        self.directory_cell.setReadOnly(True)
        self.directory_window.addWidget(self.directory_cell)
        self.directory_choose_button = QPushButton("Choose")
        self.directory_choose_button.setIcon(QIcon("gui/icons/folder-plus.png"))
        self.directory_choose_button.clicked.connect(self.choose_directory)
        self.directory_window.addWidget(self.directory_choose_button)
        self.experiment_settings_main_window.addLayout(self.directory_window)

        self.grid_layout.addLayout(self.experiment_settings_main_window, 1, 0)

        self.image_settings_label = QLabel('Image Settings')
        self.image_settings_label.setFont(QFont("Helvetica", 16))
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
        self.speckle_button = QCheckBox('Infrared')
        self.image_settings_second_window.addWidget(self.speckle_button)
        self.red_button = QCheckBox('Red')
        self.image_settings_second_window.addWidget(self.red_button)
        self.green_button = QCheckBox('Green')
        self.image_settings_second_window.addWidget(self.green_button)
        self.fluorescence_button = QCheckBox('Blue')
        self.image_settings_second_window.addWidget(self.fluorescence_button)
        self.image_settings_main_window.addLayout(self.image_settings_second_window)
        
        self.grid_layout.addLayout(self.image_settings_main_window, 1, 1)

        self.live_preview_label = QLabel('Live Preview')
        self.live_preview_label.setFont(QFont("Helvetica", 16))
        self.grid_layout.addWidget(self.live_preview_label, 0, 2)

        self.live_preview_pixmap = QPixmap('mouse.jpg')
        self.live_preview_image = QLabel(self)
        self.live_preview_image.setPixmap(self.live_preview_pixmap)
        self.live_preview_image.resize(self.live_preview_pixmap.width(),
                          self.live_preview_pixmap.height())
        self.grid_layout.addWidget(self.live_preview_image, 1, 2)

        self.stimulation_tree_label = QLabel('Stimulation Tree')
        self.stimulation_tree_label.setFont(QFont("Helvetica", 16))
        self.grid_layout.addWidget(self.stimulation_tree_label, 2, 0)

        self.stimulation_tree_window = QVBoxLayout()
        self.stimulation_tree = QTreeWidget()
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
        
        #self.stimulation_tree_window.addLayout(self.stimulation_tree_switch_window)
        self.stimulation_tree_switch_window.setCurrentIndex(1)
        self.grid_layout.addLayout(self.stimulation_tree_window, 3, 0)

        self.signal_adjust_label = QLabel('Signal Adjust')
        self.signal_adjust_label.setFont(QFont("Helvetica", 16))
        self.grid_layout.addWidget(self.signal_adjust_label, 2, 1)


        self.signal_adjust_superposed = QStackedLayout()
        self.stimulation_edit_layout = QVBoxLayout()

        self.stimulation_name_label = QLabel("Stimulation Name")
        self.stimulation_name_cell = QLineEdit()
        self.stimulation_name_cell.textEdited.connect(self.change_branch_name)
        self.stimulation_name_window = QHBoxLayout()
        self.stimulation_name_window.addWidget(self.stimulation_name_label)
        self.stimulation_name_window.addWidget(self.stimulation_name_cell)
        self.stimulation_edit_layout.addLayout(self.stimulation_name_window)



        self.stimulation_edit_container = QWidget()
        self.stimulation_edit_container.setLayout(self.stimulation_edit_layout)
        self.block_edit_layout = QVBoxLayout()

        self.block_name_label = QLabel("Block Name")
        self.block_name_cell = QLineEdit()
        self.block_name_cell.textEdited.connect(self.change_branch_name)
        self.block_name_window = QHBoxLayout()
        self.block_name_window.addWidget(self.block_name_label)
        self.block_name_window.addWidget(self.block_name_cell)
        self.block_edit_layout.addLayout(self.block_name_window)



        self.block_edit_container = QWidget()
        self.block_edit_container.setLayout(self.block_edit_layout)
        self.signal_adjust_superposed.addWidget(self.stimulation_edit_container)
        self.signal_adjust_superposed.addWidget(self.block_edit_container)
        self.signal_adjust_superposed.addWidget(QLabel())
        self.signal_adjust_superposed.setCurrentIndex(2)
        self.grid_layout.addLayout(self.signal_adjust_superposed, 3, 1)

        

        self.signal_preview_label = QLabel('Signal Preview')
        self.signal_preview_label.setFont(QFont("Helvetica", 16))
        self.grid_layout.addWidget(self.signal_preview_label, 2, 2)

        self.buttons_main_window = QHBoxLayout()
        self.stop_button = QPushButton('Stop')
        self.stop_button.setIcon(QIcon("gui/icons/player-stop.png"))
        self.stop_button.clicked.connect(self.stop)
        self.buttons_main_window.addWidget(self.stop_button)
        self.run_button = QPushButton('Run')
        self.run_button.setIcon(QIcon("gui/icons/player-play.png"))
        self.run_button.clicked.connect(self.run)
        self.buttons_main_window.addWidget(self.run_button)
        self.test_tree = QTreeWidget()
        self.grid_layout.addWidget(self.test_tree, 3,2)
        self.grid_layout.addLayout(self.buttons_main_window, 4, 2)

        self.show()

    def run(self):
        lights = []
        if self.speckle_button.isChecked():
            lights.append('ir')
        if self.red_button.isChecked():
            lights.append('red')
        if self.green_button.isChecked():
            lights.append('green')
        if self.fluorescence_button.isChecked():
            lights.append('blue')
        print('\n'.join(lights))

    def stop(self):
        pass

    def choose_directory(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory_cell.setText(folder)

    def delete_branch(self):
        try:
            root = self.stimulation_tree.invisibleRootItem()
            parent = self.stimulation_tree.currentItem().parent()
            if parent.childCount() == 1:
                parent.setIcon(0, QIcon("gui/icons/wave-square.png"))
            (parent or root).removeChild(self.stimulation_tree.currentItem())
            self.actualize_tree()
        except Exception:
            root.removeChild(self.stimulation_tree.currentItem())
            self.actualize_tree()
        
    
    def add_brother(self):
        if self.stimulation_tree.currentItem():
            stimulation_tree_item = QTreeWidgetItem()
            stimulation_tree_item.setText(0, "No Name")
            stimulation_tree_item.setForeground(0, QBrush(QColor(211,211,211)))
            stimulation_tree_item.setIcon(0, QIcon("gui/icons/wave-square.png"))
            parent = self.stimulation_tree.selectedItems()[0].parent()
            if parent:
                index = parent.indexOfChild(self.stimulation_tree.selectedItems()[0])
                parent.insertChild(index+1, stimulation_tree_item)
            else:
                self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
        else:
            pass

    def add_child(self):
        if self.stimulation_tree.currentItem():
            self.stimulation_tree.currentItem().setIcon(0, QIcon("gui/icons/package.png"))
            stimulation_tree_item = QTreeWidgetItem()
            stimulation_tree_item.setIcon(0, QIcon("gui/icons/wave-square.png"))
            stimulation_tree_item.setText(0,"No Name")
            stimulation_tree_item.setForeground(0, QBrush(QColor(211,211,211)))
            self.stimulation_tree.selectedItems()[0].addChild(stimulation_tree_item)
            self.stimulation_tree.selectedItems()[0].setExpanded(True)
            self.stimulation_tree.setCurrentItem(stimulation_tree_item)
        else:
            pass

    def actualize_tree(self):
        if self.stimulation_tree.currentItem():
            self.stimulation_tree_switch_window.setCurrentIndex(0)
        else:
            self.stimulation_tree_switch_window.setCurrentIndex(1)
        try:
            if self.stimulation_tree.currentItem().childCount() > 0:
                self.signal_adjust_superposed.setCurrentIndex(1)
                if self.stimulation_tree.currentItem().text(0) != "No Name":
                    self.block_name_cell.setText(self.stimulation_tree.currentItem().text(0))
                else:
                    self.block_name_cell.setText("")
            else:
                self.signal_adjust_superposed.setCurrentIndex(0)
                if self.stimulation_tree.currentItem().text(0) != "No Name":
                    self.stimulation_name_cell.setText(self.stimulation_tree.currentItem().text(0))
                else:
                    self.stimulation_name_cell.setText("")
        except Exception:
            self.signal_adjust_superposed.setCurrentIndex(2)



    def first_stimulation(self):
        stimulation_tree_item = QTreeWidgetItem()
        stimulation_tree_item.setForeground(0, QBrush(QColor(211,211,211)))
        stimulation_tree_item.setIcon(0, QIcon("gui/icons/wave-square.png"))
        stimulation_tree_item.setText(0, "No Name")
        self.stimulation_tree.addTopLevelItem(stimulation_tree_item)
        self.stimulation_tree_switch_window.setCurrentIndex(0)
        self.stimulation_tree.setCurrentItem(stimulation_tree_item)

    def change_branch_name(self):
        branch = self.stimulation_tree.currentItem()
        branch.setForeground(0, QBrush(QColor(0, 0, 0)))
        if branch.childCount() > 0:
            branch.setText(0, self.block_name_cell.text())
        else:
            branch.setText(0, self.stimulation_name_cell.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())