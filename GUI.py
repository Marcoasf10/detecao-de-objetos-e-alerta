import sys

from PyQt5.QtWidgets import *
import testeCv


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Object Detection")
        self.setGeometry(500, 500, 500, 500)

        layout = QVBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QVBoxLayout()
        layout4 = QVBoxLayout()

        self.label = QLabel("Choose device to connect to:")
        self.objectsSelected = QListWidget()
        self.availableObjects = QListWidget()
        self.label2 = QLabel("Objects to detect: ")
        self.availableObjects.addItems(['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'])
        self.objectsSelected.currentTextChanged.connect(self.text_changed)
        self.availableObjects.currentTextChanged.connect(self.text_changed)

        self.button = QPushButton("Start Detection")
        self.buttonRemove = QPushButton("Remove (-)")
        self.buttonAdd = QPushButton("Add (+)")
        self.buttonTrain = QPushButton("Train new Object")
        self.button.clicked.connect(self.run_script)

        self.listDevices = QListWidget()

        self.button2 = QPushButton("Search Devices")
        self.button2.clicked.connect(self.update_camera_list)

        layout3.addWidget(self.objectsSelected)
        layout3.addWidget(self.buttonRemove)
        layout4.addWidget(self.availableObjects)
        layout4.addWidget(self.buttonAdd)
        layout2.addLayout(layout3)
        layout2.addWidget(self.buttonTrain)
        layout2.addLayout(layout4)
        layout.addLayout(layout2)
        layout.addWidget(self.label)
        layout.addWidget(self.listDevices)
        layout.addWidget(self.button2)
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
        num_devices = self.list_available_cameras()
        self.listDevices.clear()
        for i in range(num_devices):
            item = "Device : " + str(i)
            self.listDevices.addItem(item)
            self.listDevices.item(self.listDevices.count() - 1).setData(0, item)

    def list_available_cameras(self):
        try:
            num_devices = testeCv.list_available_cameras()
            return num_devices
        except Exception as e:
            print(f"Error executing script: {e}")
            return 0

    def text_changed(self, s):
        print("Current text:", s)

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
