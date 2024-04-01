import datetime
import math
import os
import time

from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import numpy as np
from threading import Thread
from multiprocessing import Process

model = YOLO("yolov8s.pt")


def runscript(devices, classes, graphs=False):
    threads = []
    listObjToFind = []
    for classe in classes:
        listObjToFind.append(list(model.names.values()).index(classe))
    for device in devices:
        thread = Thread(target=predict, args=(device.data(1), listObjToFind, graphs))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    delete_frames()
    cv2.destroyAllWindows()

def runscriptMac(devices, classes, graphs=False):
    print(graphs)
    processes = []
    listObjToFind = []
    for classe in classes:
        listObjToFind.append(list(model.names.values()).index(classe))
    for device in devices:
        process = Process(target=predict, args=(device.data(1), listObjToFind, graphs))
        process.start()
        processes.append(process)

    # Wait for all processes to finish
    for process in processes:
        process.join()
    delete_frames()
    cv2.destroyAllWindows()

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


def predict(device, listObjToFind, graphs):
    local_model = YOLO("yolov8s.pt")
    cap = cv2.VideoCapture(device)
    y1Anterior = 0
    x1Anterior = 0
    x2Anterior = 0
    y2Anterior = 0
    i = 0
    margem = 10
    x1_coordinates = []
    y1_coordinates = []
    x2_coordinates = []
    y2_coordinates = []
    confiancas = []

    distanciaCanto1Lista = []
    distanciaCanto2Lista = []

    while cap.isOpened() and i < 40:
        grabbed = cap.grab()
        if not grabbed:  # Se o frame nao for lido corretamente
            print("Error: Unable to grab frame from webcam.")
            break

        ret, frame = cap.retrieve()
        if not ret:
            print("Error: Unable to retrieve frame from webcam.")
            break
        frame_filename = f"frames/device_{device}.jpg"
        cv2.imwrite(frame_filename, frame)
        results = local_model.track(
            f"frames/device_{device}.jpg", show=True, classes=listObjToFind, stream=False, persist=True)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break
        for r in results:
            coordenadas = r.boxes.cpu().numpy()
            if coordenadas:
                x1, y1, x2, y2 = coordenadas.xyxy[0]
                confiancas.append(coordenadas.conf[0] * 100)
                x1_coordinates.append(x1)
                y1_coordinates.append(y1)
                x2_coordinates.append(x2)
                y2_coordinates.append(y2)
                if i < 5:
                    x1Anterior = x1
                    y1Anterior = y1
                    x2Anterior = x2
                    y2Anterior = y2
                elif i > 5:
                    distanciaCanto1 = distance(x1Anterior, x1, y1Anterior, y1)
                    distanciaCanto1Lista.append(distanciaCanto1)
                    distanciaCanto2 = distance(x2Anterior, x2, y2Anterior, y2)
                    distanciaCanto2Lista.append(distanciaCanto2)

                    if distanciaCanto1 <= margem and distanciaCanto2 <= margem:
                        print("Parado")
                    else:
                        print(distanciaCanto1, distanciaCanto2)
                        print("Mover")
                    x1Anterior = x1
                    y1Anterior = y1
                    x2Anterior = x2
                    y2Anterior = y2
            i += 1
        time.sleep(0.2)
    cap.release()
    if graphs:
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
        axs[0, 0].legend()

        # Gráfico para y1
        axs[0, 1].plot(range(len(y1_coordinates)), y1_coordinates, label='y1', color='red')
        axs[0, 1].axhline(y=np.mean(y1_coordinates), color='grey', linestyle='--', label='y1 Mean')
        axs[0, 1].text(0.5, 0.9, f'Std of y1: {y1_std:.2f}', transform=axs[0, 1].transAxes, color='black')
        axs[0, 1].text(0.5, 0.8, f'Max dev of y1: {y1_max_dev:.2f}', transform=axs[0, 1].transAxes, color='black')
        axs[0, 1].set_title('y1 Coordinate over Time')
        axs[0, 1].set_xlabel('Frame')
        axs[0, 1].set_ylabel('Coordinate Value')
        axs[0, 1].legend()

        # Gráfico para x2
        axs[1, 0].plot(range(len(x2_coordinates)), x2_coordinates, label='x2', color='green')
        axs[1, 0].axhline(y=np.mean(x2_coordinates), color='grey', linestyle='--', label='x2 Mean')
        axs[1, 0].text(0.5, 0.9, f'Std of x2: {x2_std:.2f}', transform=axs[1, 0].transAxes, color='black')
        axs[1, 0].text(0.5, 0.8, f'Max Dev of x2: {x2_max_dev:.2f}', transform=axs[1, 0].transAxes, color='black')
        axs[1, 0].set_title('x2 Coordinate over Time')
        axs[1, 0].set_xlabel('Frame')
        axs[1, 0].set_ylabel('Coordinate Value')
        axs[1, 0].legend()

        # Gráfico para y2
        axs[1, 1].plot(range(len(y2_coordinates)), y2_coordinates, label='y2', color='magenta')
        axs[1, 1].axhline(y=np.mean(y2_coordinates), color='grey', linestyle='--', label='y2 Mean')
        axs[1, 1].text(0.5, 0.9, f'Std of y2: {y2_std:.2f}', transform=axs[1, 1].transAxes, color='black')
        axs[1, 1].text(0.5, 0.8, f'Max Dev of y2: {y2_max_dev:.2f}', transform=axs[1, 1].transAxes, color='black')
        axs[1, 1].set_title('y2 Coordinate over Time')
        axs[1, 1].set_xlabel('Frame')
        axs[1, 1].set_ylabel('Coordinate Value')
        axs[1, 1].legend()

        plt.tight_layout()
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
        output_filename = f'graficosTestes/{device}_output_coordenadas_{timestamp}.png'
        plt.savefig(output_filename)
        plt.show()

        # Plotando o gráfico para as coordenadas em "confiancas"
        plt.plot(range(len(confiancas)), confiancas, label='Coordinates', color='blue')

        # Calculando e adicionando a linha de desvio padrão
        mean = np.mean(confiancas)
        plt.axhline(y=np.mean(confiancas), color='grey', linestyle='--', label='Conf Mean')
        plt.text(0.5, 0.9, f'Mean: {mean:.2f}', transform=plt.gca().transAxes, color='blue')

        # Adicionando legendas e rótulos
        plt.title('Confidence over time')
        plt.xlabel('Frame')
        plt.ylabel('Confidence Value')
        plt.legend()
        output_filename = f'graficosTestes/{device}_output_confianca_{timestamp}.png'
        plt.savefig(output_filename)
        plt.show()

        fig2, axs2 = plt.subplots(1, 2, figsize=(15, 10))

        # Gráfico para a distância entre os cantos 1
        axs2[0].plot(range(len(canto1Coordenadas)), canto1Coordenadas, label='Distância Canto 1', color='blue')
        axs2[0].axhline(y=np.mean(canto1Coordenadas), color='grey', linestyle='--', label='Canto1 Dist Mean')
        axs2[0].text(0.5, 0.9, f'Std of Dist Cant1: {canto1Coordenadas_std:.2f}', transform=axs2[0].transAxes, color='black')
        axs2[0].text(0.5, 0.8, f'Max dev of Dist Cant1: {canto1_max_dev:.2f}', transform=axs2[0].transAxes, color='black')
        axs2[0].set_title('Distância entre os cantos 1')
        axs2[0].set_xlabel('Frame')
        axs2[0].set_ylabel('Distância')
        axs2[0].legend()

        # Gráfico para a distância entre os cantos 2
        axs2[1].plot(range(len(canto2Coordenadas)), canto2Coordenadas, label='Distância Canto 2', color='red')
        axs2[1].axhline(y=np.mean(canto2Coordenadas), color='grey', linestyle='--', label='Canto1 Dist Mean')
        axs2[1].text(0.5, 0.9, f'Std of Dist Cant2: {canto2Coordenadas_std:.2f}', transform=axs2[1].transAxes, color='black')
        axs2[1].text(0.5, 0.8, f'Max dev of Dist Cant2: {canto2_max_dev:.2f}', transform=axs2[1].transAxes, color='black')
        axs2[1].set_title('Distância entre os cantos 2')
        axs2[1].set_xlabel('Frame')
        axs2[1].set_ylabel('Distância')
        axs2[1].legend()

        plt.tight_layout()
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
        output_filename = f'graficosTestes/{device}_output_distCantos_{timestamp}.png'
        plt.savefig(output_filename)
        plt.show()


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
