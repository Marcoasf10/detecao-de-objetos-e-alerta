from PyQt5.QtWidgets import *
import testeCv


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deteção de objetos")
        self.setGeometry(500, 500, 500, 500)

        layout = QVBoxLayout()

        self.label = QLabel("Choose device to connect to:")
        self.button = QPushButton("Run script")
        self.button.clicked.connect(self.run_script)

        self.comboBox = QComboBox()

        self.label2 = QLabel("Press the button to search for cameras:")
        self.button2 = QPushButton("Search Devices")
        self.button2.clicked.connect(self.update_camera_list)

        layout.addWidget(self.label2)
        layout.addWidget(self.button2)
        layout.addWidget(self.label)
        layout.addWidget(self.comboBox)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def run_script(self):
        device = self.comboBox.currentData()
        if device >= 0:
            try:
                testeCv.runscript(int(device))
            except Exception as e:
                print(f"Error executing script: {e}")
        else:
            print("No device selected.")

    def update_camera_list(self):
        num_devices = list_available_cameras()
        self.comboBox.clear()
        for i in range(num_devices):
            self.comboBox.addItem("Device : " + str(i), i)


def list_available_cameras():
    try:
        num_devices = testeCv.list_available_cameras()
        return num_devices

    except Exception as e:
        print(f"Error executing script: {e}")
        return 0


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
