import datetime
import hashlib
import json
import math
import os
import sys
import time
import platform
from multiprocessing import Queue
from threading import Thread
import phonenumbers
from phonenumbers import PhoneMetadata
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, QSize, QRect, pyqtSignal, QThread, QDate, QPoint, QPropertyAnimation, QRectF
from PyQt5.QtGui import QPixmap, QImage, QIcon, QPainter, QColor, QPalette, QBrush, QPainterPath
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedLayout, \
    QListWidget, QScrollArea, QMainWindow, QDialog, QLineEdit, QComboBox, QCheckBox, QFrame, QProgressBar, \
    QSizePolicy, QScrollBar, QAbstractItemView, QStackedWidget, QGridLayout, QMessageBox, QListWidgetItem, \
    QDesktopWidget, QMenuBar, QAction, QFileDialog, QSpacerItem, QDateEdit, QGraphicsOpacityEffect
from PyQt5 import QtCore
import yoloScript
import multiprocessing
import pickle
from threading import Event

all_dispositivos_widget = []
global_devices = []


def absolutePath(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


if platform.system() == "Windows":
    dropdown_icon_path = './icons/dropdown.png'
    calendar_icon_path = './icons/calendario.png'
else:
    dropdown_icon_path = absolutePath('icons/dropdown.png')
    calendar_icon_path = absolutePath('icons/calendario.png')


class CustomScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                width: 15px;
            }
            QScrollBar::handle:vertical {
                background-color: #5B5B5B;
                border-radius: 7px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #292929; /* Background color of the track */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                height: 15px;
            }
            QScrollBar::handle:horizontal {
                background-color: #5B5B5B;
                border-radius: 7px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: #292929; /* Background color of the track */
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)


class HorizontalLayout(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.scroll_area = CustomScrollArea()

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

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                width: 15px;
            }
            QScrollBar::handle:vertical {
                background-color: #5B5B5B;
                border-radius: 7px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #292929; /* Background color of the track */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.scroll_area.horizontalScrollBar().setStyleSheet("""
            QScrollBar:horizontal {
                height: 15px;
            }
            QScrollBar::handle:horizontal {
                background-color: #5B5B5B;
                border-radius: 7px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: #292929; /* Background color of the track */
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        self.scroll_content = QWidget(self.scroll_area)
        self.scroll_content.setLayout(self.layout)

        self.scroll_area.setWidget(self.scroll_content)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.scroll_area)
        self.setLayout(self.main_layout)
        self.setStyleSheet("background-color: transparent")
        self.num_devices = 0
        self.widgets = []

    def updateWidgets(self, widgets):
        self.num_devices = len(widgets)

        # Remove old widgets from the layout
        for widget in self.widgets:
            self.layout.removeWidget(widget)
            widget.setParent(None)

        self.widgets = widgets
        self.adjustWidgets()

    def adjustWidgets(self):
        width = self.scroll_area.viewport().width()
        columns = max(1, width // 400)  # Number of widgets per row, assuming each widget max width is 400

        x = 0
        for i in range((self.num_devices + columns - 1) // columns):  # Calculate the number of rows needed
            for j in range(columns):
                if x < self.num_devices:
                    self.widgets[x].setMaximumSize(400, 400)
                    self.layout.addWidget(self.widgets[x], i, j)
                    x += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustWidgets()


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.myApp = None
        self.setWindowTitle('Splash Screen')
        self.setFixedSize(1100, 500)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.counter = 0
        self.n = 70

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.loading)
        self.timer.start(20)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame()
        self.frame.setObjectName("frame")
        layout.addWidget(self.frame)

        frame_layout = QVBoxLayout()
        frame_layout.setSpacing(0)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(frame_layout)

        # Create a horizontal layout for the image and title
        title_layout = QVBoxLayout()

        # QLabel for the image
        self.image_label = QLabel(self.frame)
        pixmap = QPixmap(absolutePath('icons/iconBranco.png'))
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(100, 100)  # Set the size of the image
        self.image_label.setScaledContents(True)  # Scale image to fit the QLabel
        # QLabel for the title
        self.labelTitle = QLabel(self.frame)
        self.labelTitle.setObjectName('LabelTitle')
        self.labelTitle.setText('SafeSight')
        self.labelTitle.setAlignment(Qt.AlignLeft)

        # Add the image and title to the horizontal layout
        title_layout.addWidget(self.image_label, 0, Qt.AlignCenter)
        title_layout.addWidget(self.labelTitle, 0, Qt.AlignCenter)

        # Add the title layout to the frame layout
        frame_layout.addLayout(title_layout)

        self.labelDescription = QLabel(self.frame)
        self.labelDescription.setObjectName('LabelDesc')
        self.labelDescription.setText('<strong>A carregar os dispositivos</strong>')
        listar_thread = ListarThread(self)
        listar_thread.start()
        self.labelDescription.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(self.labelDescription)

        self.progressBar = QProgressBar(self.frame)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setFormat('%p%')
        self.progressBar.setTextVisible(True)
        self.progressBar.setRange(0, self.n)
        self.progressBar.setValue(0)
        frame_layout.addWidget(self.progressBar)

        self.labelLoading = QLabel(self.frame)
        self.labelLoading.setObjectName('LabelLoading')
        self.labelLoading.setAlignment(Qt.AlignCenter)
        self.labelLoading.setText('loading...')
        frame_layout.addWidget(self.labelLoading)

        # Apply stylesheet
        self.setStyleSheet("""
                #LabelTitle {
                   margin-bottom: 20px; 
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
                #frame {
                    border-radius: 15px;
                    background-color: #292929;
                    color: #ffffff;
                    padding: 40px 10px 30px 10px;
                }
        """)

    def loading(self):
        self.progressBar.setValue(self.counter)
        if self.counter == int(self.n * 0.3):
            self.labelDescription.setText('<strong>A carregar os alertas</strong>')
        elif self.counter == int(self.n * 0.6):
            self.labelDescription.setText('<strong>A carregar o YOLO</strong>')
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
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:pressed {
                background-color: #404040;
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
            QPushButton:hover {
                background-color: #BFBFBF;
            }
            QPushButton:pressed {
                background-color: #A5A5A5;
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
            QPushButton:hover {
                background-color: #3e3e3e;
            }
            QPushButton:pressed {
                background-color: #4e4e4e;
            }
            QPushButton:disabled {
                background-color: #808080;
                color: #A0A0A0;
            }
        """)


class DispositivoWidget(QWidget):
    image_clicked = QtCore.pyqtSignal(str, QPixmap)  # Define a signal with device name

    def __init__(self, name, device, objToFind, lista_alertas, dispositovo_window, delay):
        super().__init__()
        self.image_window = None
        self.dispositivos_window = dispositovo_window
        self.pause = False
        self.name = name
        self.image_path = absolutePath("frames/noCamera.jpg")
        self.objToFind = objToFind
        layout = QVBoxLayout(self)
        self.device = device
        self.label = QLabel(name)
        self.label.setStyleSheet("font-size: 25px; color: #FFFFFF")

        # Setting button
        self.settings_button = WidgetButton()
        self.settings_button.setIcon(QIcon(absolutePath("icons/settings.png")))
        self.settings_button.setIconSize(QSize(40, 40))
        self.settings_button.setFixedSize(50, 50)
        self.settings_button.clicked.connect(self.setting_button_clicked)

        self.expand_button = WidgetButton()
        self.expand_button.setIcon(QIcon(absolutePath("icons/expand.png")))
        self.expand_button.setIconSize(QSize(35, 35))
        self.expand_button.setFixedSize(50, 50)
        self.expand_button.clicked.connect(self.expand_button_clicked)

        self.remove_button = WidgetButton()
        self.remove_button.setIcon(QIcon(absolutePath("icons/remove.png")))
        self.remove_button.setIconSize(QSize(35, 35))
        self.remove_button.setFixedSize(50, 50)
        self.remove_button.clicked.connect(self.remove_button_clicked)

        layout_imagem = QHBoxLayout()

        self.iconPause = QIcon(absolutePath("icons/pause_circle.png"))

        self.image_label = QLabel()
        pixmap = QPixmap(self.image_path)
        pixmap = pixmap.scaledToWidth(325)
        self.roundedPixmap = self.roundPixmap(pixmap)
        self.image_label.setPixmap(self.roundedPixmap)
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
        self.start_button.setIcon(QIcon(absolutePath("icons/play.png")))
        self.start_button.setIconSize(QSize(30, 30))
        self.start_button.setFixedSize(50, 50)
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button = WidgetButton()
        self.stop_button.setIcon(QIcon(absolutePath("icons/pause.png")))
        self.stop_button.setIconSize(QSize(35, 35))
        self.stop_button.setFixedSize(50, 50)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.live_button = WidgetButton()
        self.live_button.setIcon(QIcon(absolutePath("icons/live.png")))
        self.live_button.clicked.connect(self.live_button_clicked)
        self.live_button.setIconSize(QSize(35, 35))
        self.live_button.setFixedSize(50, 50)
        self.combo_delay_label = QLabel("Delay:")
        self.combo_delay_label.setStyleSheet("font-size: 15px; color: #FFFFFF")
        self.last_delay = delay
        self.combo_delay = QComboBox()
        global dropdown_icon_path
        combo_style = f"""
            QComboBox {{
                font-size: 15px;
                background-color: #D9D9D9;
                color: #000000;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }}
            QComboBox::drop-down {{
                border: 0px;
                background-color: #D9D9D9;
                margin-right: 20px;
            }}
            QComboBox::down-arrow {{
                image: url({dropdown_icon_path});
                width: 20px;
                height: 20px;
            }}
            QComboBox::item {{
                background-color: #5B5B5B;
                color: #FFFFFF;
            }}
            QComboBox::item:!selected {{
                background-color: #D9D9D9;
                color: #000000;
            }}
            QMessageBox {{
                 background-color: #5B5B5B;
                 color: #000000;
            }}
            QMessageBox QPushButton {{
                border: none;
                border-radius: 10px;
                font-size: 16px;
                padding: 10px;
                color: #FFFFFF;
                background-color: #292929;
            }}
        """
        self.combo_delay.setStyleSheet(combo_style)
        self.populate_combo_delay()
        self.combo_delay.currentIndexChanged.connect(self.combo_delay_changed)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.live_button)
        button_layout.addWidget(self.combo_delay_label)
        button_layout.addWidget(self.combo_delay)
        layout.addLayout(button_layout)
        self.start_button_clicked()
        self.lista_alertas = lista_alertas
        self.classes_to_lose_alert = []

    def roundPixmap(self, pixmap, radius_percent=4):
        width = pixmap.width()
        height = pixmap.height()
        size = min(width, height)
        radius = (radius_percent / 100) * size

        rounded_pixmap = QPixmap(width, height)
        rounded_pixmap.fill(Qt.transparent)

        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height, radius, radius)
        painter.setClipPath(path)

        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return rounded_pixmap

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
        self.image_window = ImageWindow(self.image_label.pixmap().scaledToWidth(800), self, self.device)
        self.image_window.show()

    def setting_button_clicked(self):
        # Guarda o valor do delay que está na combobox
        delay = self.combo_delay.itemData(self.combo_delay.currentIndex())
        # Abre a janela de configuração
        self.config_dialog = ConfigurarDispositivo(self.name, self.device, self.objToFind,
                                                   alertas_dict=self.lista_alertas, time_frame=delay)
        # Conecta o sinal done_clicked à funcao handle_done_clicked
        self.config_dialog.done_clicked.connect(self.handle_done_clicked)
        self.config_dialog.exec_()

    def handle_done_clicked(self, name, device, selected_items, lista_alertas):
        print(f"Updating device '{device}' with selected items: {selected_items}")
        self.name = name
        # Altera o nome do DispositivoWidget
        self.label.setText(name)
        self.objToFind = selected_items
        # Caso o dispositivo seja um número, converte para inteiro
        if device.isdigit():
            device = int(device)
        self.lista_alertas = lista_alertas
        # Atualiza os objetos a detetar e a lista de alertas do dispositivo no yoloScript
        yoloScript.update_obj_to_find(device, self.objToFind, self.lista_alertas)

    def update_image(self, frame):
        if self.pause:
            return
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        pixmap = self.roundPixmap(pixmap)
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

    def combo_delay_changed(self):
        delay = self.combo_delay.itemData(self.combo_delay.currentIndex())
        if delay == self.last_delay:
            return
        for classe, tempo in self.lista_alertas.items():
            if tempo > 0:
                if tempo < delay or tempo % delay != 0:
                    self.classes_to_lose_alert.append(classe)
        if len(self.classes_to_lose_alert) > 0:
            self.show_warning()
        else:
            self.start_button_clicked()

    def show_warning(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('Aviso')
        msg_box.setText(
            'Ao alterar o tempo de captura, os objetos cujos tempos para emissão de alerta não sejam maiores e múltiplos do tempo de captura, vão deixar de emitir alertas. Deseja continuar?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet("""
                                QMessageBox {
                                    background-color: #4e4e4e; /* Light background color */
                                }
                                QMessageBox QLabel {
                                    color: white;
                                }
                                QAbstractButton {
                                    background-color: #292929; /* Darker color for buttons */
                                    color: white;
                                    border-radius: 10px; /* Rounded borders */
                                    padding: 5px 10px;
                                }
                                QAbstractButton:hover {
                                    background-color: #3d3d3d; /* Slightly lighter on hover */
                                }
                                StandardButton {
                                    background-color: #292929; /* Darker color for buttons */
                                    color: white;
                                    border-radius: 10px; /* Rounded borders */
                                    padding: 5px 10px;
                                }
                                StandardButton:hover {
                                    background-color: #3d3d3d;
                                }
                                QPushButton {
                                    background-color: #292929;
                                    color: white;
                                    border-radius: 10px;
                                    padding: 5px 10px;
                                }
                                QPushButton:hover {
                                    background-color: #3d3d3d;
                                }

                            """)
        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            for classe in self.classes_to_lose_alert:
                self.lista_alertas[classe] = 0
            self.classes_to_lose_alert.clear()
            yoloScript.update_obj_to_find(self.device, self.objToFind, self.lista_alertas)
            self.start_button_clicked()
        else:
            self.combo_delay.setCurrentIndex(self.combo_delay.findData(self.last_delay))

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
        self.combo_delay.setCurrentIndex(self.combo_delay.findData(self.last_delay))

    def change_delay(self):
        self.last_delay = self.combo_delay.itemData(self.combo_delay.currentIndex())
        yoloScript.change_delay(self.device, self.last_delay)

    def remove_button_clicked(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('Confirmação')
        msg_box.setText('Tem a certeza que deseja remover o dispositivo?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #4e4e4e; /* Light background color */
            }
            QMessageBox QLabel {
                color: white;
            }
            QAbstractButton {
                background-color: #292929; /* Darker color for buttons */
                color: white;
                border-radius: 10px; /* Rounded borders */
                padding: 5px 10px;
            }
            QAbstractButton:hover {
                background-color: #3d3d3d; /* Slightly lighter on hover */
            }
            StandardButton {
                background-color: #292929; /* Darker color for buttons */
                color: white;
                border-radius: 10px; /* Rounded borders */
                padding: 5px 10px;
            }
            StandardButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton {
                background-color: #292929;
                color: white;
                border-radius: 10px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
    
        """)

        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            self.remove_button_action()

    def remove_button_action(self):
        yoloScript.remove_device(self.device)
        all_dispositivos_widget.remove(self)
        self.dispositivos_window.remove_device(self.device)
        if self.image_window is not None:
            self.image_window.hide()
            self.image_window.close()
        self.deleteLater()

    def handle_close_image_window(self):
        self.image_window = None

    def to_dict(self):
        return {
            "name": self.name,
            "device": self.device,
            "objs": self.objToFind,
            "alerts": self.lista_alertas,
            "delay": self.last_delay
        }

    @staticmethod
    def from_dict(self, data):
        return DispositivoWidget(data["name"], data["device"], data["objs"], data["alerts"], self.dispositivos_window)


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
    alertReceived = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.main_window = parent
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
        self.mosaicoButton.setIcon(QIcon(absolutePath("icons/mosaico_2.png")))
        self.mosaicoButton.clicked.connect(self.layout_mosaico)
        self.threads = []

        self.horizontalbutton = LightButton()
        self.horizontalbutton.setIcon(QIcon(absolutePath("icons/mosaico.png")))
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
        """
        self.add_dispositivo("Dispositivo 1", 0, [], {})
        self.add_dispositivo("Dispositivo 2", 1, [], {})
        self.add_dispositivo("Dispositivo 3", 2, [], {})
        self.add_dispositivo("Dispositivo 4", "http://75.149.26.30:1024/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 5", "http://74.65.56.223:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 6", "http://72.199.200.5:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 7", "http://109.192.213.146:8888/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 8", "http://139.64.168.120:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 9", "http://77.98.38.218:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 10", "http://97.68.104.34:80/mjpg/video.mjpg", [], {})
        self.add_dispositivo("Dispositivo 11", "http://62.131.207.209:8080/cam_1.cgi", [], {})
        self.add_dispositivo("Dispositivo 12", "http://80.15.116.66:86/SnapshotJPEG?Resolution=640x480&amp;Quality=Clarity&amp;1713985444", [], {})
        self.add_dispositivo("Dispositivo 13", "http://195.223.180.50/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 14", "http://45.46.151.31:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 15", "http://216.137.193.126:8083/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 16", "http://109.206.96.58:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 17", "http://198.71.120.207:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 18", "http://79.120.134.229:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 19", "http://99.114.240.169:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 20", "http://216.137.193.126:8080/cam_1.jpg", [], {})
        self.add_dispositivo("Dispositivo 21", "http://185.97.122.128/cgi-bin/faststream.jpg?stream=half&fps=30&rand=COUNTER", [], {})
        self.add_dispositivo("Dispositivo 22", "http://37.156.71.253/cgi-bin/faststream.jpg?stream=half&fps=15&rand=COUNTER", [], {})
        self.add_dispositivo("Dispositivo 23", "http://85.193.230.144:81/webcapture.jpg?command=snap&channel=1?1718299430", [], {})
        self.add_dispositivo("Dispositivo 24", "http://166.247.77.253:81/mjpg/video.mjpg", [], {})
        """

    def layout_mosaico(self):
        global all_dispositivos_widget
        self.mosaicoButton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #292929}")
        self.horizontalbutton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.horizontalbutton.setEnabled(True)
        self.mosaicoButton.setEnabled(False)
        self.stacked_layout.setCurrentIndex(1)
        for widget in all_dispositivos_widget:
            self.horizontal_layout.removeWidget(widget)
        self.mosaico_layout.updateWidgets(all_dispositivos_widget)

    def layout_horizontal(self):
        self.horizontalbutton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #292929}")
        self.mosaicoButton.setStyleSheet(self.mosaicoButton.styleSheet() + "QPushButton{background-color: #5B5B5B}")
        self.horizontalbutton.setEnabled(False)
        self.mosaicoButton.setEnabled(True)
        self.stacked_layout.setCurrentIndex(0)
        self.mosaico_layout.updateWidgets(all_dispositivos_widget)
        for widget in all_dispositivos_widget:
            self.horizontal_layout.addWidget(widget)

    def add_dispositivo(self, name, device, objToFind, lista_alertas, delay=10):
        global all_dispositivos_widget
        dispositivo_widget = DispositivoWidget(name, device, objToFind, lista_alertas, self, delay)
        all_dispositivos_widget.append(dispositivo_widget)
        self.dispositivos_dict[device] = dispositivo_widget
        if self.stacked_layout.currentIndex() == 1:
            self.mosaico_layout.updateWidgets(all_dispositivos_widget)
        if self.stacked_layout.currentIndex() == 0:
            self.horizontal_layout.addWidget(dispositivo_widget)
        thread = Thread(target=self.runscript_thread, args=(device, objToFind, lista_alertas))
        thread.start()
        self.threads.append(thread)
        if not self.reading:
            thread = Thread(target=self.readQueue)
            thread.start()
            self.threads.append(thread)
            self.reading = True

    def runscript_thread(self, device, objToFind, alertas_dict):
        yoloScript.addDispositivoToPredict(device, objToFind, alertas_dict, self.queue, 10)

    def readQueue(self):
        while True:
            try:
                frames = self.queue.get()
                if frames == -1:
                    break
                for device, frame in frames.items():
                    if device == -2:
                        self.alertReceived.emit(frame)
                        continue
                    if device in self.dispositivos_dict.keys():
                        self.dispositivos_dict[device].update_image(frame)
                        if self.image_window is not None:
                            self.image_window.update_image(frame)
            except Exception as e:
                print(f"Error reading queue: {e}")

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
        if self.stacked_layout.currentIndex() == 1:
            self.mosaico_layout.updateWidgets(all_dispositivos_widget)
        del self.dispositivos_dict[device]

    def to_dict(self):
        global all_dispositivos_widget
        devices = []
        for widget in all_dispositivos_widget:
            devices.append(widget.to_dict())
        return {"devices": devices}

    def from_dict(self, data):
        global all_dispositivos_widget
        all_dispositivos_widget.clear()
        for device_data in data.get("devices", []):
            self.add_dispositivo(device_data["name"], device_data["device"], device_data["objs"], device_data["alerts"],
                                 device_data["delay"])


class AlertaDetalhes(QMainWindow):
    def __init__(self, frame, alerta_tempo, device, classe, timestamp, id_objeto):
        super().__init__()
        self.setWindowIcon(QIcon(absolutePath('icons/iconBranco.png')))
        self.setWindowTitle("Detalhes do Alerta")
        # Set the window size and position to be centered
        self.setGeometry(100, 100, 800, 600)
        self.resize(800, 600)
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Label para a imagem
        self.image_label = QLabel()

        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        max_size = self.size()
        pixmap = pixmap.scaled(max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)  # Para redimensionar a imagem para o tamanho do QLabel
        main_layout.addWidget(self.image_label, 1)  # Adicionando a imagem com mais espaço

        # Layout para os detalhes
        details_layout = QVBoxLayout()

        string_tempo = self.format_alert_time(alerta_tempo)
        self.descricao_label = QLabel(f"<b> Tempo parado: {string_tempo}</b>")
        self.device_label = QLabel(f"<b> Device: {device} </b>")
        self.classe_label = QLabel(f"<b> Classe: {classe} </b>")
        self.id_objeto_label = QLabel(f"<b> ID do objeto: {id_objeto} </b>")
        time_struct = time.localtime(timestamp)
        data = time.strftime('%d/%m/%Y %H:%M:%S', time_struct)
        self.data_label = QLabel(f"<b> Data: {data} </b>")

        details_layout.addWidget(self.descricao_label)
        details_layout.addWidget(self.device_label)
        details_layout.addWidget(self.classe_label)
        details_layout.addWidget(self.id_objeto_label)
        details_layout.addWidget(self.data_label)

        # Adicionar os detalhes abaixo da imagem
        main_layout.addLayout(details_layout)

        self.setStyleSheet("""
            AlertaDetalhes {
                   background-color: #292929;
               }
            QLabel {
                color: #FFFFFF;
                font-size: 20px;
            }
        """)

    def format_alert_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        if hours > 0:
            if minutes > 0 and seconds > 0:
                time_str = f'{int(hours)} horas, {int(minutes)} minutos e {int(seconds)} segundos'
            elif minutes > 0 and seconds == 0:
                time_str = f'{int(hours)} horas e {int(minutes)} minutos'
            elif minutes == 0 and seconds > 0:
                time_str = f'{int(hours)} horas e {int(seconds)} segundos'
            else:
                time_str = f'{int(hours)} horas'
        elif minutes > 0:
            if seconds > 0:
                time_str = f'{int(minutes)} minutos e {int(seconds)} segundos'
            else:
                time_str = f'{int(minutes)} minutos'
        else:
            time_str = f'{int(seconds)} segundos'

        return time_str


class AlertaWidget(QWidget):
    def __init__(self, alerta, alerta_window):
        super().__init__()
        self.setFixedHeight(150)
        self.alerta = alerta
        # Layout principal que conterá todos os elementos
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.alerta_window = alerta_window
        # Layout de grade para posicionar o botão no canto superior esquerdo
        top_layout = QGridLayout()
        main_layout.addLayout(top_layout)

        # Botão para eliminar o widget
        self.remove_button = QPushButton()
        self.remove_button.setIcon(QIcon(absolutePath("icons/close_white.png")))
        self.remove_button.setIconSize(QSize(15, 15))
        self.remove_button.setFixedSize(25, 25)
        self.remove_button.clicked.connect(self.remove_button_clicked_msg_box)
        top_layout.addWidget(self.remove_button, 0, 0, Qt.AlignTop | Qt.AlignRight)
        # Layout horizontal para o restante do conteúdo
        self.item_layout = QHBoxLayout()
        main_layout.addLayout(self.item_layout)

        # Adiciona o texto à esquerda
        self.texto_esquerda = QLabel(f"Dispositivo {alerta.device}\n\n{alerta.get_descricao()}")
        self.texto_esquerda.setStyleSheet("font-size: 16px; color: #FFFFFF")
        self.item_layout.addWidget(self.texto_esquerda)

        # Adiciona a imagem à direita
        imagem_direita = QLabel()
        height, width, channel = alerta.get_photo().shape
        bytes_per_line = 3 * width
        img_array_rgb = cv2.cvtColor(alerta.get_photo(), cv2.COLOR_BGR2RGB)
        q_img = QImage(img_array_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        pixmap = pixmap.scaledToWidth(100)
        imagem_direita.setPixmap(pixmap)
        self.item_layout.addWidget(imagem_direita, alignment=Qt.AlignRight)

        self.device = alerta.get_device()
        self.classe = alerta.get_classe()
        self.timestamp = alerta.get_date()
        self.tempo_alerta = alerta.get_tempo_alerta()
        self.detalhes_window = None

        # Set initial background color
        self.setStyleSheet("""
                    AlertaWidget {
                        background-color: #292929;
                    }
                """)

    def enterEvent(self, event):
        self.setStyleSheet("""
            AlertaWidget {
                background-color: #1f1f1f;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            AlertaWidget {
                background-color: #292929;
            }
        """)
        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_alerta_detalhes()

    def paintEvent(self, event):
        # Call the base class paintEvent to ensure standard painting behavior
        super().paintEvent(event)

        # Set the background color for AlertaWidget
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().color(QPalette.Background))

    def open_alerta_detalhes(self):
        alerta_tempo = self.alerta.get_tempo_alerta()
        device = self.alerta.get_device()
        classe = self.alerta.get_classe()
        data = self.alerta.get_date()
        imagem = self.alerta.get_photo()
        id_objeto = self.alerta.get_id_objeto()

        self.detalhes_window = AlertaDetalhes(imagem, alerta_tempo, device, classe, data, id_objeto)
        self.detalhes_window.show()

    def remove_button_clicked_msg_box(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('Confirmação')
        msg_box.setText('Tem a certeza que deseja remover o alerta?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #4e4e4e;
                    }
                    QMessageBox QLabel {
                        color: white;
                    }
                    QAbstractButton {
                        color: white;
                        border-radius: 10px;
                        padding: 5px 10px;
                    }
                    QAbstractButton:hover {
                        background-color: #3d3d3d;
                    }
                    StandardButton {
                        background-color: #4e4e4e;
                        color: white;
                        border-radius: 10px;
                        padding: 5px 10px;
                    }
                    StandardButton:hover {
                        background-color: #3d3d3d;
                    }
                    QPushButton {
                        background-color: #4e4e4e;
                        color: white;
                        border-radius: 10px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                    }

                """)

        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            self.remove_button_clicked()

    def remove_button_clicked(self):
        try:
            alertas = []
            alertas_path = absolutePath("alertas.bin")
            with open(alertas_path, 'rb') as f:
                while True:
                    try:
                        alertas.append(pickle.load(f))
                    except EOFError:
                        break
            alertas = [a for a in alertas if a.get_id() != self.alerta.get_id()]
            with open(alertas_path, 'wb') as f:
                for alerta in alertas:
                    pickle.dump(alerta, f)
        except Exception as e:
            print(f"Erro ao remover alerta: {e}")

        self.alerta_window.remove_alerta_widget(self)
        self.setParent(None)
        self.deleteLater()


class AlertasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.alertas = []
        self.setWindowTitle("Alertas")
        self.setGeometry(100, 100, 600, 400)  # Definindo a geometria da janela
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.scroll_area = QScrollArea()
        self.scroll_area.verticalScrollBar().setStyleSheet("""
                    QScrollBar:vertical {
                        width: 15px;
                    }
                    QScrollBar::handle:vertical {
                        background-color: #5B5B5B;
                        border-radius: 7px;
                    }
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                        background: #292929; /* Background color of the track */
                    }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                        height: 0px;
                    }
                """)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)  # Definindo um layout QVBoxLayout para a área de rolagem
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)  # Filters layout

        self.filter_layout = QHBoxLayout()
        self.filter_layout_2 = QHBoxLayout()
        self.filter_layout_vertical = QVBoxLayout()

        self.device_spacer_item = QSpacerItem(50, 0, QSizePolicy.Expanding)
        self.device_filter = QComboBox()
        self.device_filter.currentIndexChanged.connect(self.change_index_device)
        self.label_device = QLabel("Device: ")
        self.device_filter.setEditable(True)
        self.device_filter.setPlaceholderText("Filter by device")

        self.clear_device_filter = QPushButton()
        self.clear_device_filter.setIcon(QIcon(absolutePath("icons/close_red.png")))
        self.clear_device_filter.setIconSize(QSize(15, 15))
        self.clear_device_filter.setFixedSize(25, 25)
        self.clear_device_filter.clicked.connect(self.clear_filter_device)
        self.clear_device_filter_placeholder = QLabel()  # Placeholder widget
        self.clear_device_filter_placeholder.setFixedSize(25, 25)
        self.clear_device_filter.hide()

        self.object_filter = QComboBox()
        self.object_filter.currentIndexChanged.connect(self.change_index_obj)
        self.label_object = QLabel("Object: ")
        self.object_filter.setEditable(True)
        self.object_filter.setPlaceholderText("Filter by object")

        self.clear_obj_filter = QPushButton()
        self.clear_obj_filter.setIcon(QIcon(absolutePath("icons/close_red.png")))
        self.clear_obj_filter.setIconSize(QSize(15, 15))
        self.clear_obj_filter.setFixedSize(25, 25)
        self.clear_obj_filter.clicked.connect(self.clear_filter_obj)
        self.clear_obj_filter_placeholder = QLabel()  # Placeholder widget
        self.clear_obj_filter_placeholder.setFixedSize(25, 25)
        self.clear_obj_filter.hide()

        self.clear_filter_btn = LightButton("Clear Filters")
        self.clear_filter_btn.setMaximumWidth(140)  # Adjust button width
        self.clear_filter_btn.clicked.connect(self.clear_filters)
        self.clear_filter_btn.setObjectName("clear_filter_btn")

        self.eliminar_alertas_btn = LightButton("Eliminar Alertas")
        self.eliminar_alertas_btn.setMaximumSize(120, 30)
        self.eliminar_alertas_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 5px;
                font-size: 12px;
                padding: 5px;
                color: #FFFFFF;
                background-color: #5B5B5B;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:pressed {
                background-color: #404040;
            }""")
        self.eliminar_alertas_btn.clicked.connect(self.eliminar_alertas)

        self.label_ordem = QLabel("Order by: ")
        self.order_filter = QComboBox()
        self.order_filter.addItems(["Order by date ↓", "Order by date ↑"])
        self.order_filter.currentIndexChanged.connect(self.filter_alertas)
        self.date_spacer_item = QSpacerItem(25, 0, QSizePolicy.Fixed)

        # Date filters
        self.label_date_from = QLabel("De: ")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.filter_alertas)

        self.label_date_to = QLabel("Até: ")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())  # Default to today
        self.date_to.dateChanged.connect(self.filter_alertas)
        self.clear_spacer_item = QSpacerItem(50, 0, QSizePolicy.Expanding)

        self.filter_layout.addSpacerItem(self.device_spacer_item)
        self.filter_layout.addWidget(self.label_device, 0, Qt.AlignCenter | Qt.AlignRight)
        self.filter_layout.addWidget(self.device_filter, 0, Qt.AlignCenter | Qt.AlignLeft)
        self.filter_layout.addWidget(self.clear_device_filter, 0, Qt.AlignLeft)
        self.filter_layout.addWidget(self.clear_device_filter_placeholder, 0, Qt.AlignLeft)
        self.filter_layout.addWidget(self.label_object, 0, Qt.AlignCenter | Qt.AlignRight)
        self.filter_layout.addWidget(self.object_filter, 0, Qt.AlignCenter | Qt.AlignLeft)
        self.filter_layout.addWidget(self.clear_obj_filter_placeholder, 0, Qt.AlignLeft)
        self.filter_layout.addWidget(self.clear_obj_filter, 0, Qt.AlignLeft)
        self.filter_layout.addWidget(self.label_ordem, 0, Qt.AlignCenter | Qt.AlignRight)
        self.filter_layout.addWidget(self.order_filter, 0, Qt.AlignCenter | Qt.AlignLeft)
        self.filter_layout.addSpacerItem(self.clear_spacer_item)
        self.filter_layout_2.addSpacerItem(self.clear_spacer_item)
        self.filter_layout_2.addWidget(self.label_date_from, 0, Qt.AlignCenter | Qt.AlignRight)
        self.filter_layout_2.addWidget(self.date_from, 0, Qt.AlignCenter | Qt.AlignLeft)
        self.filter_layout_2.addSpacerItem(self.date_spacer_item)
        self.filter_layout_2.addWidget(self.label_date_to, 0, Qt.AlignCenter | Qt.AlignRight)
        self.filter_layout_2.addWidget(self.date_to, 0, Qt.AlignCenter | Qt.AlignLeft)
        self.filter_layout_2.addWidget(self.clear_filter_btn, 0, Qt.AlignLeft)
        self.filter_layout_2.addSpacerItem(self.clear_spacer_item)
        self.object_filter.addItems(list(sorted(yoloScript.get_classes())))

        self.filter_layout_vertical.addLayout(self.filter_layout)
        self.filter_layout_vertical.addLayout(self.filter_layout_2)
        self.filter_layout_vertical.addWidget(self.eliminar_alertas_btn, 0, Qt.AlignBottom | Qt.AlignRight)
        self.layout.addLayout(self.filter_layout_vertical)

        # Add a button layout
        # Add a button layout
        """
        self.button_layout = QHBoxLayout()
        self.apply_filter_btn = LightButton("Apply Filters")
        self.apply_filter_btn.setMaximumWidth(120)  # Adjust button width
        self.apply_filter_btn.clicked.connect(self.filter_alertas)
        self.button_layout.addWidget(self.apply_filter_btn, 0, Qt.AlignCenter | Qt.AlignRight)  # Adjust alignment

        self.button_layout.addWidget(self.clear_filter_btn, 0, Qt.AlignCenter | Qt.AlignLeft)  # Adjust alignment
        self.layout.addLayout(self.button_layout)
        """
        self.label_sem_alertas = QLabel("Sem alertas!")
        self.label_sem_alertas.setStyleSheet("font-size: 20px; color: white; margin-top: 50px; font-weight: bold")
        self.label_sem_alertas.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_sem_alertas)
        self.label_sem_alertas.hide()
        self.alertas_widgets = []
        self.layout.addWidget(self.scroll_area)
        self.carregar_alertas()
        if len(self.alertas) == 0:
            self.label_sem_alertas.show()
            self.scroll_area.hide()
        if len(self.alertas) > 0:
            ultimo_alerta = self.alertas[-1]
            yoloScript.ultimo_id_alerta(self.alertas[0].get_id())
            data = datetime.datetime.fromtimestamp(ultimo_alerta.get_date())
            self.date_from.setDate(QDate(data.year, data.month, data.day))
        global dropdown_icon_path
        global calendar_icon_path
        self.setLayout(self.layout)
        self.setStyleSheet(f"""
            QPushButton#clear_filter_btn {{
                margin-left: 20px;
            }}
            QLabel {{
                font-size: 15px;
                color: #FFFFFF;
                margin: 0px;  /* Reduce margin */
            }}
            QPushButton {{
                margin-right: 10px;  /* Adjust margin */
            }}
            QComboBox {{
                font-size: 15px;
                background-color: #D9D9D9;
                color: #000000;
                border: 1px solid #D9D9D9;
                border-radius: 10px;
                height: 25px;
                width: 150px;
                padding: 2px 5px;
                margin: 0px;  /* Reduce margin */
            }}
                
            QDateEdit {{
                font-size: 15px;
                background-color: #D9D9D9;
                color: #000000;
                border: 1px solid #D9D9D9;
                border-radius: 10px;
                height: 25px;
                width: 150px;
                padding: 2px 5px;
                margin: 0px;  /* Reduce margin */
            }}
            
            QComboBox::drop-down {{
                border: none;
                background-color: #D9D9D9;
                margin-right: 5px;  /* Adjust margin */
                height: 30px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: #D9D9D9; /* Background color of the items */
                border-radius: 10px;
                color: #000000; /* Text color of the items */
                padding-top: 5px;
            }}
            QComboBox::item:!selected {{
                background-color: #D9D9D9;
                color: #000000;
            }}
            QHBoxLayout {{
                spacing: 0px; /* Eliminate spacing between widgets in the layout */
                margin: 0px; /* Eliminate margin */
            }}
            QComboBox::down-arrow {{
            image: url({dropdown_icon_path});
            width: 15px;
            height: 15px;
            }}
    
            QDateEdit::drop-down {{
                border: none;
                image: url({calendar_icon_path});
                margin-right: 5px;
                margin-top: 5px;
                height: 20px;
                width: 20px;
            }}
        """)

    def eliminar_alertas(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('Confirmação')
        msg_box.setText('Tem a certeza que deseja eliminar os alertas filtrados?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #4e4e4e;
                    }
                    QMessageBox QLabel {
                        color: white;
                    }
                    QAbstractButton {
                        color: white;
                        border-radius: 10px;
                        padding: 5px 10px;
                    }
                    QAbstractButton:hover {
                        background-color: #3d3d3d;
                    }
                    StandardButton {
                        background-color: #4e4e4e;
                        color: white;
                        border-radius: 10px;
                        padding: 5px 10px;
                    }
                    StandardButton:hover {
                        background-color: #3d3d3d;
                    }
                    QPushButton {
                        background-color: #4e4e4e;
                        color: white;
                        border-radius: 10px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                    }

                """)

        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            for alerta_widget in self.alertas_widgets[:]:
                alerta_widget.remove_button_clicked()

    def add_filter_row(self, label_text, combobox):
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        combobox = QComboBox()
        combobox.setEditable(True)
        combobox.setPlaceholderText(label_text)
        combobox.addItems([])
        row_layout.addWidget(label)
        row_layout.addWidget(combobox)
        self.layout.addLayout(row_layout)

    def carregar_alertas(self):
        self.alertas = []
        alertas_path = absolutePath("./alertas.bin")
        devices_in_alerts = set()
        self.device_filter.clear()
        try:
            if not os.path.exists(alertas_path):
                with open(alertas_path, 'wb') as file:
                    pass
            with open(alertas_path, 'rb') as file:
                while True:
                    alerta = pickle.load(file)
                    self.alertas.append(alerta)
                    devices_in_alerts.add(alerta.get_device())
        except EOFError:
            pass
        for device in devices_in_alerts:
            if isinstance(device, int):
                device = "Dispositivo: " + str(device)
            self.device_filter.addItem(str(device))
        self.alertas.reverse()
        if len(self.alertas) > 0:
            self.label_sem_alertas.hide()
            self.scroll_area.show()
            ultimo_alerta = self.alertas[-1]
            data = datetime.datetime.fromtimestamp(ultimo_alerta.get_date())
            self.date_from.setDate(QDate(data.year, data.month, data.day))
        self.mostrar_alertas(self.alertas)

    def filter_alertas(self):
        alertas = self.alertas
        # Aplica os filtros
        device_filter_text = self.device_filter.currentText().lower()
        object_filter_text = self.object_filter.currentText().lower()
        order_by = self.order_filter.currentText()
        if "↑" in order_by:
            alertas.sort(key=lambda x: x.get_date())
        else:
            alertas.sort(key=lambda x: x.get_date(), reverse=True)
        if device_filter_text:
            alertas = [
                alerta for alerta in alertas
                if (
                       str("Dispositivo: " + str(alerta.get_device())).lower() if isinstance(alerta.get_device(),
                                                                                             (int, float))
                       else str(alerta.get_device()).lower()
                   ) == device_filter_text.lower()
            ]

        if object_filter_text:
            alertas = [alerta for alerta in alertas if object_filter_text in alerta.get_descricao()]

        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        datetime_to = datetime.datetime(date_to.year, date_to.month, date_to.day)
        #Fazer com que seja o final do dia para incluir os alerta do proprio dia
        datetime_to = datetime_to + datetime.timedelta(days=1)
        datetime_to -= datetime.timedelta(seconds=1)
        timestamp_to = datetime_to.timestamp()
        datetime_from = datetime.datetime(date_from.year, date_from.month, date_from.day)
        timestamp_from = datetime_from.timestamp()
        alertas = [alerta for alerta in alertas if timestamp_from <= alerta.get_date() <= timestamp_to]
        # Chama a funcao que cria os AlertaWidgets e os adiciona ao layout
        self.mostrar_alertas(alertas)

    def clear_filters(self):
        # Clear filter selections
        self.device_filter.setCurrentIndex(-1)
        self.object_filter.setCurrentIndex(-1)
        self.order_filter.setCurrentIndex(0)
        self.date_to.setDate(QDate.currentDate())
        if len(self.alertas) != 0:
            ultimo_alerta = self.alertas[-1]
            data = datetime.datetime.fromtimestamp(ultimo_alerta.get_date())
            self.date_from.setDate(QDate(data.year, data.month, data.day))
        # Reload original alerts
        self.carregar_alertas()
        self.clear_device_filter.hide()
        self.clear_device_filter_placeholder.show()
        self.clear_obj_filter.hide()
        self.clear_obj_filter_placeholder.show()

    def mostrar_alertas(self, alertas):
        for widget in self.alertas_widgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.alertas_widgets = []
        for alerta in alertas:
            alerta_widget = AlertaWidget(alerta, self)
            self.alertas_widgets.append(alerta_widget)
            self.scroll_layout.addWidget(alerta_widget)

    def remove_alerta_widget(self, alerta_widget):
        if alerta_widget in self.alertas_widgets:
            self.alertas_widgets.remove(alerta_widget)
        if alerta_widget.alerta in self.alertas:
            self.alertas.remove(alerta_widget.alerta)
        if len(self.alertas_widgets) == 0 and len(self.alertas) == 0:
            self.label_sem_alertas.show()
            self.scroll_area.hide()

    def clear_filter_device(self):
        self.device_filter.setCurrentIndex(-1)
        self.clear_device_filter.hide()
        self.clear_device_filter_placeholder.show()
        self.filter_alertas()

    def clear_filter_obj(self):
        self.object_filter.setCurrentIndex(-1)
        self.clear_obj_filter.hide()
        self.clear_obj_filter_placeholder.show()
        self.filter_alertas()

    def change_index_device(self):
        self.clear_device_filter.show()
        self.clear_device_filter_placeholder.hide()
        self.filter_alertas()

    def change_index_obj(self):
        self.clear_obj_filter.show()
        self.clear_obj_filter_placeholder.hide()
        self.filter_alertas()


class ImageWindow(QMainWindow):
    def __init__(self, pixmap, parent=None, device=""):
        super().__init__()
        self.setWindowIcon(QIcon(absolutePath('icons/iconBranco.png')))
        self.dispositivo_widget = parent
        self.setWindowTitle(f'Imagem do Dispositivo {device}')
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
    def __init__(self, text, times, tempo=None):
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
        self.combo_box_time.currentIndexChanged.connect(self.update_time_unit)
        global dropdown_icon_path
        self.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: #000000;
            }}
            QComboBox {{
                font-size: 14px;
                background-color: #D9D9D9;
                color: #000000;
                border: none;
                border-radius: 10px;
                max-height: 20px;
            }}
            QComboBox::drop-down {{
                border: 0px;
                background-color: #D9D9D9;
                margin-right: 10px;
                min-height: 10px;
            }}
            QComboBox::down-arrow {{
                image: url({dropdown_icon_path});
                width: 11px;
                height: 11px;
            }}
            QComboBox::item {{
                background-color: #5B5B5B;
                color: #FFFFFF;
            }}
            QComboBox::item:!selected {{
                background-color: #D9D9D9;
                color: #000000;
            }}
        """)

        if tempo is not None:
            if tempo >= 3600:
                self.update_time_unit(2)
                tempo = tempo / 3600
                self.combo_box_time.setCurrentText("horas")
            elif tempo >= 60:
                self.update_time_unit(1)
                self.combo_box_time.setCurrentText("minutos")
                tempo = tempo / 60
            self.combo_box.setCurrentText(str(int(tempo)))

    def update_time_unit(self, index):
        unit = self.combo_box_time.itemText(index)
        times = self.change_times(self.times, unit)
        self.update_combo_box(times, unit)

    def change_times(self, times, unit):
        if unit == "segundos":
            return times
        elif unit == "minutos":
            return list(range(60))
        elif unit == "horas":
            return list(range(24))

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
            return int(self.combo_box.currentText())
        if self.combo_box_time.currentText() == "minutos":
            return int(self.combo_box.currentText()) * 60
        if self.combo_box_time.currentText() == "horas":
            return int(self.combo_box.currentText()) * 3600


class ConnectionThread(QThread):
    connection_status = pyqtSignal(bool, str)

    def __init__(self, ip, timeout=10):
        super().__init__()
        self.ip = ip
        self.timeout = timeout
        self.cap = None

    def run(self):
        def open_camera(event):
            try:
                self.cap = cv2.VideoCapture(self.ip)
                if self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        event.set()
            except Exception as e:
                print(f"Error opening camera: {e}")

        event = Event()
        thread = Thread(target=open_camera, args=(event,))
        thread.start()
        event.wait(self.timeout)  # Wait for the event to be set or timeout

        if not event.is_set() or self.cap is None or not self.cap.isOpened():
            self.connection_status.emit(False, "Não foi possível conectar ao dispositivo.")
        else:
            self.connection_status.emit(True, "Conexão estabelecida com sucesso.")

        if self.cap:
            self.cap.release()


class ConfigurarDispositivo(QDialog):
    done_clicked = QtCore.pyqtSignal(str, str, list, dict)

    def __init__(self, name="", device="", objToFind=None, dispositivos_dict=None, alertas_dict=None, time_frame=10):
        if dispositivos_dict is None:
            dispositivos_dict = {}
        if alertas_dict is None:
            alertas_dict = {}
        if objToFind is None:
            objToFind = []
        super().__init__()
        self.setWindowIcon(QIcon(absolutePath('icons/iconBranco.png')))
        global dropdown_icon_path
        self.setStyleSheet(f"""
                       ConfigurarDispositivo {{
                           background-color: #5B5B5B;
                       }}
                       QLineEdit {{
                           background-color: #D9D9D9;
                           border: none;
                           font-size: 16px;
                           padding: 5px;
                           color: #000000;
                           margin: 0px;
                           border-radius: 10px;
                       }}
                       QLabel {{
                            font-size: 16px;
                            color: #FFFFFF;
                       }}
                       QComboBox {{
                            font-size: 15px;
                            background-color: #D9D9D9;
                            color: #000000;
                            border: none;
                            border-radius: 10px;
                            padding: 5px;
                        }}
                        QComboBox::drop-down {{
                            border: 0px;
                            background-color: #D9D9D9;
                            margin-right: 20px;
                        }}
                        QComboBox::down-arrow {{
                            image: url({dropdown_icon_path});
                            width: 20px;
                            height: 20px;
                        }}
                        QComboBox::item {{
                            background-color: #5B5B5B;
                            color: #FFFFFF;
                        }}
                        QComboBox::item:!selected {{
                            background-color: #D9D9D9;
                            color: #000000;
                        }}
                        QComboBox:disabled {{
                            background-color: #CCCCCC; /* Light gray background */
                            color: #808080; /* Light gray text color */
                        }}
                        QCheckBox::indicator:disabled {{
                            background-color: #CCCCCC; /* Light gray */
                        }}
                        QListWidget {{
                            font-size: 14px;
                            border-radius: 10px;
                        }}
                        QListWidget::item {{
                            height: 20px;
                        }}
                        QListView::item:selected{{
                            background-color: #D9D9D9;
                            color: #000000;
                        }}
                        QMessageBox {{
                             background-color: #5B5B5B;
                             color: #000000;
                        }}
                        QMessageBox QPushButton {{
                            border: none;
                            border-radius: 10px;
                            font-size: 16px;
                            padding: 10px;
                            color: #FFFFFF;
                            background-color: #292929;
                        }}
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
        self.tempo_alertas = {}

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
        self.test_connection_label = QLabel("A testar a conexão...")
        self.testButton = DarkButton("Test connection")
        self.testButton.clicked.connect(self.test_connection)

        self.layout_objetos = QHBoxLayout()
        self.layout_selected = QVBoxLayout()
        self.layout_availave = QVBoxLayout()

        self.button_next = LightButton("")
        self.button_next.setIcon(QIcon(absolutePath("icons/arrow_right.png")))
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
        layout.addWidget(self.test_connection_label)
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
        self.test_connection_label.hide()
        if device != "":
            self.nomeLineEdit.setText(name)
            print("device", device)
            if "http" in str(device) or "rtsp" in str(device):
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
        self.button_prev.setIcon(QIcon(absolutePath("icons/arrow_left.png")))
        self.button_prev.setIconSize(QSize(50, 50))
        self.button_prev.setFixedSize(50, 50)
        self.button_prev.clicked.connect(self.previous_page)
        self.objetos_alerta = QListWidget()
        self.objetos_alerta.setSelectionMode(QAbstractItemView.NoSelection)
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
            "Nesta janela pode definir o tempo de inatividade para cada objeto antes que um alerta seja emitido. A unidade a 0 significa que o objeto não emite alerta")
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

    def test_connection(self):
        ip = self.ip_line_edit.text().strip()
        self.testButton.setEnabled(False)
        self.test_connection_label.show()
        self.camera_thread = ConnectionThread(ip, timeout=10)
        self.camera_thread.connection_status.connect(self.handle_connection_status)
        self.camera_thread.start()

    def handle_connection_status(self, success, message):
        self.test_connection_label.hide()
        if success:
            QMessageBox.information(self, "Sucesso", message)
        else:
            QMessageBox.warning(self, "Erro", message)
        self.testButton.setEnabled(True)

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
                self.tempo_alertas[item.text()] = 0
        self.repaint()

    def buttonRemovef(self):
        selected_items = self.objectsSelected.selectedItems()
        for item in selected_items:
            if self.objectsSelected.findItems(item.text(), Qt.MatchExactly):
                self.objectsSelected.takeItem(self.objectsSelected.row(item))
                self.availableObjects.addItem(item.text())
                self.class_names.append(item.text())
                self.class_names_selected.remove(item.text())
                if item.text() in self.tempo_alertas:
                    del self.tempo_alertas[item.text()]
                for i in range(self.objetos_alerta.count()):
                    list_item = self.objetos_alerta.item(i)
                    custom_widget = self.objetos_alerta.itemWidget(list_item)
                    if custom_widget.get_classe() == item.text():
                        self.objetos_alerta.takeItem(i)
                        break
                if item.text() in self.class_alertas:
                    self.class_alertas.remove(item.text())
        self.availableObjects.sortItems()
        self.repaint()

    def filter_list_selected(self):
        search_text = self.search_bar_selected.text().lower()
        self.objectsSelected.clear()
        filtered_items = [item for item in self.class_names_selected if search_text in item.lower()]
        self.objectsSelected.addItems(sorted(filtered_items))

    def on_done_clicked(self):
        name = self.nomeLineEdit.text()
        if name == "":
            QMessageBox.warning(self, "Erro", "Introduza um nome para o dispositivo.")
            return
        if self.checkBox_IP.isChecked():
            device = self.ip_line_edit.text().strip()
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

        for i in range(self.objetos_alerta.count()):
            list_item = self.objetos_alerta.item(i)
            custom_widget = self.objetos_alerta.itemWidget(list_item)
            self.tempo_alertas[custom_widget.get_classe()] = custom_widget.get_time()
        self.done_clicked.emit(name, device, selected_items, self.tempo_alertas)
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
        if has_dispositivos:
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


class EmailDialog(QDialog):
    def __init__(self, parent=None, emails=None):
        super(EmailDialog, self).__init__(parent)
        if emails is None:
            emails = []
        self.setWindowTitle("Gerir Emails")
        self.setStyleSheet("background-color: #5B5B5B; color: white; font-size: 16px;")
        self.parent = parent
        self.layout = QVBoxLayout(self)

        self.email_list_label = QLabel("Emails:", self)
        self.layout.addWidget(self.email_list_label)

        self.email_list = QListWidget(self)
        self.email_list.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.email_list)

        self.email_input_label = QLabel("Email:", self)
        self.layout.addWidget(self.email_input_label)

        self.email_input = QLineEdit(self)
        self.email_input.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.email_input)

        buttons_layout = QHBoxLayout()

        self.add_button = DarkButton("Adicionar Email")
        self.add_button.clicked.connect(self.add_email)
        buttons_layout.addWidget(self.add_button)

        self.remove_button = DarkButton("Remover Email")
        self.remove_button.clicked.connect(self.remove_email)
        buttons_layout.addWidget(self.remove_button)

        self.layout.addLayout(buttons_layout)
        if emails:
            self.email_list.addItems(emails)

    def add_email(self):
        email = self.email_input.text()
        if email:
            self.email_list.addItem(email)
            self.email_input.clear()

    def remove_email(self):
        selected_items = self.email_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.email_list.takeItem(self.email_list.row(item))

    def closeEvent(self, a0):
        self.send_emails()
        super().closeEvent(a0)

    def send_emails(self):
        emails = []
        for index in range(self.email_list.count()):
            displayed_email = self.email_list.item(index).text()
            emails.append(displayed_email)
        self.parent.email_changed(emails)


global_country_codes = []


class PhoneDialog(QDialog):
    def __init__(self, parent=None, phone_numbers=None):
        super(PhoneDialog, self).__init__(parent)
        if phone_numbers is None:
            phone_numbers = []
        self.setWindowTitle("Adicionar Números de Telemovel")
        self.setStyleSheet("background-color: #5B5B5B; color: white; font-size: 16px;")
        self.parent = parent
        self.layout = QVBoxLayout(self)

        self.phone_list_label = QLabel("Telemovel:", self)
        self.layout.addWidget(self.phone_list_label)

        self.phone_list = QListWidget(self)
        self.phone_list.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.phone_list)

        hbox = QHBoxLayout()

        self.phone_input_label = QLabel("Telefone:", self)
        hbox.addWidget(self.phone_input_label)

        self.country_code_selector = QComboBox(self)
        global dropdown_icon_path
        combo_style = f"""
                    QComboBox {{
                        font-size: 16px;
                        background-color: #D9D9D9;
                        color: #000000;
                        border: none;
                        border-radius: 5px;
                        padding: 2px;
                    }}
                    QComboBox::drop-down {{
                        border: 0px;
                        background-color: #D9D9D9;
                        margin-right: 20px;
                    }}
                    QComboBox::down-arrow {{
                        image: url({dropdown_icon_path});
                        width: 10px;
                        height: 10px;
                    }}
                    QComboBox::item {{
                        background-color: #5B5B5B;
                        color: #FFFFFF;
                    }}
                    QComboBox::item:!selected {{
                        background-color: #D9D9D9;
                        color: #000000;
                    }}
                """
        self.country_code_selector.setStyleSheet(combo_style)

        if not global_country_codes:
            self.populate_country_codes()
        else:
            self.country_code_selector.addItems(global_country_codes)
        self.country_code_selector.setCurrentIndex(68)
        self.country_code_selector.setFixedWidth(100)  # Set a fixed width for the combobox
        hbox.addWidget(self.country_code_selector)

        self.phone_input = QLineEdit(self)
        self.phone_input.setStyleSheet("font-size: 16px;")
        hbox.addWidget(self.phone_input)

        self.layout.addLayout(hbox)

        buttons_layout = QHBoxLayout()

        self.add_button = DarkButton("Adicionar Número de Telefone")
        self.add_button.clicked.connect(self.add_phone_number)
        buttons_layout.addWidget(self.add_button)

        self.remove_button = DarkButton("Remover Número de Telefone")
        self.remove_button.clicked.connect(self.remove_phone_number)
        buttons_layout.addWidget(self.remove_button)

        self.layout.addLayout(buttons_layout)

        if phone_numbers:
            self.phone_list.addItems(phone_numbers)

    def populate_country_codes(self):
        global global_country_codes
        country_codes = []
        combo_items = []
        for region_code in phonenumbers.SUPPORTED_REGIONS:
            country_code = phonenumbers.country_code_for_region(region_code)
            countre_name = phonenumbers.phonenumberutil.region_code_for_country_code(country_code)
            if country_code not in country_codes:
                combo_items.append(f"+{country_code} {countre_name}")
            country_codes.append(country_code)
        combo_items.sort()
        global_country_codes = combo_items
        self.country_code_selector.addItems(combo_items)

    def add_phone_number(self):
        phone_number = self.phone_input.text()
        country_code = self.country_code_selector.currentText().split(' ')[0]
        if phone_number:
            self.phone_list.addItem(f"{country_code} {phone_number}")
            self.phone_input.clear()

    def remove_phone_number(self):
        selected_items = self.phone_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.phone_list.takeItem(self.phone_list.row(item))

    def closeEvent(self, a0):
        self.send_phone_numbers()
        super().closeEvent(a0)

    def send_phone_numbers(self):
        phone_numbers = []
        for index in range(self.phone_list.count()):
            displayed_phone_number = self.phone_list.item(index).text()
            phone_numbers.append(displayed_phone_number)
        self.parent.phone_numbers_changed(phone_numbers)


class ToastNotification(QWidget):
    active_toasts = []

    def __init__(self, title, message, duration=2000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.title = title
        self.message = message
        self.duration = duration

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Main container widget with background color
        container = QWidget()
        container.setStyleSheet("background-color: #F7CA00; border-radius: 10px;")
        container_layout = QVBoxLayout(container)

        # Horizontal layout for title and icon
        title_layout = QHBoxLayout()

        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("color: #292929; font-weight: bold; padding-bottom: 5px;")
        title_layout.addWidget(self.title_label)

        # Warning icon label
        warning_pixmap = QPixmap(absolutePath('icons/warning.png'))
        self.warning_icon_label = QLabel()
        self.warning_icon_label.setPixmap(
            warning_pixmap.scaledToWidth(16, Qt.SmoothTransformation))  # Adjust size as needed
        self.warning_icon_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_layout.addWidget(self.warning_icon_label)

        container_layout.addLayout(title_layout)

        # Message label
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet("color: #292929; padding: 10px;")
        container_layout.addWidget(self.message_label)

        layout.addWidget(container)
        self.setLayout(layout)
        self.adjustSize()

        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_fade_out)

    def start_fade_out(self):
        self.opacity_animation.setDirection(QPropertyAnimation.Backward)
        self.opacity_animation.start()
        self.opacity_animation.finished.connect(self.close)

    def showNotification(self):
        if not self.isVisible():
            self.opacity_animation.setDirection(QPropertyAnimation.Forward)
            self.opacity_animation.start()
            self.timer.start(self.duration)
            self.show()

            ToastNotification.active_toasts.append(self)
            self.move_to_free_space()

    def move_to_free_space(self):
        parent_rect = self.parent().geometry()
        bottom_margin = 10
        x_margin = 10
        y = parent_rect.bottom() - bottom_margin - self.height()
        x = parent_rect.right() - x_margin - self.width()

        for toast in ToastNotification.active_toasts:
            if toast is not self:
                current_geometry = QRect(toast.geometry())
                if current_geometry.intersects(QRect(QPoint(x, y), self.sizeHint())):
                    y -= current_geometry.height() + bottom_margin

        self.move(QPoint(x, y))

    def closeEvent(self, event):
        if self in ToastNotification.active_toasts:
            ToastNotification.active_toasts.remove(self)
        event.accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(absolutePath('icons/iconBranco.png')))
        self.setWindowTitle("SafeSight")
        self.setGeometry(500, 100, 1280, 720)
        self.setStyleSheet("""
                QMenuBar {
                    background-color: #1c1c1c;
                    color: white;
                }
                QMenuBar::item {
                    background-color: #1c1c1c;
                    color: white;
                }
                QMenuBar::item:selected {
                    background-color: #373737;
                }
                QMenu {
                    background-color: #1c1c1c;
                    color: white;
                }
                QMenu::item {
                    background-color: #1c1c1c;
                    color: white;
                }
                QMenu::item:selected {
                    background-color: #373737;
                }
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

        # Adicionando a barra de menu
        self.menu_bar = QMenuBar(self)
        file_menu = self.menu_bar.addMenu('File')
        preferences_menu = self.menu_bar.addMenu('Preferences')
        help_menu = self.menu_bar.addMenu('Help')
        self.phone_numbers = []
        self.emails = []

        # Adicionando ações ao menu File
        new_action = QAction('New', self)
        new_action.triggered.connect(self.new_file)
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_files)
        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_files)
        save_as_action = QAction('Save as', self)
        save_as_action.triggered.connect(self.save_as_files)
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addAction(exit_action)

        # Adicionando ações ao menu Preferences
        email_action = QAction('Emails to send alert', self)
        email_action.triggered.connect(self.email_config)
        phone_action = QAction('Phone numbers to send alert', self)
        phone_action.triggered.connect(self.phone_config)

        preferences_menu.addAction(email_action)
        preferences_menu.addAction(phone_action)

        main_layout.setMenuBar(self.menu_bar)

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
        self.dispositivos_window = DispositivosWindow(self)
        self.dispositivos_window.alertReceived.connect(self.alert_notification)
        self.alertas_window = AlertasWindow()
        self.stacked_layout.addWidget(self.dispositivos_window)
        self.stacked_layout.addWidget(self.alertas_window)
        main_layout.addLayout(self.stacked_layout)
        self.file_name = None
        self.devices_hash = None

        # Definindo a página inicial como Dispositivos
        self.show_dispositivos()

    def alert_notification(self, message):
        toast = ToastNotification("ALERTA GERADO", message, 5000, self)
        if self.stacked_layout.currentIndex() == 1:
            self.alertas_window.carregar_alertas()
        toast.showNotification()

    def show_dispositivos(self):
        self.stacked_layout.setCurrentIndex(0)
        self.dispositivos_button.setStyleSheet(
            "background-color: #292929; border: none; font-size: 20px; padding:10px 0")
        self.alertas_button.setStyleSheet(
            "background-color: #5B5B5B; border: none; border-bottom-left-radius:20%; font-size: 20px; padding:10px 0")

    def show_alertas(self):
        self.alertas_window.carregar_alertas()
        self.stacked_layout.setCurrentIndex(1)
        self.dispositivos_button.setStyleSheet(
            "background-color: #5B5B5B; border: none; border-bottom-right-radius:20%; font-size: 20px; padding:10px 0")
        self.alertas_button.setStyleSheet("background-color: #292929; border: none; font-size: 20px; padding:10px 0")

    def new_file(self):
        data = self.dispositivos_window.to_dict()
        data['emails'] = self.emails
        data['phone_numbers'] = self.phone_numbers
        if len(all_dispositivos_widget) > 0 and (
                self.file_name is None or self.devices_hash != self.hash_dict(data)):
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Message")
            if self.file_name is None:
                msg_box.setText("Do you want to save changes?")
            else:
                msg_box.setText("Do you want to save changes to " + os.path.basename(self.file_name) + "?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setStyleSheet("""
                                        QMessageBox {
                                            background-color: #4e4e4e; /* Light background color */
                                        }
                                        QMessageBox QLabel {
                                            color: white;
                                        }
                                        QAbstractButton {
                                            background-color: #292929; /* Darker color for buttons */
                                            color: white;
                                            border-radius: 10px; /* Rounded borders */
                                            padding: 5px 10px;
                                        }
                                        QAbstractButton:hover {
                                            background-color: #3d3d3d; /* Slightly lighter on hover */
                                        }
                                        StandardButton {
                                            background-color: #292929; /* Darker color for buttons */
                                            color: white;
                                            border-radius: 10px; /* Rounded borders */
                                            padding: 5px 10px;
                                        }
                                        StandardButton:hover {
                                            background-color: #3d3d3d;
                                        }
                                        QPushButton {
                                            background-color: #292929;
                                            color: white;
                                            border-radius: 10px;
                                            padding: 5px 10px;
                                        }
                                        QPushButton:hover {
                                            background-color: #3d3d3d;
                                        }

                                    """)

            reply = msg_box.exec()
            if reply == QMessageBox.Yes:
                if self.file_name is None:
                    self.save_as_files()
                    if self.file_name is not None:
                        event.ignore()
                    for widget in all_dispositivos_widget[:]:
                        widget.remove_button_action()
                else:
                    self.save_files()
                    for widget in all_dispositivos_widget[:]:
                        widget.remove_button_action()
                self.file_name = None
            elif reply == QMessageBox.No:
                for widget in all_dispositivos_widget[:]:
                    widget.remove_button_action()
                self.file_name = None
            elif reply == QMessageBox.Cancel:
                return
        else:
            for widget in all_dispositivos_widget[:]:
                widget.remove_button_action()
            self.file_name = None
    def open_files(self):
        global all_dispositivos_widget
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            for widget in all_dispositivos_widget[:]:
                widget.remove_button_action()
            with open(file_name, 'r') as file:
                data = json.load(file)
                try:
                    self.dispositivos_window.from_dict(data)
                    self.file_name = file_name
                    self.email_changed(data["emails"])
                    self.phone_numbers_changed(data["phone_numbers"])
                    self.devices_hash = self.hash_dict(data)
                except:
                    QMessageBox.critical(self, "Erro", "Erro ao carregar os dispositivos do ficheiro")

    def save_files(self):
        if self.file_name:
            data = self.dispositivos_window.to_dict()
            data['emails'] = self.emails
            data['phone_numbers'] = self.phone_numbers
            with open(self.file_name, 'w') as file:
                json.dump(data, file, indent=4)
            self.devices_hash = self.hash_dict(data)
        else:
            self.save_as_files()

    def save_as_files(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            with open(file_name, 'w') as file:
                data = self.dispositivos_window.to_dict()
                data['emails'] = self.emails
                data['phone_numbers'] = self.phone_numbers
                json.dump(data, file)
                self.devices_hash = self.hash_dict(data)

    def email_config(self):
        email_dialog = EmailDialog(self, self.emails)
        email_dialog.exec_()

    def phone_config(self):
        phone_dialog = PhoneDialog(self, self.phone_numbers)
        phone_dialog.exec_()

    def phone_numbers_changed(self, phone_numbers):
        phone_numbers = [phone_number.replace(' ', '') for phone_number in phone_numbers]
        self.phone_numbers = phone_numbers
        yoloScript.phone_numbers_to_send_alert(phone_numbers)

    def email_changed(self, emails):
        self.emails = emails
        yoloScript.emails_to_send_alert(emails)

    def closeEvent(self, event):
        data = self.dispositivos_window.to_dict()
        data['emails'] = self.emails
        data['phone_numbers'] = self.phone_numbers
        if len(all_dispositivos_widget) > 0 and (
                self.file_name is None or self.devices_hash != self.hash_dict(data)):
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Message")
            if self.file_name is None:
                msg_box.setText("Do you want to save changes?")
            else:
                msg_box.setText("Do you want to save changes to " + os.path.basename(self.file_name) + "?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msg_box.setStyleSheet("""
                            QMessageBox {
                                background-color: #4e4e4e; /* Light background color */
                            }
                            QMessageBox QLabel {
                                color: white;
                            }
                            QAbstractButton {
                                background-color: #292929; /* Darker color for buttons */
                                color: white;
                                border-radius: 10px; /* Rounded borders */
                                padding: 5px 10px;
                            }
                            QAbstractButton:hover {
                                background-color: #3d3d3d; /* Slightly lighter on hover */
                            }
                            StandardButton {
                                background-color: #292929; /* Darker color for buttons */
                                color: white;
                                border-radius: 10px; /* Rounded borders */
                                padding: 5px 10px;
                            }
                            StandardButton:hover {
                                background-color: #3d3d3d;
                            }
                            QPushButton {
                                background-color: #292929;
                                color: white;
                                border-radius: 10px;
                                padding: 5px 10px;
                            }
                            QPushButton:hover {
                                background-color: #3d3d3d;
                            }
                                
                        """)

            reply = msg_box.exec()
            if reply == QMessageBox.Yes:
                if self.file_name is None:
                    self.save_as_files()
                    if self.file_name is not None:
                        event.ignore()
                    for widget in all_dispositivos_widget[:]:
                        widget.remove_button_action()
                    event.accept()
                else:
                    self.save_files()
                    for widget in all_dispositivos_widget[:]:
                        widget.remove_button_action()
                    event.accept()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.No:
                for widget in all_dispositivos_widget[:]:
                    widget.remove_button_action()
                self.dispositivos_window.queue.put(-1)
                event.accept()
        elif self.file_name is not None and self.devices_hash == self.hash_dict(self.dispositivos_window.to_dict()):
            for widget in all_dispositivos_widget[:]:
                widget.remove_button_action()
            event.accept()
        for widget in all_dispositivos_widget[:]:
            print("Aqui")
            widget.remove_button_action()
        self.dispositivos_window.queue.put(-1)

    @staticmethod
    def hash_dict(d):
        dict_str = json.dumps(d, sort_keys=True)
        hash_obj = hashlib.sha256(dict_str.encode())
        return hash_obj.hexdigest()

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
                   color: #ffffff;
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
    app.setWindowIcon(QIcon(absolutePath('icons/iconBranco.png')))
    app.exec_()
    print('Closing Window...')
