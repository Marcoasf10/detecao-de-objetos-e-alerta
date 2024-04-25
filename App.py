from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedLayout, \
    QListWidget, QScrollArea, QMainWindow, QDialog, QLineEdit, QAbstractItemView
from PyQt5 import QtCore
import testeCv


class DispositivoWidget(QWidget):
    image_clicked = QtCore.pyqtSignal(str, QPixmap)  # Define a signal with device name
    setting_clicked = QtCore.pyqtSignal(str)  # Define a signal for setting button clicked

    def __init__(self, name, image_path):
        super().__init__()
        self.name = name
        self.image_path = image_path  # Store the image path
        layout = QVBoxLayout(self)

        # Create a horizontal layout for the label and setting button
        top_layout = QHBoxLayout()
        self.label = QLabel(name)
        top_layout.addWidget(self.label)

        # Setting button
        self.setting_button = QPushButton("Settings")
        self.setting_button.clicked.connect(self.setting_button_clicked)
        top_layout.addWidget(self.setting_button)

        layout.addLayout(top_layout)

        self.image_label = QLabel()
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaledToWidth(700)
        self.image_label.setPixmap(pixmap)
        layout.addWidget(self.image_label)

        # Buttons for start, stop, and live
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.live_button = QPushButton("Live")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.live_button)
        layout.addLayout(button_layout)

        # Connect image clicked signal to slot
        self.image_label.mousePressEvent = self.on_image_clicked

    def on_image_clicked(self, event):
        self.image_clicked.emit(self.name, QPixmap(self.image_path))  # Emit device name along with pixmap

    def setting_button_clicked(self):
        self.setting_clicked.emit(self.name)  # Emit device name when setting button is clicked


class DispositivosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dispositivos")
        layout = QVBoxLayout(self)

        # Button to add dispositivos
        add_button = QPushButton("Adicionar Dispositivos")
        add_button.clicked.connect(self.open_device_ip_window)
        layout.addWidget(add_button)

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
        self.add_dispositivo("Dispositivo 1", "/Users/marcoferreira/Projeto_Informatico/detecao-de-objetos-e-alerta/frames/track/image0.jpg")
        self.add_dispositivo("Dispositivo 2", "/Users/marcoferreira/Projeto_Informatico/detecao-de-objetos-e-alerta/frames/track/image0.jpg")
        self.add_dispositivo("Dispositivo 3", "/Users/marcoferreira/Projeto_Informatico/detecao-de-objetos-e-alerta/frames/track/image0.jpg")

    def add_dispositivo(self, name, image_path):
        dispositivo_widget = DispositivoWidget(name, image_path)
        dispositivo_widget.image_clicked.connect(self.show_image_window)  # Connect signal to slot
        self.dispositivos_layout.addWidget(dispositivo_widget)

    def show_image_window(self, name, pixmap):
        print("Device Name:", name)  # Print the device name
        image_window = ImageWindow(pixmap)
        image_window.show()

    def open_device_ip_window(self):
        device_ip_window = ConfigurarDispositivo(self)
        device_ip_window.exec_()


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


class ConfigurarDispositivo(QDialog):
    def __init__(self,  dispositivos_window):
        super().__init__()
        self.class_names = testeCv.get_classes()
        self.setWindowTitle("Configurar Dispositivo")
        layout = QVBoxLayout()
        self.dispositivos_window = dispositivos_window
        # Line edit for entering device IP
        self.ipLabeb = QLabel("Introduza IP do dispositivo")
        self.ip_line_edit = QLineEdit()
        self.testButton = QPushButton("Test connection")

        # List widget for selecting objects to detect
        self.objetosLabeb = QLabel("Selecione objetos a detetar")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_list)
        self.availableObjects = QListWidget()
        self.availableObjects.addItems(sorted(self.class_names))
        self.selected_items = []

        # Label to display selected objects
        self.selected_objects_label = QLabel("Selected Objects: ")

        # Button to add objects
        self.add_button = QPushButton("Add Objects")
        self.add_button.clicked.connect(self.add_objects)
        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(self.adicionarDispositivo)

        # Add widgets to layout
        layout.addWidget(self.ipLabeb)
        layout.addWidget(self.ip_line_edit)
        layout.addWidget(self.testButton)
        layout.addWidget(self.objetosLabeb)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.availableObjects)
        layout.addWidget(self.selected_objects_label)
        layout.addWidget(self.add_button)
        layout.addWidget(self.doneButton)

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

    def add_objects(self):
        for item in self.selected_items:
            print("Objects Selected:", item)

    def adicionarDispositivo(self):
        self.dispositivos_window.add_dispositivo(self.ip_line_edit.text(), "frames/noCamera.jpg")
        self.close()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Object Detection")
        self.setGeometry(500, 100, 600, 400)

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
