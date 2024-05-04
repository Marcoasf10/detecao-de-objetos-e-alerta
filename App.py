import time
from multiprocessing import Queue
from threading import Thread

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, QSize, QRect
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedLayout, \
    QListWidget, QScrollArea, QMainWindow, QDialog, QLineEdit, QComboBox, QCheckBox, QFrame, QProgressBar, QSpacerItem, \
    QSizePolicy, QScrollBar, QAbstractItemView
from PyQt5 import QtCore
import yoloScript

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Spash Screen Example')
        self.setFixedSize(1100, 500)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.counter = 0
        self.n = 300  # total instance

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

    def __init__(self, name, device, objToFind):
        super().__init__()
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
        self.expand_button.setIconSize(QSize(40, 40))
        self.expand_button.setFixedSize(50, 50)
        self.expand_button.clicked.connect(self.expand_button_clicked)

        layout_imagem = QHBoxLayout()

        self.iconPause = QIcon("icons/pause_circle.png")

        self.image_label = QLabel()
        pixmap = QPixmap(self.image_path)
        pixmap = pixmap.scaledToWidth(500)
        self.image_label.setPixmap(pixmap)
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self.settings_button, alignment=Qt.AlignTop)
        settings_layout.addWidget(self.expand_button, alignment=Qt.AlignTop)
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
        self.start_button.setIconSize(QSize(40, 40))
        self.start_button.setFixedSize(50, 50)
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button = WidgetButton()
        self.stop_button.setIcon(QIcon("icons/pause.png"))
        self.stop_button.setIconSize(QSize(40, 40))
        self.stop_button.setFixedSize(50, 50)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.live_button = WidgetButton()
        self.live_button.setIcon(QIcon("icons/live.png"))
        self.live_button.clicked.connect(self.live_button_clicked)
        self.live_button.setIconSize(QSize(40, 40))
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
        self.image_clicked.emit(self.name, QPixmap(self.image_path))  # Emit device name along with pixmap

    def setting_button_clicked(self):
        config_dialog = ConfigurarDispositivo(self.name, self.device, self.objToFind)
        config_dialog.exec_()


    def update_image(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        pixmap = pixmap.scaled(self.image_label.size(), aspectRatioMode=Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

    def start_button_clicked(self):
        self.start_button.setStyleSheet(self.start_button.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.stop_button.setStyleSheet(self.stop_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.live_button.setStyleSheet(self.live_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        yoloScript.change_stop(self.device, False)

    def stop_button_clicked(self):
        self.start_button.setStyleSheet(self.start_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.stop_button.setStyleSheet(self.stop_button.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.live_button.setStyleSheet(self.live_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        '''image_stopped = self.sobrepor_icon_centralizado(self.image_label.pixmap().toImage(), self.iconPause)
        self.update_image(image_stopped)'''
        yoloScript.change_stop(self.device, True)

    def live_button_clicked(self):
        self.start_button.setStyleSheet(self.start_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.stop_button.setStyleSheet(self.stop_button.styleSheet() + "QPushButton{background-color: #D9D9D9}")
        self.live_button.setStyleSheet(self.live_button.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        yoloScript.change_stop(self.device, False)
        yoloScript.change_delay(self.device, 0)

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
        layout = QVBoxLayout(self)
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

        layout.addLayout(buttons_layout)

        self.reading = False

        # Horizontal layout to list dispositivos adicionados
        dispositivos_layout = QHBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("""
                    QScrollArea {
                        background-color: #FFFFFF; /* Set background color to white */
                        border-radius: 10px; /* Set border radius to 10px for rounded corners */
                    }
                """)
        self.scroll_area.setVerticalScrollBar(StyledScrollBar())

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        self.scroll_widget = QWidget()
        self.dispositivos_layout = QHBoxLayout(self.scroll_widget)
        self.dispositivos_layout.setAlignment(Qt.AlignLeft)
        self.scroll_area.setWidget(self.scroll_widget)
        dispositivos_layout.addWidget(self.scroll_area)
        dispositivos_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(dispositivos_layout)
        self.layout_horizontal()

    def layout_mosaico(self):
        self.mosaicoButton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #292929}")
        self.horizontalbutton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #5B5B5B}")

    def layout_horizontal(self):
        self.horizontalbutton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #292929}")
        self.mosaicoButton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #5B5B5B}")
    def add_dispositivo(self, name, device, objToFind):
        dispositivo_widget = DispositivoWidget(name, device, objToFind)
        self.dispositivos_dict[device] = dispositivo_widget
        dispositivo_widget.image_clicked.connect(self.show_image_window)  # Connect signal to slot
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
                    print("frame",type(frame))
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
            if widget.device == device:
                print(f"Updating device '{device}' with selected items: {selected_items}")
                self.dispositivos_dict[widget].objToFind = selected_items
                self.dispositivos_dict[widget].name = name
                return

        print(f"Adding new device '{name}' with selected items: {selected_items}")
        if device.isdigit():
            device = int(device)
        self.add_dispositivo(name, device, selected_items)

    def open_device_config_dialog(self, name, device, objToFind):
        device_config_dialog = ConfigurarDispositivo(name, device, objToFind)
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

    def __init__(self, name="", device="", objToFind=None):
        super().__init__()
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
                   """)
        self.class_names = yoloScript.get_classes()
        self.class_names_selected = []
        self.setWindowTitle("Configurar Dispositivo")
        layout = QVBoxLayout()
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

        # List widget for selecting objects to detect
        self.procurar_objetos_label = QLabel("Selecionar objetos a detetar")
        self.objetosLabeb = QLabel("Objetos disponíveis")
        self.objetos_selecionados_labeb = QLabel("Objetos selecionados")
        self.search_bar = QLineEdit()
        self.search_bar_selected = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar_selected.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_list)
        self.search_bar_selected.textChanged.connect(self.filter_list_selected)
        self.availableObjects = QListWidget()
        self.availableObjects.setSelectionMode(QAbstractItemView.MultiSelection)
        self.selectedObects = QListWidget()
        self.availableObjects.addItems(sorted(self.class_names))
        self.objectsSelected = QListWidget()
        self.objectsSelected.setSelectionMode(QAbstractItemView.MultiSelection)
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
        layout.addWidget(self.checkBox_IP)
        layout.addWidget(self.procurar_objetos_label, alignment=Qt.AlignCenter)
        layout.addLayout(self.layout_objetos)
        layout.addWidget(self.doneButton)
        self.ipLabeb.hide()
        self.ip_line_edit.hide()
        self.testButton.hide()
        self.label_procura_dispositivo.hide()
        if device != "":
            self.nomeLineEdit.setText(name)
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
        self.setLayout(layout)

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
        else:
            device = self.device_combo_box.itemData(self.device_combo_box.currentIndex())
            device = str(device)
        selected_items = self.class_names_selected
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
        self.stacked_layout.setCurrentIndex(1)
        self.dispositivos_button.setStyleSheet("background-color: #5B5B5B; border: none; border-bottom-right-radius:20%; font-size: 20px; padding:10px 0")
        self.alertas_button.setStyleSheet("background-color: #292929; border: none; font-size: 20px; padding:10px 0")

if __name__ == '__main__':
    app = QApplication([])
    window = SplashScreen()
    window.setStyleSheet('''
               #LabelTitle {
                   font-size: 60px;
                   color: #93deed;
               }

               #LabelDesc {
                   font-size: 30px;
                   color: #c2ced1;
               }

               #LabelLoading {
                   font-size: 30px;
                   color: #e8e8eb;
               }

               QFrame {
                   background-color: #2F4454;
                   color: rgb(220, 220, 220);
               }

               QProgressBar {
                   background-color: #DA7B93;
                   color: rgb(200, 200, 200);
                   border-style: none;
                   border-radius: 10px;
                   text-align: center;
                   font-size: 30px;
               }

               QProgressBar::chunk {
                   border-radius: 10px;
                   background-color: qlineargradient(spread:pad x1:0, x2:1, y1:0.511364, y2:0.523, stop:0 #1C3334, stop:1 #376E6F);
               }
           ''')
    window.show()
    app.exec_()
    print('Closing Window...')
