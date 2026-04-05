import cv2
import numpy as np
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time

# ================= GLOBAL =================
running = False
ser = None
background = None
use_bg = False
current_frame = None

# ================= LOG =================
def log_sys(msg):
    timestamp = time.strftime("%H:%M:%S")
    sys_log.insert(tk.END, f"[{timestamp}] {msg}\n")
    sys_log.see(tk.END)

def log_serial(msg):
    timestamp = time.strftime("%H:%M:%S")
    serial_log.insert(tk.END, f"[{timestamp}] {msg}\n")
    serial_log.see(tk.END)

# ================= SERIAL =================
def connect_serial(port):
    global ser
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        log_sys(f"Connected: {port}")
    except:
        log_sys("Serial error")

def disconnect_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
        log_sys("Serial disconnected")

def read_serial():
    global running
    while running:
        if ser and ser.is_open:
            try:
                data = ser.readline().decode().strip()
                if data:
                    root.after(0, log_serial, f"RX: {data}")
            except:
                pass

def send_color(color):
    if ser and ser.is_open:
        ser.write((color + "\n").encode())
        root.after(0, log_serial, f"TX: {color}")

# ================= COLOR DETECT =================
kernel = np.ones((5,5), np.uint8)

def detect_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    masks = {
        "RED": cv2.inRange(hsv,(0,120,70),(10,255,255)) + cv2.inRange(hsv,(170,120,70),(180,255,255)),
        "GREEN": cv2.inRange(hsv,(30,50,50),(90,255,255)),
        "YELLOW": cv2.inRange(hsv,(20,100,100),(35,255,255)),
        "BLACK": cv2.inRange(hsv,(0,0,0),(180,255,50))
    }

    detected = None
    max_area = 0

    for color, mask in masks.items():
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 2000 and area > max_area:
                max_area = area
                detected = color

                x,y,w,h = cv2.boundingRect(cnt)
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                cv2.putText(frame,color,(x,y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

    return frame, detected

# ================= BG REMOVE =================
def remove_background(frame):
    if background is None:
        return frame

    diff = cv2.absdiff(background, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return cv2.bitwise_and(frame, frame, mask=mask)

# ================= CAMERA =================
def camera_loop():
    global running, current_frame

    cap = cv2.VideoCapture(int(cam_combo.get()), cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    last_sent = 0
    last_detect = 0

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640,480))
        current_frame = frame.copy()

        # 👉 CHỈ detect mỗi 0.2s (5 FPS)
        if time.time() - last_detect > 0.2:
            if use_bg:
                frame_proc = remove_background(frame)
            else:
                frame_proc = frame

            frame_proc, color = detect_color(frame_proc)

            if color and time.time() - last_sent > 0.7:
                send_color(color)
                root.after(0, log_sys, f"Detected: {color}")
                last_sent = time.time()

            last_detect = time.time()

        # 👉 LUÔN HIỂN THỊ (không skip)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))

        root.after(0, update_video, img)

    cap.release()

def update_video(img):
    video_label.imgtk = img
    video_label.configure(image=img)

# ================= CONTROL =================
def start():
    global running
    running = True

    if port_combo.get():
        connect_serial(port_combo.get())

    threading.Thread(target=camera_loop, daemon=True).start()
    threading.Thread(target=read_serial, daemon=True).start()

def stop():
    global running
    running = False
    disconnect_serial()

def capture_background():
    global background
    if current_frame is not None:
        background = current_frame.copy()
        log_sys("Background captured")

def toggle_bg():
    global use_bg
    use_bg = not use_bg
    log_sys(f"Use BG: {use_bg}")

# ================= UI =================
root = tk.Tk()
root.title("Color Detection System")
root.geometry("900x700")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

video_label = tk.Label(main_frame, bg="black")
video_label.pack(fill="both", expand=True)

control = tk.Frame(main_frame)
control.pack(fill="x")

# LEFT
left = tk.Frame(control)
left.pack(side="left", padx=10)

tk.Label(left, text="Camera").pack(side="left")
cam_combo = ttk.Combobox(left, values=[0,1,2], width=5)
cam_combo.current(0)
cam_combo.pack(side="left", padx=5)

tk.Label(left, text="COM").pack(side="left", padx=(50,0))
ports = [p.device for p in serial.tools.list_ports.comports()]
port_combo = ttk.Combobox(left, values=ports, width=10)
port_combo.pack(side="left", padx=5)

# RIGHT
right = tk.Frame(control)
right.pack(side="right", padx=10)

tk.Button(right, text="Chụp nền", command=capture_background).pack(side="left", padx=5)
tk.Button(right, text="BG", command=toggle_bg).pack(side="left", padx=5)

tk.Button(right, text="START", bg="green", fg="white",
          width=10, height=2, command=start).pack(side="left", padx=20)

tk.Button(right, text="STOP", bg="red", fg="white",
          width=10, height=2, command=stop).pack(side="left")

# LOG
log_row = tk.Frame(main_frame)
log_row.pack(fill="both", expand=True)

log_row.columnconfigure(0, weight=1)
log_row.columnconfigure(1, weight=1)
log_row.rowconfigure(0, weight=1)

sys_log = tk.Text(log_row)
sys_log.grid(row=0, column=0, sticky="nsew")

serial_log = tk.Text(log_row)
serial_log.grid(row=0, column=1, sticky="nsew")

root.mainloop()