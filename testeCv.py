import math
import time

from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import numpy as np


def runscript(device, classes):
    model = YOLO("yolov8s.pt")
    indexMouse = list(model.names.values()).index("mouse")
    indexPerson = list(model.names.values()).index("person")
    listObjToFind = [indexMouse, indexPerson]
    cap = cv2.VideoCapture(device)
    y1Anterior = 0
    x1Anterior = 0
    x2Anterior = 0
    y2Anterior = 0
    i = 0
    margem = 10

    x1_coordinates = []
    y1_coordinates = []

    def distance(x1, x2, y1, y2):
        return math.sqrt((x1-x2) ** 2 + (y1-y2) ** 2)

    while cap.isOpened() and i < 11:
        grabbed = cap.grab()
        if not grabbed:  # Se o frame nao for lido corretamente
            print("Error: Unable to grab frame from webcam.")
            break

        ret, frame = cap.retrieve()
        if not ret:
            print("Error: Unable to retrieve frame from webcam.")
            break

        results = model.track(
            frame, show=True, classes=listObjToFind, stream=False, persist=True)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break
        for r in results:
            coordenadas = r.boxes.cpu().numpy()
            if coordenadas:
                x1, y1, x2, y2 = coordenadas.xyxy[0]
                x1_coordinates.append(x1)
                y1_coordinates.append(y1)
                if i == 0:
                    x1Anterior = x1
                    y1Anterior = y1
                    x2Anterior = x2
                    y2Anterior = y2
                else:
                    distanciaCanto1 = distance(x1Anterior, x1, y1Anterior, y1)
                    distanciaCanto2 = distance(x2Anterior, x2, y2Anterior, y2)

                    if distanciaCanto1 <= margem and distanciaCanto2 <= margem:
                        print("Parado")
                    else:
                        print("Mover")
                    x1Anterior = x1
                    y1Anterior = y1
                    x2Anterior = x2
                    y2Anterior = y2
            i += 1
        time.sleep(2)

    cap.release()
    cv2.destroyAllWindows()

    x1_coordinates = np.array(x1_coordinates)
    y1_coordinates = np.array(y1_coordinates)

    x1_std = np.std(x1_coordinates)
    y1_std = np.std(y1_coordinates)

    plt.axhline(y=np.mean(x1_coordinates) + x1_std, color='grey', linestyle='--', label='x1 Std Dev')
    plt.axhline(y=np.mean(y1_coordinates) + y1_std, color='grey', linestyle='--', label='y1 Std Dev')

    plt.plot(range(len(x1_coordinates)),
             x1_coordinates, label='x1', color='blue')
    plt.plot(range(len(y1_coordinates)),
             y1_coordinates, label='y1', color='red')

    plt.text(0.5, 0.9, f'Std of x1: {x1_std:.2f}', transform=plt.gca().transAxes, color='blue')
    plt.text(0.5, 0.85, f'Std of y1: {y1_std:.2f}', transform=plt.gca().transAxes, color='red')

    plt.title('x1 and y1 Coordinates over Time')
    plt.xlabel('Frame')
    plt.ylabel('Coordinate Value')
    plt.legend()
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
