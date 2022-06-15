from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QGridLayout, QLabel, QHBoxLayout, QLineEdit, QCheckBox, QPushButton, QStackedLayout, QTreeWidget, QComboBox, QMessageBox, QFileDialog, QTreeWidgetItem, QApplication, QAction, QMenuBar
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QIcon, QBrush, QColor
from PyQt5.QtCore import Qt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.data_handling import split_frames_in_path


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Widefield Post Processing'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def closeEvent(self, *args, **kwargs):
        print("Closed")

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.directory_layout = QHBoxLayout()
        self.choose_directory_button = QPushButton("Choose Directory")
        self.choose_directory_button.clicked.connect(self.choose_directory)
        self.directory_layout.addWidget(self.choose_directory_button)
        self.directory_cell = QLineEdit()
        self.directory_cell.setEnabled(False)
        self.directory_layout.addWidget(self.directory_cell)
        self.main_layout.addLayout(self.directory_layout)

        self.split_button = QPushButton("Separate Arrays")
        self.split_button.setEnabled(False)
        self.split_button.clicked.connect(self.split_arrays)
        self.main_layout.addWidget(self.split_button)
        self.show()

    def choose_directory(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory_cell.setText(folder)
        self.split_button.setEnabled(True)

    def split_arrays(self):
        split_frames_in_path(self.directory_cell.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("IBM Plex Sans")
    app.setFont(font)
    ex = App()
    sys.exit(app.exec_())
