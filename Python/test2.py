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
    full_msg = f"[{timestamp}] {msg}"

    def update():
        sys_log.insert(tk.END, full_msg + "\n")
        sys_log.see(tk.END)

    try:
        sys_log.after(0, update)
    except:
        pass


def log_serial(msg):
    timestamp = time.strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"

    def update():
        serial_log.insert(tk.END, full_msg + "\n")
        serial_log.see(tk.END)

    try:
        serial_log.after(0, update)
    except:
        pass

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
    global ser, running
    while running:
        if ser and ser.is_open:
            try:
                data = ser.readline().decode().strip()
                if data:
                    log_serial(f"RX: {data}")
            except:
                pass

def send_color(color):
    if ser and ser.is_open:
        ser.write((color + "\n").encode())
        log_serial(f"TX: {color}")

# ================= COLOR DETECT =================
def detect_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    masks = {}

    mask_red1 = cv2.inRange(hsv, (0,120,70), (10,255,255))
    mask_red2 = cv2.inRange(hsv, (170,120,70), (180,255,255))
    masks["RED"] = mask_red1 + mask_red2

    masks["GREEN"] = cv2.inRange(hsv, (30,50,50), (90,255,255))
    masks["YELLOW"] = cv2.inRange(hsv, (20,100,100), (35,255,255))
    masks["BLACK"] = cv2.inRange(hsv, (0,0,0), (180,255,50))

    detected = None
    max_area = 0

    for color, mask in masks.items():
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
    global background
    if background is None:
        return frame

    diff = cv2.absdiff(background, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return cv2.bitwise_and(frame, frame, mask=mask)

# ================= CAMERA LOOP =================
def camera_loop():
    global running, use_bg, current_frame

    cap = cv2.VideoCapture(int(cam_combo.get()), cv2.CAP_DSHOW)
    last_sent_time = 0

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        current_frame = frame.copy()

        if use_bg:
            frame = remove_background(frame)

        frame, color = detect_color(frame)

        if color:
            now = time.time()
            if now - last_sent_time > 0.7:
                send_color(color)
                log_sys(f"Detected: {color}")
                last_sent_time = now

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb).resize((640,480))
        imgtk = ImageTk.PhotoImage(image=img)

        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

    cap.release()
    log_sys("Camera stopped")

# ================= UI FUNCTIONS =================
def start():
    global running
    running = True

    port = port_combo.get()
    if port:
        connect_serial(port)

    threading.Thread(target=camera_loop, daemon=True).start()
    threading.Thread(target=read_serial, daemon=True).start()

def stop():
    global running
    running = False
    disconnect_serial()

def capture_background():
    global background, current_frame
    if current_frame is not None:
        background = current_frame.copy()
        log_sys("Background captured")
    else:
        log_sys("No frame yet")

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

# VIDEO
video_frame = tk.Frame(main_frame)
video_frame.pack(fill="both", expand=True)

video_label = tk.Label(video_frame, bg="black")
video_label.pack(fill="both", expand=True)

# ===== CONTROL ROW =====
control_row = tk.Frame(main_frame)
control_row.pack(fill="x", pady=5)

# LEFT GROUP
left_group = tk.Frame(control_row)
left_group.pack(side="left", padx=10)

tk.Label(left_group, text="Camera").pack(side="left")
cam_combo = ttk.Combobox(left_group, values=[0,1,2,3], width=5)
cam_combo.current(0)
cam_combo.pack(side="left", padx=5)

tk.Label(left_group, text="COM").pack(side="left" , padx = (50, 0))
ports = [p.device for p in serial.tools.list_ports.comports()]
port_combo = ttk.Combobox(left_group, values=ports, width=10)
port_combo.pack(side="left", padx=5)

tk.Button(left_group, text="Disconnect", command=disconnect_serial).pack(side="left", padx=5)

# RIGHT GROUP
right_group = tk.Frame(control_row)
right_group.pack(side="right", padx=10)

tk.Button(right_group, text="Chụp nền", command=capture_background).pack(side="left", padx=10)
tk.Button(right_group, text="Bật/Tắt BG", command=toggle_bg).pack(side="left", padx=5)



tk.Button(right_group, text="START", bg="green", fg="white",
          width=10, height=2, command=start).pack(side="left", padx=50)

tk.Button(right_group, text="STOP", bg="red", fg="white",
          width=10, height=2, command=stop).pack(side="left")

# ===== LOG AREA (2 cột) =====
log_row = tk.Frame(main_frame)
log_row.pack(fill="both", expand=True)

log_row.columnconfigure(0, weight=1)
log_row.columnconfigure(1, weight=1)
log_row.rowconfigure(0, weight=1)

# SYSTEM LOG
sys_frame = tk.Frame(log_row)
sys_frame.grid(row=0, column=0, sticky="nsew")

tk.Label(sys_frame, text="System Log").pack(anchor="w")

sys_log_box = tk.Frame(sys_frame)
sys_log_box.pack(fill="both", expand=True)

sys_log = tk.Text(sys_log_box)
sys_log.pack(side="left", fill="both", expand=True)

sys_scroll = tk.Scrollbar(sys_log_box, command=sys_log.yview)
sys_scroll.pack(side="right", fill="y")

sys_log.config(yscrollcommand=sys_scroll.set)

# SERIAL LOG
serial_frame = tk.Frame(log_row)
serial_frame.grid(row=0, column=1, sticky="nsew")
sys_frame.grid(row=0, column=0, sticky="nsew", padx=(5,2))
serial_frame.grid(row=0, column=1, sticky="nsew", padx=(2,5))

tk.Label(serial_frame, text="Serial Log").pack(anchor="w")

serial_log_box = tk.Frame(serial_frame)
serial_log_box.pack(fill="both", expand=True)

serial_log = tk.Text(serial_log_box)
serial_log.pack(side="left", fill="both", expand=True)

serial_scroll = tk.Scrollbar(serial_log_box, command=serial_log.yview)
serial_scroll.pack(side="right", fill="y")

serial_log.config(yscrollcommand=serial_scroll.set)

root.mainloop()