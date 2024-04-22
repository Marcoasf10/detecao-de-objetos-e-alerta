import math
import time

from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from threading import Thread
import testeCv
import cv2
from multiprocessing import Process, Queue

class ImageViewerWindow(QMainWindow):
    def __init__(self, devices):
        super().__init__()

        self.screen_geometry = app.desktop().screenGeometry()
        self.setGeometry(0, 0, self.screen_geometry.width(), self.screen_geometry.height())
        self.setWindowTitle("Image Viewer")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout principal para organizar os locais das imagens
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Layout de grade para organizar os locais das imagens
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)

        # Lista para armazenar os QLabel para exibir as imagens
        self.image_labels = {}

        # Criar locais para exibir imagens com base no número fornecido
        self.create_image_locations(devices)
    def create_image_locations(self, devices):
        num_colunas = round(math.sqrt(len(devices)))
        i = 0
        for device in devices:
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            self.image_labels[device] = label
            row = i // num_colunas
            col = i % num_colunas
            self.grid_layout.addWidget(label, row, col)
            column_width = self.screen_geometry.width() // num_colunas

            pixmap = QPixmap("frames/noCamera.jpg")
            scaled_pixmap = pixmap.scaled(column_width, pixmap.height() // 2, Qt.KeepAspectRatio)
            self.image_labels[device].setPixmap(scaled_pixmap)
            self.image_labels[device].setPixmap(scaled_pixmap)
            i += 1

    def update_image(self, frame, device):
        if device in self.image_labels.keys():
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            # Convert BGR to RGB
            img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            pixmap = pixmap.scaled(self.image_labels[device].size(), aspectRatioMode=Qt.KeepAspectRatio)
            self.image_labels[device].setPixmap(pixmap)
class MainWindow(QWidget):
    thread_finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Object Detection")
        self.setGeometry(500, 500, 500, 500)
        self.queue = Queue()
        layout = QVBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QVBoxLayout()
        layout4 = QVBoxLayout()
        gridLayout = QGridLayout()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image_from_queue)
        self.label = QLabel("Choose device to connect to:")
        self.objectsSelected = QListWidget()
        self.graphs = False
        self.graphCheckBox = QCheckBox()
        self.graphCheckBox.setText("Graphs")
        self.device_windows = {}
        self.graphCheckBox.stateChanged.connect(self.checkedGraphs)
        self.graphCheckBox.move(20, 40)
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
        self.label3 = QLabel("Searching for devices...")
        self.label4 = QLabel("Objects to find:")
        self.label5 = QLabel("Objects available:")
        self.label3.hide()
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

        layout3.addWidget(self.label4)
        layout3.addWidget(self.search_bar2)
        layout3.addWidget(self.objectsSelected)
        layout3.addWidget(self.buttonRemove)
        layout4.addWidget(self.label5)
        layout4.addWidget(self.search_bar)
        layout4.addWidget(self.availableObjects)
        layout4.addWidget(self.buttonAdd)
        layout2.addLayout(layout3)
        layout2.addWidget(self.buttonTrain)
        layout2.addLayout(layout4)
        layout.addLayout(layout2)
        layout.addWidget(self.label)
        layout.addWidget(self.listDevices)
        layout.addWidget(self.label3)
        layout.addWidget(self.button2)
        layout.addWidget(self.button)
        layout.addLayout(gridLayout)
        gridLayout.addWidget(self.graphCheckBox,0,0, alignment=Qt.AlignCenter)
        self.image_window = None
        self.setLayout(layout)

    def run_script(self):
        devices = [item.data(1) for item in self.listDevices.selectedItems()]
        #devices.append("http://62.131.207.209:8080/cam_1.cgi")
        #devices.append("http://97.68.104.34:80/mjpg/video.mjpg")
        self.image_window = ImageViewerWindow(devices)
        self.image_window.show()
        if len(devices) > 0:
            self.button.setEnabled(False)
            try:
                thread = Thread(target=self.run_script_thread, args=(devices, self.class_names_selected, self.graphs, True, self.queue))
                thread.start()
                Thread(target=self.wait_for_thread, args=(thread,)).start()
                Thread(target=self.readQueue).start()
            except Exception as e:
                print(f"Error executing script: {e}")
        else:
            print("No device selected.")

    def update_image_from_queue(self):
        try:
            frames = self.queue.get(timeout=0.4)
            if frames == -1:
                self.timer.stop()
                return 1
            for device, frame in frames.items():
                self.image_window.update_image(frame, device)

            return 0
        except self.queue.empty:
            print("Queue is empty.")
            return 0

    def readQueue(self):
        while True:
            try:
                frames = self.queue.get()
                if frames == -1:
                    self.timer.stop()
                for device, frame in frames.items():
                    self.image_window.update_image(frame, device)
            except self.queue.empty:
                print("Queue is empty.")
            time.sleep(0.5)
    def wait_for_thread(self, thread):
        thread.join()
        self.button.setEnabled(True)

    @staticmethod
    def run_script_thread(devices, selected, graphs, mac, queue):
        if mac:
            #testeCv.runscriptSingle(devices, selected, queue,graphs)
            testeCv.runscriptgrabRetrieve(devices, selected, queue, graphs)
            #testeCv.runscriptMac(devices, selected, queue,graphs)
        else:
            testeCv.runscriptgrabRetrieve(devices, selected, graphs)
            #testeCv.runscript(devices, selected,graphs)

    def update_camera_list(self):
        Thread(target=self.search_for_cameras).start()


    def search_for_cameras(self):
        self.label3.show()
        self.button2.setEnabled(False)
        num_devices = self.list_available_cameras()
        self.listDevices.clear()
        for i in range(num_devices):
            item = "Device : " + str(i)
            self.listDevices.addItem(item)
            self.listDevices.item(self.listDevices.count() - 1).setData(0, item)  # Set display text
            self.listDevices.item(self.listDevices.count() - 1).setData(1, i)  # Set data
        self.label3.hide()
        self.button2.setEnabled(True)

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
        self.repaint()

    def buttonRemovef(self):
        selected_items = self.objectsSelected.selectedItems()
        for item in selected_items:
            if self.objectsSelected.findItems(item.text(), Qt.MatchExactly):
                self.objectsSelected.takeItem(self.objectsSelected.row(item))
                self.availableObjects.addItem(item.text())
                self.class_names.append(item.text())
                self.class_names_selected.remove(item.text())
        self.availableObjects.sortItems()
        self.repaint()

    def checkedGraphs(self, checked):
        if checked:
            self.graphs = True
        else:
            self.graphs = False
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
