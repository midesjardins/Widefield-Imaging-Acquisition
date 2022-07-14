from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QGridLayout, QLabel, QHBoxLayout, QLineEdit, QCheckBox, QPushButton, QStackedLayout, QTreeWidget, QComboBox, QMessageBox, QFileDialog, QTreeWidgetItem, QApplication, QAction, QMenuBar, QProgressBar
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QIcon, QBrush, QColor
from PyQt5.QtCore import Qt
import sys
import os
from threading import Thread
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.data_handling import extract_from_path, separate_images, separate_vectors
import numpy as np


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Widefield Post Processing'
        self.left = 10
        self.top = 10
        self.width = 600
        self.height = 150
        self.initUI()

    def closeEvent(self, *args, **kwargs):
        print("Closed")

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.directory_layout = QHBoxLayout()
        self.choose_directory_button = QPushButton("Choose Directory")
        self.choose_directory_button.setIcon(QIcon("gui/icons/folder-plus.png"))
        self.choose_directory_button.clicked.connect(self.choose_directory)
        self.directory_layout.addWidget(self.choose_directory_button)
        self.directory_cell = QLineEdit()
        self.directory_cell.setEnabled(False)
        self.directory_layout.addWidget(self.directory_cell)
        self.main_layout.addLayout(self.directory_layout)

        self.split_button = QPushButton("Separate Light Channels")
        self.split_button.setIcon(QIcon("gui/icons/arrows-split.png"))
        self.split_button.setEnabled(False)
        self.split_button.clicked.connect(self.open_split_thread)
        self.main_layout.addWidget(self.split_button)

        self.progress_bar = QProgressBar()
        self.progress_bar_label = QLabel("")
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.progress_bar_label)
        self.show()

    def choose_directory(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.directory_cell.setText(folder)
        self.split_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar_label.setText(f"")

    def open_split_thread(self):
        self.choose_directory_button.setEnabled(False)
        self.split_button.setEnabled(False)
        self.split_arrays_thread = Thread(target=self.split_arrays)
        self.split_arrays_thread.start()


    def split_arrays(self):
        path = self.directory_cell.text()
        self.progress_bar_label.setText(f"Extracting Files...")
        lights, frames, vector = extract_from_path(path)
        self.progress_bar.setMaximum(2*len(lights)-1)
        arrays = separate_images(lights, frames)
        vectors = separate_vectors(lights, vector)
        for i, array in enumerate(arrays):
            self.progress_bar.setValue(2*i)
            self.progress_bar_label.setText(f"Saving {lights[i].capitalize()} Channel...")
            np.save(os.path.join(path, f"{lights[i]}.npy"), array)
            self.progress_bar_label.setText(f"Saving {lights[i].capitalize()} Metadata...")
            np.save(os.path.join(path, f"{lights[i]}-signals.npy"), vectors[i])
            self.progress_bar.setValue(2*i+1)
        self.progress_bar_label.setText(f"Done!")
        self.choose_directory_button.setEnabled(True)
        self.split_button.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily("IBM Plex Sans")
    app.setFont(font)
    ex = App()
    sys.exit(app.exec_())
