import math
import time

from ultralytics import YOLO
import cv2
import torch

model = YOLO("yolov8s.pt")  # load a pretrained model (recommended for training)
indexPerson = list(model.names.values()).index("person")
cap = cv2.VideoCapture(0)  # Assuming you're capturing from a webcam
x1Anterior = 0
y1Anterior = 0
x2Anterior = 0
y2Anterior = 0
i = 0
margem = 10

def distance(x1, x2, y1, y2):
    return math.sqrt((x1-x2) ** 2 + (y1-y2) ** 2)

while cap.isOpened():
    ret, frame =cap.read()
    if not ret: #Se o frame nao for lido corretamente
        break
    results = model.track(frame, show=True, classes=indexPerson, stream=False, persist=True)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
        break
    for r in results:
        coordenadas = r.boxes.cpu().numpy()
        x1,y1,x2,y2 = coordenadas.xyxy[0]
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
 