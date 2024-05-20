import time
from multiprocessing import Queue
from threading import Thread

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, QSize, QRect, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedLayout, \
    QListWidget, QScrollArea, QMainWindow, QDialog, QLineEdit, QComboBox, QCheckBox, QFrame, QProgressBar, \
    QSizePolicy, QScrollBar, QAbstractItemView, QStackedWidget, QGridLayout, QMessageBox, QListWidgetItem
from PyQt5 import QtCore
import yoloScript
import multiprocessing
import pickle

all_dispositivos_widget = []
global_devices = []

class HorizontalLayout(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("""
                                   QScrollArea {
                                       background-color: #FFFFFF; /* Set background color to white */
                                       border-radius: 10px; /* Set border radius to 10px for rounded corners */
                                   }
                               """)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        self.scroll_widget = QWidget()
        self.dispositivos_layout = QHBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, widget):
        widget.setMaximumSize(400, 400)
        self.dispositivos_layout.addWidget(widget, alignment=Qt.AlignLeft)

    def removeWidget(self, widget):
        self.dispositivos_layout.removeWidget(widget)


class MosaicoLayout(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        self.num_devices = 0
    def addWidget(self, widget):
        widget.setMaximumSize(400, 400)
        row = self.num_devices // 3
        col = self.num_devices % 3
        self.layout.addWidget(widget, row, col)
        self.num_devices += 1

    def removeWidget(self, widget):
        self.layout.removeWidget(widget)
        if self.num_devices > 0:
            self.num_devices -= 1


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Spash Screen Example')
        self.setFixedSize(1100, 500)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.counter = 0
        self.n = 50

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.loading)
        self.timer.start(30)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.frame = QFrame()
        layout.addWidget(self.frame)

        self.labelTitle = QLabel(self.frame)
        self.labelTitle.setObjectName('LabelTitle')

        # center labels
        self.labelTitle.resize(self.width() - 10, 150)
        self.labelTitle.move(0, 40)  # x, y
        self.labelTitle.setText('Splash Screen')
        self.labelTitle.setAlignment(Qt.AlignCenter)

        self.labelDescription = QLabel(self.frame)
        self.labelDescription.resize(self.width() - 10, 50)
        self.labelDescription.move(0, self.labelTitle.height())
        self.labelDescription.setObjectName('LabelDesc')
        self.labelDescription.setText('<strong>Working on Task #1</strong>')
        self.labelDescription.setAlignment(Qt.AlignCenter)

        self.progressBar = QProgressBar(self.frame)
        self.progressBar.resize(self.width() - 200 - 10, 50)
        self.progressBar.move(100, self.labelDescription.y() + 130)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setFormat('%p%')
        self.progressBar.setTextVisible(True)
        self.progressBar.setRange(0, self.n)
        self.progressBar.setValue(20)

        self.labelLoading = QLabel(self.frame)
        self.labelLoading.resize(self.width() - 10, 50)
        self.labelLoading.move(0, self.progressBar.y() + 70)
        self.labelLoading.setObjectName('LabelLoading')
        self.labelLoading.setAlignment(Qt.AlignCenter)
        self.labelLoading.setText('loading...')

    def loading(self):
        self.progressBar.setValue(self.counter)

        if self.counter == int(self.n * 0.3):
            self.labelDescription.setText('<strong>Working on Task #2</strong>')
        elif self.counter == int(self.n * 0.6):
            self.labelDescription.setText('<strong>Working on Task #3</strong>')
        elif self.counter >= self.n:
            self.timer.stop()
            self.close()

            time.sleep(1)

            self.myApp = MainWindow()
            self.myApp.show()

        self.counter += 1

class LightButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 10px;
                font-size: 16px;
                padding: 10px;
                color: #FFFFFF;
                background-color: #5B5B5B;
            }
        """)

class WidgetButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 10px;
                font-size: 16px;
                padding: 10px;
                color: #FFFFFF;
                background-color: #D9D9D9;
            }
        """)
class WidgetPressedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 10px;
                font-size: 16px;
                padding: 10px;
                color: #FFFFFF;
                background-color: #5B5B5B;
            }
        """)


class DarkButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 10px;
                font-size: 16px;
                padding: 10px;
                color: #FFFFFF;
                background-color: #292929;
            }
        """)


class DispositivoWidget(QWidget):
    image_clicked = QtCore.pyqtSignal(str, QPixmap)  # Define a signal with device name

    def __init__(self, name, device, objToFind, lista_alertas ,dispositovo_window):
        super().__init__()
        self.image_window = None
        self.dispositivos_window = dispositovo_window
        self.pause = False
        self.name = name
        self.image_path = "frames/noCamera.jpg"  # Store the image path
        self.objToFind = objToFind
        layout = QVBoxLayout(self)
        self.device = device
        self.label = QLabel(name)
        self.label.setStyleSheet("font-size: 25px; color: #FFFFFF")

        # Setting button
        self.settings_button = WidgetButton()
        self.settings_button.setIcon(QIcon("icons/settings.png"))
        self.settings_button.setIconSize(QSize(40, 40))
        self.settings_button.setFixedSize(50, 50)
        self.settings_button.clicked.connect(self.setting_button_clicked)

        self.expand_button = WidgetButton()
        self.expand_button.setIcon(QIcon("icons/expand.png"))
        self.expand_button.setIconSize(QSize(35, 35))
        self.expand_button.setFixedSize(50, 50)
        self.expand_button.clicked.connect(self.expand_button_clicked)

        self.remove_button = WidgetButton()
        self.remove_button.setIcon(QIcon("icons/remove.png"))
        self.remove_button.setIconSize(QSize(35, 35))
        self.remove_button.setFixedSize(50, 50)
        self.remove_button.clicked.connect(self.remove_button_clicked)

        layout_imagem = QHBoxLayout()

        self.iconPause = QIcon("icons/pause_circle.png")

        self.image_label = QLabel()
        pixmap = QPixmap(self.image_path)
        pixmap = pixmap.scaledToWidth(325)
        self.image_label.setPixmap(pixmap)
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.settings_button, alignment=Qt.AlignTop)
        settings_layout.addWidget(self.expand_button, alignment=Qt.AlignTop)
        settings_layout.addWidget(self.remove_button, alignment=Qt.AlignTop)
        settings_layout.addStretch()
        layout_imagem.addWidget(self.image_label)
        layout_imagem.addLayout(settings_layout)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.label)
        layout.addLayout(top_layout)
        layout.addLayout(layout_imagem)

        button_layout = QHBoxLayout()
        self.start_button = WidgetPressedButton()
        self.start_button.setIcon(QIcon("icons/play.png"))
        self.start_button.setIconSize(QSize(30, 30))
        self.start_button.setFixedSize(50, 50)
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button = WidgetButton()
        self.stop_button.setIcon(QIcon("icons/pause.png"))
        self.stop_button.setIconSize(QSize(35, 35))
        self.stop_button.setFixedSize(50, 50)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.live_button = WidgetButton()
        self.live_button.setIcon(QIcon("icons/live.png"))
        self.live_button.clicked.connect(self.live_button_clicked)
        self.live_button.setIconSize(QSize(35, 35))
        self.live_button.setFixedSize(50, 50)
        self.combo_delay_label = QLabel("Delay:")
        self.combo_delay_label.setStyleSheet("font-size: 15px; color: #FFFFFF")
        self.combo_delay = QComboBox()
        combo_style = """
            QComboBox {
                font-size: 15px;
                background-color: #D9D9D9;
                color: #000000;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QComboBox::drop-down {
                border: 0px;
                background-color: #D9D9D9;
                margin-right: 20px;
            }
            QComboBox::down-arrow {
                image: url(icons/dropdown.png);
                width: 20px;
                height: 20px;
            }
            QComboBox::item {
                background-color: #5B5B5B;
                color: #FFFFFF;
            }
            QComboBox::item:!selected {
                background-color: #D9D9D9;
                color: #000000;
            }   
        """
        self.combo_delay.setStyleSheet(combo_style)
        self.populate_combo_delay()
        self.combo_delay.currentIndexChanged.connect(self.change_delay)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.live_button)
        button_layout.addWidget(self.combo_delay_label)
        button_layout.addWidget(self.combo_delay)
        layout.addLayout(button_layout)
        self.start_button_clicked()
        self.lista_alertas = lista_alertas

        # Connect image clicked signal to slot
        #self.image_label.mousePressEvent = self.on_image_clicked

    def sobrepor_icon_centralizado(self, frame, icon):
        frame_height = frame.height()
        frame_width = frame.width()
        icon_height = icon.actualSize(QSize(frame_width, frame_height)).height()
        icon_width = icon.actualSize(QSize(frame_width, frame_height)).width()

        x_offset = (frame_width - icon_width) // 2
        y_offset = (frame_height - icon_height) // 2

        frame_with_icon = frame.copy()
        painter = QPainter(frame_with_icon)
        icon.paint(painter, QRect(x_offset, y_offset, icon_width, icon_height))
        painter.end()

        return frame_with_icon

    def expand_button_clicked(self):
        self.image_window = ImageWindow(self.image_label.pixmap().scaledToWidth(800), self)
        self.image_window.show()

    def setting_button_clicked(self):
        delay = self.combo_delay.itemData(self.combo_delay.currentIndex())
        print("delay", delay)
        self.config_dialog = ConfigurarDispositivo(self.name, self.device, self.objToFind, alertas_dict=self.lista_alertas , time_frame=delay)
        self.config_dialog.done_clicked.connect(self.handle_done_clicked)
        self.config_dialog.exec_()

    def handle_done_clicked(self, name, device, selected_items, lista_alertas):
        print(f"Updating device '{device}' with selected items: {selected_items}")
        self.name = name
        self.label.setText(name)
        self.objToFind = selected_items
        if device.isdigit():
            deviceInt = int(device)
        self.lista_alertas = lista_alertas
        yoloScript.update_obj_to_find(deviceInt, self.objToFind)

    def update_image(self, frame):
        if self.pause:
            return
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        pixmap = pixmap.scaled(self.image_label.size(), aspectRatioMode=Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)
        if self.image_window is not None:
            self.image_window.update_image(frame)

    def start_button_clicked(self):
        self.pause = False
        yoloScript.change_stop(self.device, False)
        self.change_delay()
        self.start_button.setStyleSheet(self.start_button.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.stop_button.setStyleSheet(self.stop_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.live_button.setStyleSheet(self.live_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")

    def stop_button_clicked(self):
        yoloScript.change_stop(self.device, True)
        self.start_button.setStyleSheet(self.start_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.stop_button.setStyleSheet(self.stop_button.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.live_button.setStyleSheet(self.live_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        image_stopped = self.sobrepor_icon_centralizado(self.image_label.pixmap().toImage(), self.iconPause)
        image_format = QImage.Format_ARGB32
        converted_image = image_stopped.convertToFormat(image_format)
        buffer = converted_image.bits()
        buffer.setsize(converted_image.byteCount())
        image_np = np.array(buffer).reshape(converted_image.height(), converted_image.width(), 4)
        self.update_image(image_np)
        self.pause = True

    def live_button_clicked(self):
        self.pause = False
        yoloScript.change_stop(self.device, False)
        yoloScript.change_delay(self.device, 0)
        self.start_button.setStyleSheet(self.start_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.stop_button.setStyleSheet(self.stop_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.live_button.setStyleSheet(self.live_button.styleSheet() + "QPushButton{background-color: #5B5B5B}")


    def populate_combo_delay(self):
        self.combo_delay.clear()
        self.combo_delay.addItem("1 segundo", 1)
        self.combo_delay.addItem("5 segundos", 5)
        self.combo_delay.addItem("10 segundos", 10)
        self.combo_delay.addItem("30 segundos", 30)
        self.combo_delay.addItem("1 minuto", 60)
        self.combo_delay.addItem("5 minutos", 300)
        self.combo_delay.addItem("10 minutos", 600)
        self.combo_delay.addItem("30 minutos", 1800)
        self.combo_delay.addItem("1 hora", 3600)
        self.combo_delay.addItem("1h 30m", 5400)
        self.combo_delay.setCurrentIndex(2)

    def change_delay(self):
        delay = self.combo_delay.itemData(self.combo_delay.currentIndex())
        print(delay)
        yoloScript.change_delay(self.device, delay)

    def remove_button_clicked(self):
        yoloScript.remove_device(self.device)
        self.dispositivos_window.remove_device(self.device)
        all_dispositivos_widget.remove(self)
        if self.image_window is not None:
            self.image_window.hide()
            self.image_window.close()
        self.deleteLater()
    def handle_close_image_window(self):
        self.image_window = None
class StyledScrollBar(QScrollBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QScrollBar:vertical {
                background-color: #FFFFFF; /* Set background color to white for vertical scrollbar */
                width: 20px; /* Set width of scrollbar */
                border-radius: 10px; /* Set border radius for rounded corners */
            }

            QScrollBar:horizontal {
                background-color: #FFFFFF; /* Set background color to white for horizontal scrollbar */
                height: 20px; /* Set height of scrollbar */
                border-radius: 10px; /* Set border radius for rounded corners */
            }
        """)


class DispositivosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dispositivos")
        self.stacked_layout = QStackedLayout()
        self.horizontal_layout = HorizontalLayout()
        self.mosaico_layout = MosaicoLayout()
        self.stacked_layout.addWidget(self.horizontal_layout)
        self.stacked_layout.addWidget(self.mosaico_layout)
        layout = QVBoxLayout()

        self.queue = Queue()
        self.dispositivos_dict = {}

        self.add_button = LightButton("+ Adicionar Dispositivos")
        self.add_button.clicked.connect(self.open_device_ip_window)

        self.mosaicoButton = LightButton()
        self.mosaicoButton.setIcon(QIcon("icons/mosaico_2.png"))
        self.mosaicoButton.clicked.connect(self.layout_mosaico)

        self.horizontalbutton = LightButton()
        self.horizontalbutton.setIcon(QIcon("icons/mosaico.png"))
        self.horizontalbutton.clicked.connect(self.layout_horizontal)
        self.mosaicoButton.setIconSize(QSize(35, 35))
        self.mosaicoButton.setFixedSize(50, 50)
        self.horizontalbutton.setIconSize(QSize(40, 40))
        self.horizontalbutton.setFixedSize(50, 50)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addStretch(1)

        buttons_layout.addWidget(self.mosaicoButton)
        buttons_layout.addWidget(self.horizontalbutton)

        buttons_layout.setContentsMargins(0, 40, 0, 0)

        top_layout = QVBoxLayout()
        top_layout.addLayout(buttons_layout)

        layout.addLayout(top_layout)

        self.stacked_layout.setCurrentIndex(0)
        layout.addLayout(self.stacked_layout)
        self.setLayout(layout)
        self.image_window = None
        self.reading = False
        self.horizontalbutton.setEnabled(False)
        self.mosaicoButton.setEnabled(True)
        self.horizontalbutton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #292929}")
        self.mosaicoButton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #5B5B5B}")
    def layout_mosaico(self):
        global all_dispositivos_widget
        self.mosaicoButton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #292929}")
        self.horizontalbutton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.horizontalbutton.setEnabled(True)
        self.mosaicoButton.setEnabled(False)
        self.stacked_layout.setCurrentIndex(1)
        for widget in all_dispositivos_widget:
            self.horizontal_layout.removeWidget(widget)
            self.mosaico_layout.addWidget(widget)


    def layout_horizontal(self):
        self.horizontalbutton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #292929}")
        self.mosaicoButton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.horizontalbutton.setEnabled(False)
        self.mosaicoButton.setEnabled(True)
        self.stacked_layout.setCurrentIndex(0)
        for widget in all_dispositivos_widget:
            self.mosaico_layout.removeWidget(widget)
            self.horizontal_layout.addWidget(widget)

    def add_dispositivo(self, name, device, objToFind, lista_alertas):
        global all_dispositivos_widget
        dispositivo_widget = DispositivoWidget(name, device, objToFind, lista_alertas, self)
        all_dispositivos_widget.append(dispositivo_widget)
        self.dispositivos_dict[device] = dispositivo_widget
        if self.stacked_layout.currentIndex() == 1:
            self.mosaico_layout.addWidget(dispositivo_widget)
        if self.stacked_layout.currentIndex() == 0:
            self.horizontal_layout.addWidget(dispositivo_widget)
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
                    if self.image_window is not None:
                        self.image_window.update_image(frame)
            except self.queue.empty:
                print("Queue is empty.")
            time.sleep(0.5)

    def open_device_ip_window(self):
        self.device_ip_window = ConfigurarDispositivo(dispositivos_dict=self.dispositivos_dict)
        self.device_ip_window.done_clicked.connect(self.handle_done_clicked)
        self.device_ip_window.exec_()

    def handle_done_clicked(self, name, device, selected_items, lista_alertas):
        if device in self.dispositivos_dict.keys():
            QMessageBox.warning(self, "Erro", "Dispositivo já existe na lista de dispositivos.")
            return
        print(f"Adding new device '{name}' with selected items: {selected_items}")
        if device.isdigit():
            device = int(device)
        self.add_dispositivo(name, device, selected_items, lista_alertas)

    def remove_device(self, device):
        del self.dispositivos_dict[device]


class AlertaWidget(QWidget):
    def __init__(self, device, classe, descricao, frame):
        super().__init__()
        self.item_layout = QHBoxLayout()

        texto_esquerda = QLabel(descricao)
        texto_esquerda.setStyleSheet("font-size: 16px; color: #FFFFFF")

        self.item_layout.addWidget(texto_esquerda)

        imagem_direita = QLabel()
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        pixmap = pixmap.scaledToWidth(100)
        imagem_direita.setPixmap(pixmap)
        self.item_layout.addWidget(imagem_direita, alignment=Qt.AlignRight)
        self.device = device
        self.classe = classe
        self.setLayout(self.item_layout)

class AlertasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alertas")
        self.setGeometry(100, 100, 600, 400)  # Definindo a geometria da janela
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.alertas_widgets = []

    def carregar_alertas(self):
        alertas = []
        for widget in self.alertas_widgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.alertas_widgets = []
        try:
            with open("alertas.bin", 'rb') as file:
                while True:
                    alerta = pickle.load(file)
                    alertas.append(alerta)
        except EOFError:
            pass
        for alerta in alertas:
            alerta_widget = AlertaWidget(alerta.get_device(), alerta.get_classe(), alerta.get_descricao(), alerta.get_photo())
            self.alertas_widgets.append(alerta_widget)
            self.layout.addWidget(alerta_widget)




class ImageWindow(QMainWindow):
    def __init__(self, pixmap, parent=None):
        super().__init__()
        self.dispositivo_widget = parent
        self.setWindowTitle("Image Window")
        self.setGeometry(0, 0, 800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

    def update_image(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        pixmap = pixmap.scaled(self.image_label.size(), aspectRatioMode=Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.dispositivo_widget.handle_close_image_window()
        super().closeEvent(event)

class ListarThread(QThread):
    finished = pyqtSignal(list, bool)
    def run(self):
        global global_devices
        global_devices = yoloScript.list_available_cameras()
        self.finished.emit(global_devices, True)


class CustomWidget(QWidget):
    def __init__(self, text, times, tempo = None):
        super().__init__()
        layout = QHBoxLayout()
        self.label = QLabel(text)
        self.combo_box = QComboBox()
        self.times = times
        for time in self.times:
            if time < 60:
                self.combo_box.addItem(str(time))
            else:
                break

        self.combo_box_time = QComboBox()
        self.combo_box_time.addItem("segundos")
        self.combo_box_time.addItem("minutos")
        self.combo_box_time.addItem("horas")

        layout.addWidget(self.label)
        layout.addWidget(self.combo_box)
        layout.addWidget(self.combo_box_time)
        self.setLayout(layout)
        if tempo is not None:
            self.combo_box.setCurrentText(tempo)
        self.combo_box_time.currentIndexChanged.connect(self.update_time_unit)

        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #000000;
            }
            QComboBox {
                font-size: 14px;
                background-color: #D9D9D9;
                color: #000000;
                border: none;
                border-radius: 10px;
                max-height: 20px;
            }
            QComboBox::drop-down {
                border: 0px;
                background-color: #D9D9D9;
                margin-right: 10px;
                min-height: 10px;
            }
            QComboBox::down-arrow {
                image: url(icons/dropdown.png);
                width: 11px;
                height: 11px;
            }
            QComboBox::item {
                background-color: #5B5B5B;
                color: #FFFFFF;
            }
            QComboBox::item:!selected {
                background-color: #D9D9D9;
                color: #000000;
            }
        """)

    def update_time_unit(self, index):
        unit = self.combo_box_time.itemText(index)
        times = self.change_times(self.times, unit)
        self.update_combo_box(times, unit)

    def change_times(self, times, unit):
        if unit == "segundos":
            return times
        elif unit == "minutos":
            return [time / 60 for time in times]
        elif unit == "horas":
            return [time / 3600 for time in times]

    def update_combo_box(self, times, unit):
        self.combo_box.clear()
        for time in times:
            if time % 1 == 0:
                if unit == "segundos":
                    if time < 60:
                        self.combo_box.addItem(str(int(time)))
                    else:
                        break
                elif unit == "minutos":
                    if time < 60:
                        self.combo_box.addItem(str(int(time)))
                    else:
                        break
                elif unit == "horas":
                    self.combo_box.addItem(str(int(time)))
    def get_classe(self):
        return self.label.text()

    def get_time(self):
        if self.combo_box_time.currentText() == "segundos":
            return self.combo_box.currentText()
        if self.combo_box_time.currentText() == "minutos":
            return self.combo_box.currentText() * 60
        if self.combo_box_time.currentText() == "horas":
            return self.combo_box.currentText() * 3600


class ConfigurarDispositivo(QDialog):
    done_clicked = QtCore.pyqtSignal(str, str, list, dict)

    def __init__(self, name="", device="", objToFind=None, dispositivos_dict = {}, alertas_dict = {},time_frame=10):
        if objToFind is None:
            objToFind = []
        super().__init__()
        print("time_frame", time_frame)
        self.setStyleSheet("""
                       ConfigurarDispositivo {
                           background-color: #5B5B5B;
                       }
                       QLineEdit {
                           background-color: #D9D9D9;
                           border: none;
                           font-size: 16px;
                           padding: 5px;
                           color: #000000;
                           margin: 0px;
                           border-radius: 10px;
                       }
                       QLabel {
                            font-size: 16px;
                            color: #FFFFFF;
                       }
                       QComboBox {
                            font-size: 15px;
                            background-color: #D9D9D9;
                            color: #000000;
                            border: none;
                            border-radius: 10px;
                            padding: 5px;
                        }
                        QComboBox::drop-down {
                            border: 0px;
                            background-color: #D9D9D9;
                            margin-right: 20px;
                        }
                        QComboBox::down-arrow {
                            image: url(icons/dropdown.png);
                            width: 20px;
                            height: 20px;
                        }
                        QComboBox::item {
                            background-color: #5B5B5B;
                            color: #FFFFFF;
                        }
                        QComboBox::item:!selected {
                            background-color: #D9D9D9;
                            color: #000000;
                        }
                        QListWidget {
                            font-size: 14px;
                            border-radius: 10px;
                        }
                        QListWidget::item {
                            height: 20px;
                        }
                        QListView::item:selected{
                            background-color: #D9D9D9;
                            color: #000000;
                        }
                        QMessageBox {
                             background-color: #5B5B5B;
                             color: #000000;
                        }
                        QMessageBox QPushButton {
                            border: none;
                            border-radius: 10px;
                            font-size: 16px;
                            padding: 10px;
                            color: #FFFFFF;
                            background-color: #292929;
                        }
                   """)

        self.class_names = list(set(yoloScript.get_classes()).difference(objToFind))
        self.class_names_selected = objToFind[:]
        self.interval = time_frame
        self.setWindowTitle("Configurar Dispositivo")
        self.objetos_selecionados_labeb = QLabel("Objetos selecionados")
        self.dispositivo_dict = dispositivos_dict
        self.stacked_widget = QStackedWidget()
        self.page1 = QWidget()
        self.page2 = QWidget()
        self.current_page_index = 0
        self.class_alertas = []

        # Configuração das duas páginas
        self.setup_page1(device, name)
        self.setup_page2(alertas_dict)

        # Adicionando as páginas ao QStackedWidget
        self.stacked_widget.addWidget(self.page1)
        self.stacked_widget.addWidget(self.page2)

        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def setup_page1(self, device, name):
        layout = QVBoxLayout(self.page1)
        self.setWindowTitle("Configurar Dispositivo")
        self.nomeLabel = QLabel("Insira o nome:")
        self.nomeLineEdit = QLineEdit()
        self.dispositivo_label = QLabel("Escolha o dispositivo:")
        self.device_combo_box = QComboBox()
        if len(global_devices) > 0:
            self.listar_dispositivos(global_devices)
        self.label_procura_dispositivo = QLabel("A procurar por dispositivos...")
        self.atualizar_dispositivos_button = DarkButton("Atualizar Dispositivos")
        self.checkBox_IP = QCheckBox("Inserir camera por IP")
        self.checkBox_IP.setStyleSheet("font-size: 16px; color: #FFFFFF")
        self.checkBox_IP.stateChanged.connect(self.toggle_visibility)
        self.atualizar_dispositivos_button.clicked.connect(self.atualizar_dispositivos)
        # Line edit for entering device IP
        self.ipLabeb = QLabel("Introduza IP do dispositivo")
        self.ip_line_edit = QLineEdit()
        self.ip_line_edit.setText(name)
        self.testButton = DarkButton("Test connection")

        self.layout_objetos = QHBoxLayout()
        self.layout_selected = QVBoxLayout()
        self.layout_availave = QVBoxLayout()

        self.button_next = LightButton("")
        self.button_next.setIcon(QIcon("icons/arrow_right.png"))
        self.button_next.setIconSize(QSize(50, 50))
        self.button_next.setFixedSize(50, 50)
        self.button_next.clicked.connect(self.next_page)

        # List widget for selecting objects to detect
        self.procurar_objetos_label = QLabel("Selecionar objetos a detetar")
        self.objetosLabeb = QLabel("Objetos disponíveis")
        self.search_bar = QLineEdit()
        self.search_bar_selected = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar_selected.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_list)
        self.search_bar_selected.textChanged.connect(self.filter_list_selected)
        self.availableObjects = QListWidget()
        self.availableObjects.setSelectionMode(QAbstractItemView.MultiSelection)
        self.availableObjects.addItems(sorted(self.class_names))
        self.objectsSelected = QListWidget()
        self.objectsSelected.setSelectionMode(QAbstractItemView.MultiSelection)
        self.objectsSelected.addItems(sorted(self.class_names_selected))
        self.buttonRemove = DarkButton("Remove (-)")
        self.buttonAdd = DarkButton("Add (+)")
        self.buttonAdd.clicked.connect(self.buttonAddf)
        self.buttonRemove.clicked.connect(self.buttonRemovef)

        # Button to add objects
        self.doneButton = DarkButton("Done")
        self.doneButton.clicked.connect(self.on_done_clicked)

        self.layout_selected.addWidget(self.search_bar_selected)
        self.layout_selected.addWidget(self.objetos_selecionados_labeb)
        self.layout_selected.addWidget(self.objectsSelected)
        self.layout_selected.addWidget(self.buttonRemove)
        self.layout_availave.addWidget(self.search_bar)
        self.layout_availave.addWidget(self.objetosLabeb)
        self.layout_availave.addWidget(self.availableObjects)
        self.layout_availave.addWidget(self.buttonAdd)
        self.layout_objetos.addLayout(self.layout_selected)
        self.layout_objetos.addLayout(self.layout_availave)
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
        layout_horizontal = QHBoxLayout()
        layout_vertical = QVBoxLayout()
        layout_vertical.addWidget(self.checkBox_IP)
        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout_vertical.addWidget(spacer_widget)
        layout_vertical.addWidget(self.procurar_objetos_label, alignment=Qt.AlignCenter)
        layout_horizontal.addLayout(layout_vertical)
        layout_horizontal.addWidget(self.button_next, alignment=Qt.AlignRight)
        layout.addLayout(layout_horizontal)
        layout.addLayout(self.layout_objetos)
        layout.addWidget(self.doneButton)
        self.ipLabeb.hide()
        self.ip_line_edit.hide()
        self.testButton.hide()
        self.label_procura_dispositivo.hide()
        if device != "":
            self.nomeLineEdit.setText(name)
            print("device", device)
            if str(device)[:4] == "http" or device == "rtsp":
                self.checkBox_IP.setChecked(True)
                self.ip_line_edit.setText(device)
                self.ip_line_edit.setEnabled(False)
            else:
                self.device_combo_box.setCurrentIndex(self.device_combo_box.findData(int(device)))
                self.device_combo_box.setEnabled(False)
            self.checkBox_IP.setEnabled(False)
            self.atualizar_dispositivos_button.setEnabled(False)
            self.testButton.setEnabled(False)

    def setup_page2(self, alertas_dict):
        layout = QHBoxLayout(self.page2)
        vertical_left_layout = QVBoxLayout()
        self.vertical_right_layout = QVBoxLayout()
        self.button_prev = LightButton("")
        self.button_prev.setIcon(QIcon("icons/arrow_left.png"))
        self.button_prev.setIconSize(QSize(50, 50))
        self.button_prev.setFixedSize(50, 50)
        self.button_prev.clicked.connect(self.previous_page)
        self.objetos_alerta = QListWidget()
        self.objetos_alerta.setMinimumSize(300, 250)
        vertical_left_layout.addWidget(self.button_prev)
        layout.addLayout(vertical_left_layout)
        middle_layout = QVBoxLayout()
        label_alerta = QLabel("Emitir Alertas")
        label_alerta.setStyleSheet("font-size: 30px;")
        self.vertical_right_layout.addWidget(label_alerta, alignment=Qt.AlignTop | Qt.AlignHCenter)
        middle_layout.addWidget(QLabel("Objetos selecionados"), alignment=Qt.AlignCenter)
        middle_layout.addWidget(self.objetos_alerta, alignment=Qt.AlignCenter)
        self.vertical_right_layout.addLayout(middle_layout)
        label = QLabel(
            "Nesta janela pode definir o tempo de inatividade para cada objeto antes que um alerta seja emitido.")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        self.vertical_right_layout.addWidget(label, alignment=Qt.AlignBottom | Qt.AlignHCenter)
        layout.addLayout(self.vertical_right_layout)
        if len(alertas_dict) != 0:
            for classe, tempo in alertas_dict.items():
                time_frames = self.available_times(self.interval)
                custom_widget = CustomWidget(classe, time_frames, tempo)
                list_item = QListWidgetItem(self.objetos_alerta)
                list_item.setSizeHint(custom_widget.sizeHint())
                self.objetos_alerta.setItemWidget(list_item, custom_widget)
                self.class_alertas.append(classe)


    def next_page(self):
        self.current_page_index = 1
        self.stacked_widget.setCurrentIndex(self.current_page_index)
        time_frames = self.available_times(self.interval)
        for classe in sorted(self.class_names_selected):
            if classe not in self.class_alertas:
                custom_widget = CustomWidget(classe, time_frames)
                list_item = QListWidgetItem(self.objetos_alerta)
                list_item.setSizeHint(custom_widget.sizeHint())
                self.objetos_alerta.setItemWidget(list_item, custom_widget)
                self.class_alertas.append(classe)

    def available_times(self, interval):
        max_time = 24 * 3600  # 24 horas em segundos
        available_times = []

        for time in range(0, max_time, interval):
            available_times.append(time)

        return available_times

    def previous_page(self):
        self.current_page_index = 0
        self.stacked_widget.setCurrentIndex(self.current_page_index)

    def filter_list(self):
        search_text = self.search_bar.text().lower()
        self.availableObjects.clear()
        filtered_items = [item for item in self.class_names if search_text in item.lower()]
        self.availableObjects.addItems(sorted(filtered_items))

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

    def filter_list_selected(self):
        search_text = self.search_bar_selected.text().lower()
        self.objectsSelected.clear()
        filtered_items = [item for item in self.class_names_selected if search_text in item.lower()]
        self.objectsSelected.addItems(sorted(filtered_items))

    def on_done_clicked(self):
        name = self.nomeLineEdit.text()
        if self.checkBox_IP.isChecked():
            device = self.ip_line_edit.text()
            if device in self.dispositivo_dict.keys():
                QMessageBox.warning(self, "Erro", "Dispositivo já existe na lista de dispositivos.")
                return
        else:
            device = self.device_combo_box.itemData(self.device_combo_box.currentIndex())
            if device in self.dispositivo_dict.keys():
                QMessageBox.warning(self, "Erro", "Dispositivo já existe na lista de dispositivos.")
                return
            device = str(device)
        print("device", device)
        if device == "" or device == "None":
            QMessageBox.warning(self, "Erro", "Selecione um dispositivo.")
            return
        selected_items = [self.objectsSelected.item(i).text() for i in range(self.objectsSelected.count())]
        tempo_alertas = {}
        for i in range(self.objetos_alerta.count()):
            list_item = self.objetos_alerta.item(i)
            custom_widget = self.objetos_alerta.itemWidget(list_item)
            tempo_alertas[custom_widget.get_classe()] = custom_widget.get_time()
        self.done_clicked.emit(name, device, selected_items, tempo_alertas)
        self.accept()

    def atualizar_dispositivos(self):
        listar_thread = ListarThread(self)
        listar_thread.finished.connect(self.listar_dispositivos)
        listar_thread.start()
        self.device_combo_box.clear()
        self.label_procura_dispositivo.show()
        self.atualizar_dispositivos_button.setEnabled(False)

    def listar_dispositivos(self, devices, has_dispositivos=False):
        if len(devices) > 0:
            for device in devices:
                self.device_combo_box.addItem(f"Dispositivo {device}", device)
            self.device_combo_box.setCurrentIndex(0)
        if(has_dispositivos):
            self.label_procura_dispositivo.hide()
            self.atualizar_dispositivos_button.setEnabled(True)

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
        self.setStyleSheet("""
               MainWindow {
                   background-color: #292929;
               }
               QPushButton {
                   border: none;
                   font-size: 16px;
                   padding: 10px;
                   color: #FFFFFF;
                   margin: 0px;
               }
               #dark_button {
                   background-color: #292929;
               }
               #light_button {
                   background-color: #5B5B5B;
               }
           """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Layout horizontal para os botões, centralizando-os horizontalmente
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignCenter)
        self.button_layout.setSpacing(0)  # Removendo o espaçamento entre os botões

        self.dispositivos_button = QPushButton("Dispositivos")
        self.dispositivos_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dispositivos_button.clicked.connect(self.show_dispositivos)
        self.button_layout.addWidget(self.dispositivos_button)

        self.alertas_button = QPushButton("Alertas")
        self.alertas_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.alertas_button.clicked.connect(self.show_alertas)
        self.button_layout.addWidget(self.alertas_button)

        main_layout.addLayout(self.button_layout)

        self.stacked_layout = QStackedLayout()
        self.dispositivos_window = DispositivosWindow()
        self.alertas_window = AlertasWindow()
        self.stacked_layout.addWidget(self.dispositivos_window)
        self.stacked_layout.addWidget(self.alertas_window)
        main_layout.addLayout(self.stacked_layout)

        # Definindo a página inicial como Dispositivos
        self.show_dispositivos()

    def show_dispositivos(self):
        self.stacked_layout.setCurrentIndex(0)
        self.dispositivos_button.setStyleSheet("background-color: #292929; border: none; font-size: 20px; padding:10px 0")
        self.alertas_button.setStyleSheet("background-color: #5B5B5B; border: none; border-bottom-left-radius:20%; font-size: 20px; padding:10px 0")

    def show_alertas(self):
        self.alertas_window.carregar_alertas()
        self.stacked_layout.setCurrentIndex(1)
        self.dispositivos_button.setStyleSheet("background-color: #5B5B5B; border: none; border-bottom-right-radius:20%; font-size: 20px; padding:10px 0")
        self.alertas_button.setStyleSheet("background-color: #292929; border: none; font-size: 20px; padding:10px 0")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QApplication([])
    window = SplashScreen()
    window.setStyleSheet('''
               #LabelTitle {
                   font-size: 60px;
                   color: #ffffff;
               }

               #LabelDesc {
                   font-size: 30px;
                   color: #ffffff;
               }

               #LabelLoading {
                   font-size: 30px;
                   color: #ffffff;
               }

               QFrame {
                   background-color: #292929;
                   color: #fffff;
                   border-radius: 10px;
               }

               QProgressBar {
                   background-color: #ffffff;
                   color: #000000;
                   border-style: none;
                   border-radius: 10px;
                   text-align: center;
                   font-size: 30px;
               }

               QProgressBar::chunk {
                   border-radius: 10px;
                   background-color: #D9D9D9;
               }
           ''')
    window.show()
    app.exec_()
    print('Closing Window...')
