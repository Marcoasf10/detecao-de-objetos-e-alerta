import datetime
import math
import os
import threading
import time
from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import numpy as np
from threading import Thread
from multiprocessing import Manager
import psutil

modelo = 'yolov8s'
model = YOLO(modelo)
grabbed_frames = {}
retrieved_frames = {}
predicted_frames= {}
caps = {}
cpu_usage = []
memory_usage = []
cpu_inicial = psutil.cpu_percent()
memory_inicial = psutil.virtual_memory().percent
stop = False
stop_lock = threading.Lock()
retrived_frames_lock = threading.Lock()
predicted_frames_lock = threading.Lock()

def runscript(devices, classes,graphs=False):
    global cpu_usage
    global memory_usage
    start_time = time.time()
    threads = []
    listObjToFind = []
    for classe in classes:
        listObjToFind.append(list(model.names.values()).index(classe))
    for device in devices:
        thread = Thread(target=predict, args=(device, listObjToFind, graphs))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    print(len(cpu_usage))
    graficoPerformance(start_time, cpu_usage, memory_usage)
    delete_frames()
    cv2.destroyAllWindows()

def runscriptMac(devices, classes, queue, delay, graphs=False):
    with Manager() as manager:
        cpu_usage = manager.list()
        memory_usage = manager.list()
        start_time = time.time()
        threads = []
        listObjToFind = []
        for classe in classes:
            listObjToFind.append(list(model.names.values()).index(classe))
        for device in devices:
            thread = Thread(target=predict, args=(device, listObjToFind, graphs, cpu_usage, memory_usage, queue, delay))
            thread.start()
            threads.append(thread)

        # Wait for all processes to finish
        for thread in threads:
            thread.join()
        queue.put(-1)
        graficoPerformance(start_time, cpu_usage, memory_usage)
        cv2.destroyAllWindows()

def runscriptSingle(devices, classes, queue, graphs=False):
    global cpu_usage
    global memory_usage
    start_time = time.time()
    listObjToFind = []
    for classe in classes:
        listObjToFind.append(list(model.names.values()).index(classe))
    interval = 0
    while interval < 40:
        for device in devices:
            cap = cv2.VideoCapture(device)
            ret, frame = cap.read()
            if not ret:
                print("Error: Unable to retrieve frame from webcam.")
                break
            predictRetrieve(frame, listObjToFind, graphs, device)
            cpu_usage.append(psutil.cpu_percent())
            memory_usage.append(psutil.virtual_memory().percent)
            cap.release()
            cv2.destroyAllWindows()
        queue.put(predicted_frames)
        print(interval)
        interval += 1
    queue.put(-1)
    graficoPerformance(start_time, cpu_usage, memory_usage)
    cv2.destroyAllWindows()

def runscriptgrabRetrieve(devices, classes, queue, graphs=False):
    global stop
    global cpu_usage
    global memory_usage
    global caps
    listObjToFind = []
    threads = []
    start_time = time.time()
    for classe in classes:
        listObjToFind.append(list(model.names.values()).index(classe))
    interval = 0
    for device in devices:
        caps[device] = cv2.VideoCapture(device)
    while interval < 200:
        for device in devices:
            thread = Thread(target=retrieveFrames, args=(device,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        for device, frame in retrieved_frames.items():
            threads = []
            thread = Thread(target=predictRetrieve, args=(frame, listObjToFind, graphs, device))
            thread.start()
            threads.append(thread)
            for thread in threads:
                thread.join()
        queue.put(predicted_frames)
        cpu_usage.append(psutil.cpu_percent())
        memory_usage.append(psutil.virtual_memory().percent)
        cv2.destroyAllWindows()
        print(interval)
        interval += 1
    queue.put(-1)
    for key,cap in caps.items():
        cap.release()
    graficoPerformance(start_time, cpu_usage, memory_usage)
    with stop_lock:
        stop = True

def distance(x1, x2, y1, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def delete_frames():
    folder = "frames"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


def captureThread(device):
    global stop
    i = 0
    while caps[device].isOpened():
        with stop_lock:
            if stop:
                break
        caps[device].grab()
        i += 1
    caps[device].release()
    with stop_lock:
        stop = False

def retrieveFrames(device):
    global caps
    i = 0
    ret = False
    while not ret and i <= 10:
        ret, frame = caps[device].read()
        i += 1
    with retrived_frames_lock:
        retrieved_frames[device] = frame


def predict(device, listObjToFind, graphs, cpu_shared, memory_shared, queue, delay):
    global predicted_frames
    canto1Mapper = dict()
    canto2Mapper = dict()
    local_model = YOLO(modelo)
    cap = cv2.VideoCapture(device)
    i = 0
    margem = 4
    x1_coordinates = []
    y1_coordinates = []
    x2_coordinates = []
    y2_coordinates = []
    confiancas = []
    distanciaCanto1Lista = []
    distanciaCanto2Lista = []
    last_frame = None
    error = 0

    while cap.isOpened() and i < 40:
        #dar tempo para câmara inicializar
        if last_frame is None:
            time.sleep(0.1)
        start_time = time.time()
        grabbed = cap.grab()
        if not grabbed:
            cap.release()
            cap = cv2.VideoCapture(device)
            print("Error: Unable to grab frame from webcam.")
            continue
        ret, frame = cap.retrieve()
        if not ret:
            print("Error: Unable to retrieve frame from webcam.")
            break
        if last_frame is not None:
            img1 = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            error, diff = diferenceImgs(img1, img2)
            print("Error diference: ", error)
        # if img not equal last img:
        if last_frame is None or (last_frame is not None and error > 15):
            results = local_model.track(frame, save=True, project="frames", exist_ok=True, classes=listObjToFind, stream=False, persist=True, imgsz=1280)
            last_frame = frame
        with predicted_frames_lock:
            try:
                predicted_frames[device] = cv2.imread("frames/track/image0.jpg")
            except Exception as e:
                print(f"Error: {e}")
                continue
            queue.put(predicted_frames)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break
        for r in results:
            boxes = r.boxes.cpu().numpy()
            if not boxes or boxes.id is None or boxes.id.size == 0:
                cpu_shared.append(psutil.cpu_percent())
                memory_shared.append(psutil.virtual_memory().percent)
                i += 1
                continue
            if boxes:
                for f in range(boxes.id.size):
                    id = boxes.id[f]
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
                    else:
                        print(f"ID: {int(id)} -> Mover")
        cpu_usage.append(psutil.cpu_percent())
        memory_usage.append(psutil.virtual_memory().percent)
        i += 1
        while time.time() - start_time <= delay:
            cap.grab()

    cap.release()
    if graphs:
        criarGraficos(device, modelo, x1_coordinates, y1_coordinates, x2_coordinates, y2_coordinates, confiancas, distanciaCanto1Lista, distanciaCanto2Lista)

def diferenceImgs(img1, img2):
   h, w = img1.shape
   diff = cv2.subtract(img1, img2)
   err = np.sum(diff**2)
   mse = err/(float(h*w))
   return mse, diff
def predictRetrieve(frame, listObjToFind, graphs, device):
    canto1Mapper = dict()
    canto2Mapper = dict()
    local_model = YOLO(modelo)
    i = 0
    margem = 4
    x1_coordinates = []
    y1_coordinates = []
    x2_coordinates = []
    y2_coordinates = []
    confiancas = []
    distanciaCanto1Lista = []
    distanciaCanto2Lista = []

    results = local_model.track(frame, save=True, project="frames", exist_ok=True, classes=listObjToFind, stream=False, persist=True, imgsz=1280 , conf=0.35)
    with predicted_frames_lock:
        predicted_frames[device] = cv2.imread("frames/track/image0.jpg")

    for r in results:
        boxes = r.boxes.cpu().numpy()
        if not boxes or boxes.id is None or boxes.id.size == 0:
            continue
        if boxes:
            for f in range(boxes.id.size):
                id = boxes.id[f]
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
                else:
                    print(f"ID: {int(id)} -> Mover")
        i += 1

def list_available_cameras():
    num_devices = 0
    while True:
        try:
            cap = cv2.VideoCapture(num_devices)
            if cap.isOpened():
                print(f"Camera {num_devices}: Available")
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
    return num_devices


def get_classes():
    return list(model.names.values())


def criarGraficos(device, modelo, x1_coordinates, y1_coordinates, x2_coordinates, y2_coordinates, confiancas, distanciaCanto1Lista, distanciaCanto2Lista):
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

def graficoPerformance(start_time, cpu_usage, memory_usage):
    duracao = time.time() - start_time
    duracao_minutos = int(duracao // 60)
    duracao_segundos = int(duracao % 60)
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
    axs[0].text(0.5, 0.6, f'Média CPU Usage (%): {np.mean(cpu_usage_array):.2f}', transform=axs[0].transAxes, color='black')
    axs[0].set_title('CPU Usage (%)')
    axs[0].set_xlabel('Frame')
    axs[0].set_ylabel('Usage')
    axs[0].set_yticks(np.arange(0, 100, 10))
    axs[0].legend()

    # Gráfico para a distância entre os cantos 2
    axs[1].plot(range(len(memory_usage_array)), memory_usage_array, label='CPU Usage', color='blue')
    axs[1].axhline(y=np.mean(memory_usage_array), color='grey', linestyle='--', label='CPU Usage Mean')
    axs[1].text(0.5, 0.5, f'Inicial Memory (%): {memory_inicial:.2f}', transform=axs[1].transAxes, color='black')
    axs[1].text(0.5, 0.4, f'Max Memory usage (%): {max(memory_usage_array):.2f}', transform=axs[1].transAxes, color='black')
    axs[1].text(0.5, 0.3, f'Min Memory usage (%): {min(memory_usage_array):.2f}', transform=axs[1].transAxes, color='black')
    axs[1].text(0.5, 0.2, f'Média Memory usage (%): {np.mean(memory_usage_array):.2f}', transform=axs[1].transAxes, color='black')
    axs[1].set_title('Memory Usage (%)')
    axs[1].set_xlabel('Frame')
    axs[1].set_ylabel('Usage')
    axs[1].set_yticks(np.arange(0, 100, 10))
    axs[1].legend()

    plt.suptitle(f'Desempenho do Sistema duração: {duracao_minutos}m:{duracao_segundos}s', fontsize=16)
    plt.tight_layout()
    output_filename = f'graficosTestes/performanceGraph_{timestamp}_{modelo}.png'
    plt.savefig(output_filename)
    plt.show()
