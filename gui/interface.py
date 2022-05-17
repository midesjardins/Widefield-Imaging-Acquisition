
import sys
from PyQt5.QtWidgets import *
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
        self.button = QCheckBox()
        self.button.clicked.connect(self.clickme)
        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.tree)
        windowLayout.addWidget(self.button)
        self.setLayout(windowLayout)
        
        self.show()

    def clickme(self):
        self.tree.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())