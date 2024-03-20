import math
import time

from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import torch


def runscript():
    # load a pretrained model (recommended for training)
    model = YOLO("yolov8s.pt")
    indexPerson = list(model.names.values()).index("person")
    cap = cv2.VideoCapture(1)  # Assuming you're capturing from a webcam
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
            frame, show=True, classes=indexPerson, stream=False, persist=True)
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

    plt.plot(range(len(x1_coordinates)),
             x1_coordinates, label='x1', color='blue')
    plt.plot(range(len(y1_coordinates)),
             y1_coordinates, label='y1', color='red')
    plt.title('x1 and y1 Coordinates over Time')
    plt.xlabel('Frame')
    plt.ylabel('Coordinate Value')
    plt.legend()
    plt.show()
