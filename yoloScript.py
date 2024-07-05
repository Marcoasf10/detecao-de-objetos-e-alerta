import math
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread, Lock
import cv2
import numpy as np
from ultralytics import YOLO
import pickle
from twilio.rest import Client
import psutil
import matplotlib.pyplot as plt
import shutil
import datetime

import App

modelo = 'yolov8s'
model = YOLO(modelo)
retrieved_frames = {}
predicted_frames = {}
stop_dict = {}
delay_dict = {}
obj_find_dict = {}
alert_time_dict = {}
alerta_tempo_start = {}
delete_devices = []
obj_find_lock = Lock()
stop_lock = Lock()
retrived_frames_lock = Lock()
predicted_frames_lock = Lock()
delay_lock = Lock()
alert_time_lock = Lock()
alerta_tempo_start_lock = Lock()
delete_devices_lock = Lock()
cpu_usage = []
memory_usage = []
cpu_usage_lock = Lock()
memory_usage_lock = Lock()
cpu_inicial = psutil.cpu_percent()
memory_inicial = psutil.virtual_memory().percent
threads = []
grafico_made = True
grafico_made_lock = Lock()
emails_alert = []
phone_numbers_alert = []
emails_alert_lock = Lock()
phone_numbers_alert_lock = Lock()
id_ultimo_alerta = 0

def addDispositivoToPredict(device, classes, lista_alertas, queue, delay,graphs=False):
    global grafico_made
    listObjToFind = []
    for classe in classes:
        listObjToFind.append(list(model.names.values()).index(classe))
    change_alert_time(device, lista_alertas)
    thread = Thread(target=predict, args=(device, listObjToFind, queue, delay, lista_alertas,graphs))
    threads.append(thread)
    thread.start()
    thread.join()
    cv2.destroyAllWindows()
    with grafico_made_lock:
        if grafico_made:
            #graficoPerformance(cpu_usage, memory_usage)
            grafico_made = False
def distance(x1, x2, y1, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def diferenceImgs(img1, img2):
    h, w = img1.shape
    diff = cv2.subtract(img1, img2)
    err = np.sum(diff ** 2)
    mse = err / (float(h * w))
    return mse, diff


def predict(device, listObjToFind, queue, delay, lista_alertas, graphs):
    global predicted_frames
    global stop_dict
    global delay_dict
    global obj_find_dict
    global alerta_tempo_start
    global alert_time_dict
    canto1Mapper = dict()
    canto2Mapper = dict()
    x1_coordinates = []
    y1_coordinates = []
    x2_coordinates = []
    y2_coordinates = []
    distanciaCanto1Lista = []
    distanciaCanto2Lista = []
    confiancas = []
    local_model = YOLO(modelo)
    cap = cv2.VideoCapture(device)
    i = 0
    margem = 4
    last_frame = None
    error = 0
    stop = False
    alerta_filename = App.absolutePath('alertas.bin')

    if 'http' in str(device) or 'rtsp' in str(device):
        device_folder = device.split('/')[2].replace('.', '_').replace(':', '_')
    else:
        device_folder = str(device)
    if not os.path.exists(f'frames/{device_folder}'):
        os.makedirs(f'frames/{device_folder}')
    while True:
        # Verifica se o dispositivo foi removido
        with delete_devices_lock:
            if device in delete_devices:
                break
        # Verifica se o dispositivo foi parado
        with stop_lock:
            if device in stop_dict:
                stop = stop_dict[device]
        # Se o dispositivo foi parado, fecha a câmara
        if stop:
            if cap.isOpened():
                cap.release()
            time.sleep(0.5)
            continue
        if not cap.isOpened():
            cap = cv2.VideoCapture(device)
        # dar tempo para câmara inicializar
        with delay_lock:
            if device in delay_dict:
                delay = delay_dict[device]
        with obj_find_lock:
            if device in obj_find_dict:
                listObjToFind = []
                for classe in list(obj_find_dict[device]):
                    listObjToFind.append(list(model.names.values()).index(classe))
        if last_frame is None:
            time.sleep(0.1)
        start_time_predict = time.time()
        grabbed = cap.grab()
        if not grabbed:
            i = 0
            while not grabbed and i < 20:
                time.sleep(0.1)
                grabbed = cap.grab()
                i += 1
                with delete_devices_lock:
                    if device in delete_devices:
                        break
            if not grabbed:
                cap.release()
                cap = cv2.VideoCapture(device)
                print(device)
                print("Error: Unable to grab frame from webcam.")
                continue
        ret, frame = cap.retrieve()
        if not ret:
            print("Error: Unable to retrieve frame from webcam.")
            continue
        if last_frame is not None:
            img1 = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            error, diff = diferenceImgs(img1, img2)
            print("Error diference: ", error)
        # if img not equal last img:
        if last_frame is None or (last_frame is not None and error > 0):
            results = local_model.track(frame, save=True, project=f'frames/{device_folder}', exist_ok=True, classes=listObjToFind,
                                        stream=False, persist=True, imgsz=1280, conf=0.3)
            last_frame = frame
        with delete_devices_lock:
            if device in delete_devices:
                break
        with predicted_frames_lock:
            try:
                predicted_frames[device] = cv2.imread(f'frames/{device_folder}/track/image0.jpg')
            except Exception as e:
                print(f"Error: {e}")
                continue
            queue.put(predicted_frames)
        for r in results:
            boxes = r.boxes.cpu().numpy()
            if not boxes or boxes.id is None or boxes.id.size == 0:
                i += 1
                continue
            if boxes:
                for f in range(boxes.id.size):
                    id = int(boxes.id[f])
                    classe_obj = local_model.names[boxes.cls[f]]
                    if device not in alerta_tempo_start or id not in alerta_tempo_start[device]:
                        with alerta_tempo_start_lock:
                            if device not in alerta_tempo_start:
                                alerta_tempo_start[device] = {}
                            if id not in alerta_tempo_start[device]:
                                alerta_tempo_start[device][id] = {}
                            for classe, tempo in lista_alertas.items():
                                alerta_tempo_start[device][id][classe] = time.time()
                    if classe_obj not in alerta_tempo_start[device][id]:
                        alerta_tempo_start[device][id][classe_obj] = time.time()
                    x1, y1, x2, y2 = boxes.xyxy[f]
                    if id not in canto1Mapper and id not in canto2Mapper:
                        canto1Mapper[id] = (x1, y1, -1)
                        canto2Mapper[id] = (x2, y2, -1)
                    canto1Mapper[id] = (x1, y1, distance(canto1Mapper[id][0], x1, canto1Mapper[id][1], y1))
                    canto2Mapper[id] = (x2, y2, distance(canto2Mapper[id][0], x2, canto2Mapper[id][1], y2))
                    if canto1Mapper[id][2] == -1 and canto2Mapper[id][2] == -1:
                        continue
                    if graphs:
                        confiancas.append(boxes.conf[0] * 100)
                        x1_coordinates.append(x1)
                        y1_coordinates.append(y1)
                        x2_coordinates.append(x2)
                        y2_coordinates.append(y2)
                        distanciaCanto1Lista.append(canto1Mapper[0][2])
                        distanciaCanto2Lista.append(canto2Mapper[0][2])
                    if canto1Mapper[id][2] <= margem and canto2Mapper[id][2] <= margem:
                        print(f"ID: {int(id)} -> Parado")
                        with alert_time_lock:
                            if classe_obj in alert_time_dict[device]:
                                tempo_alerta = alert_time_dict[device][classe_obj]
                            else:
                                continue
                        with alerta_tempo_start_lock:
                            tempo_last = alerta_tempo_start[device][id][classe_obj]
                        if time.time() - tempo_last >= tempo_alerta != 0:
                            with alerta_tempo_start_lock:
                                alerta_tempo_start[device][id][classe_obj] = time.time()
                            with predicted_frames_lock:
                                alerta = criar_alerta(device, classe_obj, predicted_frames[device], tempo_alerta, queue)
                            with open(alerta_filename, 'ab') as f:
                                pickle.dump(alerta, f)
                    else:
                        alerta_tempo_start[device][id][classe_obj] = time.time()
                        print(f"ID: {int(id)} -> Mover")
        i += 1
        # Enquanto o tempo decorrido for menor que o delay definido, continua a capturar frames
        while time.time() - start_time_predict <= delay:
            # Verifica se o dispositivo foi removido
            with delete_devices_lock:
                if device in delete_devices:
                    break
            # Verifica se o dispositivo foi parado
            with stop_lock:
                if device in stop_dict:
                    stop = stop_dict[device]
                    if stop:
                        break
            # Verifica se tempo de delay foi alterado
            with delay_lock:
                if device in delay_dict:
                    delay = delay_dict[device]
            cap.grab()
        with cpu_usage_lock:
            cpu_usage.append(psutil.cpu_percent())
        with memory_usage_lock:
            memory_usage.append(psutil.virtual_memory().percent)
    # Fechar a câmara
    cap.release()
    if graphs:
        criarGraficos(device, modelo, x1_coordinates, y1_coordinates, x2_coordinates, y2_coordinates, confiancas,
                      distanciaCanto1Lista, distanciaCanto2Lista)
    # Limpar o dicionário de alertas para o dispositivo eliminado
    with alert_time_lock:
        alert_time_dict[device] = {}
    with alerta_tempo_start_lock:
        alerta_tempo_start[device] = {}
    # Limpar o dicionário de objetos para detetar para o dispositivo eliminado
    with obj_find_lock:
        obj_find_dict[device] = {}
    # Retirar o device dos dispositivos a eliminar
    if device in delete_devices:
        with delete_devices_lock:
            delete_devices.remove(device)
    if os.path.exists(f'frames/{device_folder}'):
        # Remover a pasta e todos os ficheiros
        shutil.rmtree(f'frames/{device_folder}')


def list_available_cameras():
    devices = []
    num_devices = 0
    while True:
        try:
            cap = cv2.VideoCapture(num_devices)
            if cap.isOpened():
                print(f"Camera {num_devices}: Available")
                devices.append(num_devices)
                cap.release()
                num_devices += 1
            else:
                print(f"Camera {num_devices}: Not available")
                break
        except cv2.error as e:
            print(f"Error accessing camera {num_devices}: {e}")
            num_devices += 1
            continue
        except Exception as e:
            print(f"Unknown error: {e}")
            break
    return devices


def change_stop(device, stop):
    global stop_dict
    with stop_lock:
        stop_dict[device] = stop


def change_delay(device, delay):
    global delay_dict
    with delay_lock:
        delay_dict[device] = delay


def get_classes():
    return list(model.names.values())


def update_obj_to_find(device, obj_to_find, lista_alertas):
    global obj_find_dict
    with obj_find_lock:
        obj_find_dict[device] = obj_to_find
    change_alert_time(device, lista_alertas)


def remove_device(device):
    delete_devices.append(device)


def change_alert_time(device, time_dict):
    alert_time_dict[device] = time_dict


def criar_alerta(device, classe_obj, frame, tempo_alerta, queue):
    time_struct = time.localtime(time.time())
    formatted_time = time.strftime('%d/%m/%Y', time_struct)
    if tempo_alerta >= 3600:
        hours, remainder = divmod(tempo_alerta, 3600)
        minutes, seconds = divmod(remainder, 60)
        if minutes > 0 and seconds > 0:
            tempo_alerta_str = f'{int(hours)} hora(s), {int(minutes)} minuto(s) e {int(seconds)} segundo(s)'
        elif minutes > 0 and seconds == 0:
            tempo_alerta_str = f'{int(hours)} hora(s) e {int(minutes)} minuto(s)'
        elif minutes == 0 and seconds > 0:
            tempo_alerta_str = f'{int(hours)} hora(s) e {int(seconds)} segundo(s)'
        else:
            tempo_alerta_str = f'{int(hours)} hora(s)'
    elif tempo_alerta >= 60:
        minutes, seconds = divmod(tempo_alerta, 60)
        if seconds > 0:
            tempo_alerta_str = f'{int(minutes)} minuto(s) e {int(seconds)} segundo(s)'
        tempo_alerta_str = f'{int(minutes)} minuto(s)'
    else:
        tempo_alerta_str = f'{int(tempo_alerta)} segundo(s)'

    descricao = f'Data: {formatted_time}\nO objeto: {classe_obj} está parado há {tempo_alerta_str}'
    print("Gerado ALERTA!")
    timestamp = time.time()
    alerta = Alerta(device, classe_obj, descricao, frame, timestamp, tempo_alerta)
    time_struct = time.localtime(timestamp)
    data = time.strftime('%d/%m/%Y %H:%M:%S', time_struct)
    subject = "Alerta gerado pelo sistema de monitorização.\nDispositivo: " + str(
        device) + "\n" + "Classe: " + classe_obj + "\n" + "Data: " + data + "\n" + "Tempo Parado: " + tempo_alerta_str + "\n"
    alerta_notiication = "Alerta gerado pelo sistema de monitorização.\nDispositivo: " + str(
        device) + "\t" + "Classe: " + classe_obj + "\n" "Tempo Parado: " + tempo_alerta_str

    queue.put({-2: alerta_notiication})
    with emails_alert_lock:
        for email in emails_alert:
            send_email(f'Alerta!! {classe_obj} está parado há {tempo_alerta_str}', subject, email)
    with phone_numbers_alert_lock:
        for phone_number in phone_numbers_alert:
            print(phone_number)
            #send_sms(phone_number, subject)

    return alerta


def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    from_email = "safesight9195@gmail.com"
    password = "gvwu kvox ralt vmeu"
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the fakeSMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        print("Email sent successfully!")
        server.quit()
    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")


def send_sms(numero, mensagem):
    account_id = "ACbb0292084f73400fbeed6a065c40952a"
    auth_token = "14ce372723bef16b1b2ce8cd2af91858"
    client = Client(account_id, auth_token)
    client.messages.create(
        body=mensagem,
        from_='+14237193549',
        to=numero
    )

def emails_to_send_alert(emails):
    global emails_alert
    with emails_alert_lock:
        emails_alert = emails

def phone_numbers_to_send_alert(phone_numbers):
    global phone_numbers_alert
    with phone_numbers_alert_lock:
        phone_numbers_alert = phone_numbers

def graficoPerformance(cpu_usage, memory_usage):
    fig, axs = plt.subplots(1, 2, figsize=(15, 10))
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H-%M-%S")
    cpu_usage_array = np.array(cpu_usage)
    memory_usage_array = np.array(memory_usage)

    # Gráfico para a distância entre os cantos 1
    axs[0].plot(range(len(cpu_usage_array)), cpu_usage_array, label='CPU Usage', color='blue')
    axs[0].axhline(y=np.mean(cpu_usage_array), color='grey', linestyle='--', label='CPU Usage Mean')
    axs[0].text(0.5, 0.9, f'Inicial CPU (%): {cpu_inicial:.2f}', transform=axs[0].transAxes, color='black')
    axs[0].text(0.5, 0.8, f'Max CPU Usage (%): {max(cpu_usage_array):.2f}', transform=axs[0].transAxes, color='black')
    axs[0].text(0.5, 0.7, f'Min CPU Usage (%): {min(cpu_usage_array):.2f}', transform=axs[0].transAxes, color='black')
    axs[0].text(0.5, 0.6, f'Média CPU Usage (%): {np.mean(cpu_usage_array):.2f}', transform=axs[0].transAxes,
                color='black')
    axs[0].set_title('CPU Usage (%)')
    axs[0].set_xlabel('Frame')
    axs[0].set_ylabel('Usage')
    axs[0].set_yticks(np.arange(0, 100, 10))
    axs[0].legend()

    # Gráfico para a distância entre os cantos 2
    axs[1].plot(range(len(memory_usage_array)), memory_usage_array, label='CPU Usage', color='blue')
    axs[1].axhline(y=np.mean(memory_usage_array), color='grey', linestyle='--', label='CPU Usage Mean')
    axs[1].text(0.5, 0.5, f'Inicial Memory (%): {memory_inicial:.2f}', transform=axs[1].transAxes, color='black')
    axs[1].text(0.5, 0.4, f'Max Memory usage (%): {max(memory_usage_array):.2f}', transform=axs[1].transAxes,
                color='black')
    axs[1].text(0.5, 0.3, f'Min Memory usage (%): {min(memory_usage_array):.2f}', transform=axs[1].transAxes,
                color='black')
    axs[1].text(0.5, 0.2, f'Média Memory usage (%): {np.mean(memory_usage_array):.2f}', transform=axs[1].transAxes,
                color='black')
    axs[1].set_title('Memory Usage (%)')
    axs[1].set_xlabel('Frame')
    axs[1].set_ylabel('Usage')
    axs[1].set_yticks(np.arange(0, 100, 10))
    axs[1].legend()
    plt.suptitle(f'Teste de stress camera 10 segundos', fontsize=16)
    plt.tight_layout()
    output_filename = f'graficosTestes/performanceGraph_MAX_10segundos_{timestamp}_{modelo}.png'
    plt.savefig(output_filename)
    plt.show()

class Alerta:
    def __init__(self, device, classe, descricao, photo, date, tempo_alerta):
        global id_ultimo_alerta
        id_ultimo_alerta += 1
        self.id = id_ultimo_alerta
        self.device = device
        self.classe = classe
        self.descricao = descricao
        self.photo = photo
        self.date = date
        self.tempo_alerta = tempo_alerta

    def get_id(self):
        return self.id
    def get_device(self):
        return self.device

    def get_classe(self):
        return self.classe

    def get_descricao(self):
        return self.descricao

    def get_photo(self):
        return self.photo

    def get_date(self):
        return self.date

    def get_tempo_alerta(self):
        return self.tempo_alerta

def criarGraficos(device, modelo, x1_coordinates, y1_coordinates, x2_coordinates, y2_coordinates, confiancas,
                  distanciaCanto1Lista, distanciaCanto2Lista):
    x1_coordinates = np.array(x1_coordinates)
    y1_coordinates = np.array(y1_coordinates)
    x2_coordinates = np.array(x2_coordinates)
    y2_coordinates = np.array(y2_coordinates)
    canto1Coordenadas = np.array(distanciaCanto1Lista)
    canto2Coordenadas = np.array(distanciaCanto2Lista)

    x1_std = np.std(x1_coordinates)
    y1_std = np.std(y1_coordinates)
    x2_std = np.std(x2_coordinates)
    y2_std = np.std(y2_coordinates)
    canto1Coordenadas_std = np.std(canto1Coordenadas)
    canto2Coordenadas_std = np.std(canto2Coordenadas)

    x1_max = np.max(x1_coordinates) - np.mean(x1_coordinates)
    y1_max = np.max(y1_coordinates) - np.mean(y1_coordinates)
    x2_max = np.max(x2_coordinates) - np.mean(x2_coordinates)
    y2_max = np.max(y2_coordinates) - np.mean(y2_coordinates)
    canto1_max = np.max(canto1Coordenadas) - np.mean(canto1Coordenadas)
    canto2_max = np.max(canto2Coordenadas) - np.mean(canto2Coordenadas)

    x1_min = np.min(x1_coordinates) - np.mean(x1_coordinates)
    y1_min = np.min(y1_coordinates) - np.mean(y1_coordinates)
    x2_min = np.min(x2_coordinates) - np.mean(x2_coordinates)
    y2_min = np.min(y2_coordinates) - np.mean(y2_coordinates)
    canto1_min = np.min(canto1Coordenadas) - np.mean(canto1Coordenadas)
    canto2_min = np.min(canto2Coordenadas) - np.mean(canto2Coordenadas)

    x1_max_dev = x1_max if x1_max > x1_min else x1_min
    y1_max_dev = y1_max if y1_max > y1_min else y1_min
    x2_max_dev = x2_max if x2_max > x2_min else x2_min
    y2_max_dev = y2_max if y2_max > y2_min else y2_min
    canto1_max_dev = canto1_max if canto1_max > canto1_min else canto1_min
    canto2_max_dev = canto2_max if canto2_max > canto2_min else canto2_min
    # Criando subplots
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    # Gráfico para x1
    axs[0, 0].plot(range(len(x1_coordinates)), x1_coordinates, label='x1', color='blue')
    axs[0, 0].axhline(y=np.mean(x1_coordinates), color='grey', linestyle='--', label='x1 Mean')
    axs[0, 0].text(0.5, 0.9, f'Std of x1: {x1_std:.2f}', transform=axs[0, 0].transAxes, color='black')
    axs[0, 0].text(0.5, 0.8, f'Max dev of x1: {x1_max_dev:.2f}', transform=axs[0, 0].transAxes, color='black')
    axs[0, 0].set_title('x1 Coordinate over Time')
    axs[0, 0].set_xlabel('Frame')
    axs[0, 0].set_ylabel('Coordinate Value')
    axs[0, 0].set_yticks(np.arange(round(min(x1_coordinates)) - 10, round(max(x1_coordinates)) + 10, 1))
    axs[0, 0].legend()

    # Gráfico para y1
    axs[0, 1].plot(range(len(y1_coordinates)), y1_coordinates, label='y1', color='red')
    axs[0, 1].axhline(y=np.mean(y1_coordinates), color='grey', linestyle='--', label='y1 Mean')
    axs[0, 1].text(0.5, 0.9, f'Std of y1: {y1_std:.2f}', transform=axs[0, 1].transAxes, color='black')
    axs[0, 1].text(0.5, 0.8, f'Max dev of y1: {y1_max_dev:.2f}', transform=axs[0, 1].transAxes, color='black')
    axs[0, 1].set_title('y1 Coordinate over Time')
    axs[0, 1].set_xlabel('Frame')
    axs[0, 1].set_ylabel('Coordinate Value')
    axs[0, 1].set_yticks(np.arange(round(min(y1_coordinates)) - 10, round(max(y1_coordinates)) + 10, 1))
    axs[0, 1].legend()

    # Gráfico para x2
    axs[1, 0].plot(range(len(x2_coordinates)), x2_coordinates, label='x2', color='green')
    axs[1, 0].axhline(y=np.mean(x2_coordinates), color='grey', linestyle='--', label='x2 Mean')
    axs[1, 0].text(0.5, 0.9, f'Std of x2: {x2_std:.2f}', transform=axs[1, 0].transAxes, color='black')
    axs[1, 0].text(0.5, 0.8, f'Max Dev of x2: {x2_max_dev:.2f}', transform=axs[1, 0].transAxes, color='black')
    axs[1, 0].set_title('x2 Coordinate over Time')
    axs[1, 0].set_xlabel('Frame')
    axs[1, 0].set_ylabel('Coordinate Value')
    axs[1, 0].set_yticks(np.arange(round(min(x2_coordinates)) - 10, round(max(x2_coordinates)) + 10, 1))
    axs[1, 0].legend()

    # Gráfico para y2
    axs[1, 1].plot(range(len(y2_coordinates)), y2_coordinates, label='y2', color='magenta')
    axs[1, 1].axhline(y=np.mean(y2_coordinates), color='grey', linestyle='--', label='y2 Mean')
    axs[1, 1].text(0.5, 0.9, f'Std of y2: {y2_std:.2f}', transform=axs[1, 1].transAxes, color='black')
    axs[1, 1].text(0.5, 0.8, f'Max Dev of y2: {y2_max_dev:.2f}', transform=axs[1, 1].transAxes, color='black')
    axs[1, 1].set_title('y2 Coordinate over Time')
    axs[1, 1].set_xlabel('Frame')
    axs[1, 1].set_ylabel('Coordinate Value')
    axs[1, 1].set_yticks(np.arange(round(min(y2_coordinates)) - 10, round(max(y2_coordinates)) + 10, 1))
    axs[1, 1].legend()

    plt.tight_layout()
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H-%M-%S")

    output_filename = f'graficosTestes/{device}_output_coordenadas_{timestamp}_{modelo}.png'
    plt.savefig(output_filename)
    plt.show()

    # Plotando o gráfico para as coordenadas em "confiancas"
    plt.plot(range(len(confiancas)), confiancas, label='Coordinates', color='blue')
    # Calculando e adicionando a linha de desvio padrão
    mean = np.mean(confiancas)
    plt.axhline(y=np.mean(confiancas), color='grey', linestyle='--', label='Conf Mean')
    plt.text(0.5, 0.2, f'Mean: {mean:.2f}', transform=plt.gca().transAxes, color='blue')
    plt.ylim(0, 100)

    # Adicionando legendas e rótulos
    plt.title('Confidence over time')
    plt.xlabel('Frame')
    plt.ylabel('Confidence Value')
    plt.legend()
    output_filename = f'graficosTestes/{device}_output_confianca_{timestamp}_{modelo}.png'
    plt.savefig(output_filename)
    plt.show()

    fig2, axs2 = plt.subplots(1, 2, figsize=(15, 10))

    # Gráfico para a distância entre os cantos 1
    axs2[0].plot(range(len(canto1Coordenadas)), canto1Coordenadas, label='Distância Canto 1', color='blue')
    axs2[0].axhline(y=np.mean(canto1Coordenadas), color='grey', linestyle='--', label='Canto1 Dist Mean')
    axs2[0].text(0.5, 0.9, f'Std of Dist Cant1: {canto1Coordenadas_std:.2f}', transform=axs2[0].transAxes,
                 color='black')
    axs2[0].text(0.5, 0.8, f'Max dev of Dist Cant1: {canto1_max_dev:.2f}', transform=axs2[0].transAxes, color='black')
    axs2[0].set_title('Distância entre os cantos 1')
    axs2[0].set_xlabel('Frame')
    axs2[0].set_ylabel('Distância')
    axs2[0].set_yticks(np.arange(0, round(max(canto1Coordenadas)) + 8, 1))
    axs2[0].legend()

    # Gráfico para a distância entre os cantos 2
    axs2[1].plot(range(len(canto2Coordenadas)), canto2Coordenadas, label='Distância Canto 2', color='red')
    axs2[1].axhline(y=np.mean(canto2Coordenadas), color='grey', linestyle='--', label='Canto1 Dist Mean')
    axs2[1].text(0.5, 0.9, f'Std of Dist Cant2: {canto2Coordenadas_std:.2f}', transform=axs2[1].transAxes,
                 color='black')
    axs2[1].text(0.5, 0.8, f'Max dev of Dist Cant2: {canto2_max_dev:.2f}', transform=axs2[1].transAxes, color='black')
    axs2[1].set_title('Distância entre os cantos 2')
    axs2[1].set_xlabel('Frame')
    axs2[1].set_ylabel('Distância')
    axs2[1].set_yticks(np.arange(0, round(max(canto2Coordenadas)) + 8, 1))
    axs2[1].legend()

    plt.tight_layout()
    output_filename = f'graficosTestes/{device}_output_distCantos_{timestamp}_{modelo}.png'
    plt.savefig(output_filename)
    plt.show()

def ultimo_id_alerta(id):
    global id_ultimo_alerta
    id_ultimo_alerta = id
    print(id_ultimo_alerta)
