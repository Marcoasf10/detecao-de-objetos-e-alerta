import math
import time
from threading import Thread, Lock
import cv2
import numpy as np
from ultralytics import YOLO
import pickle

modelo = 'yolov8s'
model = YOLO(modelo)
retrieved_frames = {}
predicted_frames = {}
stop_dict = {}
delay_dict = {}
obj_find_dict = {}
delete_devices = []
obj_find_lock = Lock()
stop_lock = Lock()
retrived_frames_lock = Lock()
predicted_frames_lock = Lock()
delay_lock = Lock()
delete_devices_lock = Lock()



def addDispositivoToPredict(device, classes, queue, delay):
    listObjToFind = []
    for classe in classes:
        listObjToFind.append(list(model.names.values()).index(classe))
    thread = Thread(target=predict, args=(device, listObjToFind, queue, delay))
    thread.start()
    thread.join()
    cv2.destroyAllWindows()


def distance(x1, x2, y1, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def diferenceImgs(img1, img2):
    h, w = img1.shape
    diff = cv2.subtract(img1, img2)
    err = np.sum(diff ** 2)
    mse = err / (float(h * w))
    return mse, diff


def predict(device, listObjToFind, queue, delay):
    global predicted_frames
    global stop_dict
    global delay_dict
    global obj_find_dict
    canto1Mapper = dict()
    canto2Mapper = dict()
    local_model = YOLO(modelo)
    cap = cv2.VideoCapture(device)
    i = 0
    margem = 4
    last_frame = None
    error = 0
    stop = False
    parado = 0
    mover = 0
    alerta_filename = 'alertas.bin'
    while True:
        with delete_devices_lock:
            if device in delete_devices:
                break
        with stop_lock:
            if device in stop_dict:
                stop = stop_dict[device]
        if stop:
            if cap.isOpened():
                cap.release()
            time.sleep(1)
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
        start_time = time.time()
        grabbed = cap.grab()
        if not grabbed:
            cap.release()
            cap = cv2.VideoCapture(device)
            print(device)
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
        if last_frame is None or (last_frame is not None and error > 0):
            results = local_model.track(frame, save=True, project="frames", exist_ok=True, classes=listObjToFind,
                                        stream=False, persist=True, imgsz=1280, conf=0.3)
            last_frame = frame
        with delete_devices_lock:
            if device in delete_devices:
                break
        with predicted_frames_lock:
            try:
                predicted_frames[device] = cv2.imread("frames/track/image0.jpg")
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
                    id = boxes.id[f]
                    x1, y1, x2, y2 = boxes.xyxy[f]
                    if id not in canto1Mapper and id not in canto2Mapper:
                        canto1Mapper[id] = (x1, y1, -1)
                        canto2Mapper[id] = (x2, y2, -1)
                    canto1Mapper[id] = (x1, y1, distance(canto1Mapper[id][0], x1, canto1Mapper[id][1], y1))
                    canto2Mapper[id] = (x2, y2, distance(canto2Mapper[id][0], x2, canto2Mapper[id][1], y2))
                    if canto1Mapper[id][2] == -1 and canto2Mapper[id][2] == -1:
                        continue
                    if canto1Mapper[id][2] <= margem and canto2Mapper[id][2] <= margem:
                        mover = 0
                        print(f"ID: {int(id)} -> Parado")
                        parado += 1
                    else:
                        parado = 0
                        print(f"ID: {int(id)} -> Mover")
                        mover += 1
            if parado >= 10:
                parado = 0
                descricao = f'O objeto: {local_model.names[boxes.cls[f]]} está parado á 10 segundos'
                alerta = Alerta(device, local_model.names[boxes.cls[f]], descricao, frame)
                with open(alerta_filename, 'ab') as f:
                    pickle.dump(alerta, f)

        i += 1
        while time.time() - start_time <= delay:
            with delete_devices_lock:
                if device in delete_devices:
                    break
            with stop_lock:
                if device in stop_dict:
                    stop = stop_dict[device]
                    if stop:
                        break
            with delay_lock:
                if device in delay_dict:
                    delay = delay_dict[device]
            cap.grab()
    cap.release()
    delete_devices.remove(device)


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

def update_obj_to_find(device ,obj_to_find):
    global obj_find_dict
    obj_find_dict[device] = obj_to_find

def remove_device(device):
    delete_devices.append(device)

class Alerta:
    def __init__(self, device, classe, descriçao, photo):
        self.device = device
        self.classe = classe
        self.descricao = descriçao
        self.photo = photo

    def get_device(self):
        return self.device

    def get_classe(self):
        return self.classe

    def get_descricao(self):
        return self.descricao

    def get_photo(self):
        return self.photo


