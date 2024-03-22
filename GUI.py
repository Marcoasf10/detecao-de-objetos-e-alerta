from PyQt5.QtWidgets import *
from importlib import util


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
        if device:
            try:
                spec = util.spec_from_file_location("testeCv", "testeCv.py")
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Here you can specify the function you want to run dynamically
                function_name = "runscript"

                if hasattr(module, function_name):
                    function_to_run = getattr(module, function_name)
                    function_to_run(int(device))
                else:
                    print(f"Function '{function_name}' not found in the module.")
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
        spec = util.spec_from_file_location("testeCv", "testeCv.py")
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        function_name = "list_available_cameras"

        if hasattr(module, function_name):
            function_to_run = getattr(module, function_name)
            num_devices = function_to_run()
            print("Numero devices:", num_devices)
            return num_devices
        else:
            print(f"Function '{function_name}' not found in the module.")

    except Exception as e:
        print(f"Error executing script: {e}")
        return 0


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
