import cv2
import numpy as np
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk

# ================== SERIAL ==================
ser = None

def connect_serial(port):
    global ser
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"Connected to {port}")
    except:
        print("Cannot connect serial")

def send_color(color_code):
    global ser
    if ser and ser.is_open:
        ser.write((color_code + "\n").encode())

# ================== COLOR DETECTION ==================
def detect_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # ====== Define HSV ranges ======
    masks = {}

    # RED (2 vùng)
    mask_red1 = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))
    mask_red2 = cv2.inRange(hsv, (170, 120, 70), (180, 255, 255))
    masks["RED"] = mask_red1 + mask_red2

    # GREEN
    masks["GREEN"] = cv2.inRange(hsv, (40, 70, 70), (80, 255, 255))

    # YELLOW
    masks["YELLOW"] = cv2.inRange(hsv, (20, 100, 100), (35, 255, 255))

    # BLACK
    masks["BLACK"] = cv2.inRange(hsv, (0, 0, 0), (180, 255, 50))

    detected = None
    max_area = 0

    for color, mask in masks.items():
        # Lọc nhiễu
        mask = cv2.GaussianBlur(mask, (5,5), 0)
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 2000 and area > max_area:
                max_area = area
                detected = color

                x,y,w,h = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
                cv2.putText(frame, color, (x,y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    return frame, detected

# ================== CAMERA LOOP ==================
def start_camera(cam_index):
    global running
    cap = cv2.VideoCapture(cam_index)

    last_color = ""

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        frame, color = detect_color(frame)

        if color and color != last_color:
            print("Detected:", color)
            send_color(color)
            last_color = color

        cv2.imshow("Camera", frame)

        # vẫn giữ ESC để backup
        if cv2.waitKey(1) & 0xFF == 27:
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()

# ================== UI ==================
def get_cameras():
    arr = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            arr.append(i)
        cap.release()
    return arr

def get_ports():
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]

def run():
    global running
    running = True

    cam = int(cam_combo.get())
    port = port_combo.get()

    connect_serial(port)

    # chạy camera trong thread để không bị đơ UI
    import threading
    threading.Thread(target=start_camera, args=(cam,), daemon=True).start()

def stop():
    global running
    running = False

# UI
root = tk.Tk()
root.title("Color Detection")


tk.Label(root, text="Select Camera").pack()
cam_combo = ttk.Combobox(root, values=get_cameras())
cam_combo.pack()

tk.Label(root, text="Select COM Port").pack()
port_combo = ttk.Combobox(root, values=get_ports())
port_combo.pack()

tk.Button(root, text="Start", command=run).pack()
tk.Button(root, text="Stop", command=stop).pack()

root.mainloop()