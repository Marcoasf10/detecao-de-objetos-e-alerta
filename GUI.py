from PyQt5.QtWidgets import *
from importlib import util
# from importlib import import_module


def main():
    app = QApplication([])

    window = QWidget()
    window.setGeometry(500, 500, 500, 500)
    window.setWindowTitle("Deteção de objetos")

    layout = QVBoxLayout()
    label = QLabel("Press the button to start record:")
    button = QPushButton("Run script")
    button.clicked.connect(run_script)
    label2 = QLabel("Press the button to search for cameras:")
    button2 = QPushButton("search devices")
    button2.clicked.connect(list_available_cameras)
    button.setGeometry(50, 30, 100, 30)

    layout.addWidget(label)
    layout.addWidget(button)
    layout.addWidget(label2)
    layout.addWidget(button2)

    window.setLayout(layout)

    window.show()
    app.exec()


def run_script(self):
    try:
        spec = util.spec_from_file_location("testeCv", "testeCv.py")
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Here you can specify the function you want to run dynamically
        function_name = "runscript"

        if hasattr(module, function_name):
            function_to_run = getattr(module, function_name)
            function_to_run()
        else:
            print(f"Function '{function_name}' not found in the module.")
    except Exception as e:
        print(f"Error executing script: {e}")


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
        else:
            print(f"Function '{function_name}' not found in the module.")

    except Exception as e:
        print(f"Error executing script: {e}")


if __name__ == '__main__':
    main()
