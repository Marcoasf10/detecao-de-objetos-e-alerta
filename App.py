import time
from multiprocessing import Queue
from threading import Thread

import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedLayout, \
    QListWidget, QScrollArea, QMainWindow, QDialog, QLineEdit, QComboBox, QCheckBox
from PyQt5 import QtCore
import yoloScript


class DispositivoWidget(QWidget):
    image_clicked = QtCore.pyqtSignal(str, QPixmap)  # Define a signal with device name
    setting_clicked = QtCore.pyqtSignal(str, list)  # Define a signal for setting button clicked

    def __init__(self, name, device,objToFind):
        super().__init__()
        self.name = name
        self.image_path = "frames/noCamera.jpg"  # Store the image path
        self.objToFind = objToFind
        layout = QVBoxLayout(self)
        self.device = device
        # Create a horizontal layout for the label and setting button
        top_layout = QHBoxLayout()
        self.label = QLabel(name)
        top_layout.addWidget(self.label)

        # Setting button
        self.setting_button = QPushButton("Settings")
        self.setting_button.clicked.connect(self.setting_button_clicked)
        top_layout.addWidget(self.setting_button)

        layout.addLayout(top_layout)

        layout_imagem = QVBoxLayout()

        self.image_label = QLabel()
        pixmap = QPixmap(self.image_path)
        pixmap = pixmap.scaledToWidth(700)
        self.image_label.setPixmap(pixmap)
        layout_imagem.addWidget(self.image_label, alignment=Qt.AlignCenter)
        self.pausa_label = QLabel("CAMARA PAUSADA!")
        font = QFont()
        font.setBold(True)
        font.setPointSize(15)
        self.pausa_label.setFont(font)
        self.pausa_label.hide()
        layout_imagem.addWidget(self.pausa_label, alignment=Qt.AlignCenter)
        layout.addLayout(layout_imagem)
        # Buttons for start, stop, and live
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.live_button = QPushButton("Live")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.live_button)
        layout.addLayout(button_layout)
        self.start_button.setEnabled(False)

        # Connect image clicked signal to slot
        self.image_label.mousePressEvent = self.on_image_clicked

    def on_image_clicked(self, event):
        self.image_clicked.emit(self.name, QPixmap(self.image_path))  # Emit device name along with pixmap

    def setting_button_clicked(self):
        self.setting_clicked.emit(self.name, self.objToFind)  # Emit device name and existing objects

    def update_image(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        pixmap = pixmap.scaled(self.image_label.size(), aspectRatioMode=Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

    def stop_button_clicked(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pausa_label.show()
        yoloScript.change_stop(self.device, True)

    def start_button_clicked(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.pausa_label.hide()
        yoloScript.change_stop(self.device, False)


class DispositivosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dispositivos")
        layout = QVBoxLayout(self)
        self.queue = Queue()
        self.dispositivos_dict = {}
        # Button to add dispositivos
        add_button = QPushButton("Adicionar Dispositivos")
        add_button.clicked.connect(self.open_device_ip_window)
        layout.addWidget(add_button)
        self.reading = False

        # Horizontal layout to list dispositivos adicionados
        dispositivos_layout = QHBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.dispositivos_layout = QHBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        dispositivos_layout.addWidget(self.scroll_area)
        layout.addLayout(dispositivos_layout)

        # Add sample dispositivos
        #self.add_dispositivo("Dispositivo 1","0", ["banana"])
        #self.add_dispositivo("Dispositivo 2")
        #self.add_dispositivo("Dispositivo 3")

    def add_dispositivo(self, name, device, objToFind):
        dispositivo_widget = DispositivoWidget(name, device,objToFind)
        self.dispositivos_dict[device] = dispositivo_widget
        dispositivo_widget.image_clicked.connect(self.show_image_window)  # Connect signal to slot
        dispositivo_widget.setting_clicked.connect(self.open_device_config_dialog)  # Connect setting signal
        self.dispositivos_layout.addWidget(dispositivo_widget)
        Thread(target=self.runscript_thread, args=(device, objToFind)).start()
        if not self.reading:
            Thread(target=self.readQueue).start()
            self.reading = True


    def runscript_thread(self, device, objToFind):
        yoloScript.addDispositivoToPredict(device, objToFind, self.queue, 10)

    def readQueue(self):
        while True:
            try:
                frames = self.queue.get()
                if frames == -1:
                    self.timer.stop()
                for device, frame in frames.items():
                    self.dispositivos_dict[device].update_image(frame)
            except self.queue.empty:
                print("Queue is empty.")
            time.sleep(0.5)
    def show_image_window(self, name, pixmap):
        print("Device Name:", name)  # Print the device name
        image_window = ImageWindow(pixmap)
        image_window.show()

    def open_device_ip_window(self):
        device_ip_window = ConfigurarDispositivo()
        device_ip_window.done_clicked.connect(self.handle_done_clicked)  # Connect Done signal to slot
        device_ip_window.exec_()

    def handle_done_clicked(self, name, device, selected_items):
        for widget in self.findChildren(DispositivoWidget):
            if widget.name == name:
                print(f"Updating device '{name}' with selected items: {selected_items}")
                widget.objToFind = selected_items
                return

        print(f"Adding new device '{name}' with selected items: {selected_items}")
        if device.isdigit():
            device = int(device)
        self.add_dispositivo(name, device, selected_items)

    def open_device_config_dialog(self, name, device,objToFind):
        device_config_dialog = ConfigurarDispositivo(name, device,objToFind)
        device_config_dialog.done_clicked.connect(self.handle_done_clicked)
        device_config_dialog.exec_()


class AlertasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alertas")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("MainWindow for Alertas"))


class ImageWindow(QMainWindow):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Image Window")
        self.setGeometry(0, 0, 800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)

global_devices = []
class ConfigurarDispositivo(QDialog):
    done_clicked = QtCore.pyqtSignal(str, str, list)
    def __init__(self, name="", objToFind=None):
        super().__init__()
        self.class_names = yoloScript.get_classes()
        self.setWindowTitle("Configurar Dispositivo")
        layout = QVBoxLayout()
        self.nomeLabel = QLabel("Insira o nome:")
        self.nomeLineEdit = QLineEdit()
        self.dispositivo_label = QLabel("Escolha o dispositivo:")
        self.device_combo_box = QComboBox()
        if len(global_devices) > 0:
            self.listar_dispositivos(global_devices)
        self.label_procura_dispositivo = QLabel("A procurar por dispositivos...")
        self.atualizar_dispositivos_button = QPushButton("Atualizar Dispositivos")
        self.checkBox_IP = QCheckBox("Inserir camera por IP")
        self.checkBox_IP.stateChanged.connect(self.toggle_visibility)
        self.atualizar_dispositivos_button.clicked.connect(self.atualizar_dispositivos)
        # Line edit for entering device IP
        self.ipLabeb = QLabel("Introduza IP do dispositivo")
        self.ip_line_edit = QLineEdit()
        self.ip_line_edit.setText(name)
        self.testButton = QPushButton("Test connection")

        # List widget for selecting objects to detect
        self.objetosLabeb = QLabel("Selecione objetos a detetar")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_list)
        self.availableObjects = QListWidget()
        self.availableObjects.addItems(sorted(self.class_names))
        self.selected_items = []
        self.selected_objects_label = QLabel("Selected Objects: ")
        if objToFind:
            for item in objToFind:
                items = self.availableObjects.findItems(item, Qt.MatchExactly)
                for i in items:
                    i.setSelected(True)
            self.selected_items = objToFind
            self.selected_objects_label.setText("Selected Objects: " + ", ".join(self.selected_items))

        # Button to add objects
        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(self.on_done_clicked)

        # Add widgets to layout
        layout.addWidget(self.nomeLabel)
        layout.addWidget(self.nomeLineEdit)
        layout.addWidget(self.dispositivo_label)
        layout.addWidget(self.device_combo_box)
        layout.addWidget(self.label_procura_dispositivo)
        layout.addWidget(self.atualizar_dispositivos_button)
        layout.addWidget(self.ipLabeb)
        layout.addWidget(self.ip_line_edit)
        layout.addWidget(self.testButton)
        layout.addWidget(self.checkBox_IP)
        layout.addWidget(self.objetosLabeb)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.availableObjects)
        layout.addWidget(self.selected_objects_label)
        layout.addWidget(self.doneButton)
        self.ipLabeb.hide()
        self.ip_line_edit.hide()
        self.testButton.hide()
        self.label_procura_dispositivo.hide()

        self.setLayout(layout)

        # Connect itemClicked signal to update label
        self.availableObjects.itemClicked.connect(self.update_selected_objects_label)

    def filter_list(self):
        search_text = self.search_bar.text().lower()
        filtered_items = [item for item in self.class_names if search_text in item.lower()]
        self.availableObjects.clear()
        self.availableObjects.addItems(sorted(filtered_items))

    def update_selected_objects_label(self):
        selected_item = self.availableObjects.currentItem()
        if selected_item:
            selected_text = selected_item.text()
            if selected_text in self.selected_items:
                self.selected_items.remove(selected_text)  # Remove the item if already selected
            else:
                self.selected_items.append(selected_text)  # Add the item if not already selected
            # Update the label to show all selected items
            self.selected_objects_label.setText("Selected Objects: " + ", ".join(self.selected_items))

    def on_done_clicked(self):
        name = self.nomeLineEdit.text()
        if self.checkBox_IP.isChecked():
            device = self.ip_line_edit.text()
        else:
            device = self.device_combo_box.itemData(self.device_combo_box.currentIndex())
            device = str(device)
        selected_items = self.selected_items
        self.done_clicked.emit(name, device, selected_items)  # Emit signal with device name and selected items
        self.accept()  # fechar janela

    def atualizar_dispositivos(self):
        Thread(target=self.listar_Thread).start()
    def listar_Thread(self):
        global global_devices
        self.device_combo_box.clear()
        self.label_procura_dispositivo.show()
        self.atualizar_dispositivos_button.setEnabled(False)
        global_devices = yoloScript.list_available_cameras()
        self.listar_dispositivos(global_devices)
        self.label_procura_dispositivo.hide()
        self.atualizar_dispositivos_button.setEnabled(True)
    def listar_dispositivos(self, devices):
        if len(devices) > 0:
            for device in devices:
                self.device_combo_box.addItem(f"Dispositivo {device}", device)
            self.device_combo_box.setCurrentIndex(0)
    def toggle_visibility(self, state):
        if state == Qt.Checked:
            self.ipLabeb.show()
            self.ip_line_edit.show()
            self.testButton.show()
            self.dispositivo_label.hide()
            self.device_combo_box.hide()
            self.atualizar_dispositivos_button.hide()

        else:
            self.ipLabeb.hide()
            self.ip_line_edit.hide()
            self.testButton.hide()
            self.dispositivo_label.show()
            self.device_combo_box.show()
            self.atualizar_dispositivos_button.show()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Object Detection")
        self.setGeometry(500, 100, 1280, 720)
        self.setGeometry(500, 100, 1280, 720)

        # Create layout for main window
        main_layout = QVBoxLayout(self)

        # Create horizontal layout for buttons
        button_layout = QHBoxLayout()

        # Create buttons for "Dispositivos" and "Alertas"
        dispositivos_button = QPushButton("Dispositivos")
        dispositivos_button.clicked.connect(self.show_dispositivos)
        button_layout.addWidget(dispositivos_button)

        alertas_button = QPushButton("Alertas")
        alertas_button.clicked.connect(self.show_alertas)
        button_layout.addWidget(alertas_button)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        # Create stacked layout to hold different windows
        self.stacked_layout = QStackedLayout()

        # Create instances of DispositivosWindow and AlertasWindow
        self.dispositivos_window = DispositivosWindow()
        self.alertas_window = AlertasWindow()

        # Add windows to stacked layout
        self.stacked_layout.addWidget(self.dispositivos_window)
        self.stacked_layout.addWidget(self.alertas_window)

        # Add stacked layout to main layout
        main_layout.addLayout(self.stacked_layout)

    def show_dispositivos(self):
        self.stacked_layout.setCurrentIndex(0)

    def show_alertas(self):
        self.stacked_layout.setCurrentIndex(1)


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
