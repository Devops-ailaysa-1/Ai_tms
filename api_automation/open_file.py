import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
    QPushButton, QVBoxLayout, QFileDialog, QLineEdit, QFormLayout,QLabel

# you can copy and run this code

class MainWindow(QMainWindow):

    file_name = ''

    def __init__(self, app,parent=None):#--------------
        super(MainWindow, self).__init__(parent)#  |
        self.setWindowTitle("open file dialog")#   |

#
        #												   |
        btn = QPushButton("Open File")#            |---- Just initialization
        layout = QFormLayout()#					   |
        layout.addWidget(btn)#                     |
        widget = QWidget()#                        |
        widget.setLayout(layout)#
        self.nameLineEdit = QLineEdit()
        layout.addRow(QLabel("Project_Name"), self.nameLineEdit)

                                #                |
        self.setCentralWidget(widget)#-------------

        btn.clicked.connect(self.open) # connect clicked to self.open()
        self.show()
        print("text---->", self.nameLineEdit.text())
        app.exec_()
        app.quit()

    def open(self):
        path = QFileDialog.getOpenFileName(self, 'Open a file', '',
                                        'All Files (*.*)')
        if path != ('', ''):
            print("File path : "+ path[0])
            print("text---->", self.nameLineEdit.text())
            self.file_name = path[0]

    def run():
        app = QApplication(sys.argv)
        window = MainWindow(app=app)
        return window.file_name

if __name__ == "__main__":
    pass
    # sys.exit(app.exec_())