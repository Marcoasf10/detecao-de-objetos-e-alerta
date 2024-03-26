from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

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
        self.objectsSelected.setSelectionMode(QAbstractItemView.MultiSelection)
        self.availableObjects = QListWidget()
        self.availableObjects.setSelectionMode(QAbstractItemView.MultiSelection)
        self.search_bar = QLineEdit()
        self.search_bar2 = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar2.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_list)
        self.search_bar2.textChanged.connect(self.filter_list_selected)
        self.label2 = QLabel("Objects to detect: ")
        self.class_names = testeCv.get_classes()
        self.class_names_selected = []
        self.availableObjects.addItems(sorted(self.class_names))

        self.button = QPushButton("Start Detection")
        self.buttonRemove = QPushButton("Remove (-)")
        self.buttonAdd = QPushButton("Add (+)")
        self.buttonAdd.clicked.connect(self.buttonAddf)
        self.buttonRemove.clicked.connect(self.buttonRemovef)
        self.buttonTrain = QPushButton("Train new Object")
        self.button.clicked.connect(self.run_script)

        self.listDevices = QListWidget()
        self.listDevices.setSelectionMode(QAbstractItemView.MultiSelection)
        self.button2 = QPushButton("Search Devices")
        self.button2.clicked.connect(self.update_camera_list)

        layout3.addWidget(self.search_bar2)
        layout3.addWidget(self.objectsSelected)
        layout3.addWidget(self.buttonRemove)
        layout4.addWidget(self.search_bar)
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
        devices = 0
        if devices >= 0:
            try:
                testeCv.runscript(0, self.class_names_selected)
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

    def filter_list(self):
        search_text = self.search_bar.text().lower()
        self.availableObjects.clear()
        filtered_items = [item for item in self.class_names if search_text in item.lower()]
        self.availableObjects.addItems(sorted(filtered_items))

    def filter_list_selected(self):
        print(self.class_names_selected)
        search_text = self.search_bar2.text().lower()
        self.objectsSelected.clear()
        filtered_items = [item for item in self.class_names_selected if search_text in item.lower()]
        self.objectsSelected.addItems(sorted(filtered_items))

    def buttonAddf(self):
        selected_items = self.availableObjects.selectedItems()
        for item in selected_items:
            if self.objectsSelected.findItems(item.text(), Qt.MatchExactly) == []:
                self.objectsSelected.addItem(item.text())
                self.availableObjects.takeItem(self.availableObjects.row(item))
                self.class_names.remove(item.text())
                self.class_names_selected.append(item.text())
        print(self.class_names_selected)
        self.repaint()

    def buttonRemovef(self):
        selected_items = self.objectsSelected.selectedItems()
        for item in selected_items:
            if self.objectsSelected.findItems(item.text(), Qt.MatchExactly):
                self.objectsSelected.takeItem(self.objectsSelected.row(item))
                self.availableObjects.addItem(item.text())
                self.class_names_selected.remove(item.text())
        self.availableObjects.sortItems()
        self.repaint()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
