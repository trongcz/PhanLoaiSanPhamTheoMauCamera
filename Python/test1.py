import cv2
import numpy as np
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading

# ================= GLOBAL =================
running = False
ser = None
background = None
use_bg = False
current_frame = None

# ================= SERIAL =================
def connect_serial(port):
    global ser
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print("Connected:", port)
    except:
        print("Serial error")

def disconnect_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("Serial disconnected")

def read_serial():
    global ser, running
    while running:
        if ser and ser.is_open:
            try:
                data = ser.readline().decode().strip()
                if data:
                    log_text.insert(tk.END, data + "\n")
                    log_text.see(tk.END)
            except:
                pass

def send_color(color):
    if ser and ser.is_open:
        ser.write((color + "\n").encode())

# ================= COLOR DETECTION =================
def detect_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    masks = {}

    # RED
    mask_red1 = cv2.inRange(hsv, (0,120,70), (10,255,255))
    mask_red2 = cv2.inRange(hsv, (170,120,70), (180,255,255))
    masks["RED"] = mask_red1 + mask_red2

    # GREEN (đã FIX range)
    masks["GREEN"] = cv2.inRange(hsv, (30,50,50), (90,255,255))

    # YELLOW
    masks["YELLOW"] = cv2.inRange(hsv, (20,100,100), (35,255,255))

    # BLACK
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

# ================= BACKGROUND REMOVE =================
def remove_background(frame):
    global background

    if background is None:
        return frame

    diff = cv2.absdiff(background, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # FIX threshold
    _, mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    result = cv2.bitwise_and(frame, frame, mask=mask)
    return result

# ================= CAMERA LOOP =================
def camera_loop():
    global running, use_bg, current_frame

    cam_index = int(cam_combo.get())
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)

    last_color = ""

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        current_frame = frame.copy()

        # trừ nền
        if use_bg:
            frame = remove_background(frame)

        # detect màu
        frame, color = detect_color(frame)

        if color and color != last_color:
            print("Detected:", color)
            send_color(color)
            last_color = color

        # hiển thị UI
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)

        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

    cap.release()

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

def capture_background():
    global background, current_frame

    if current_frame is not None:
        background = current_frame.copy()
        print("Background captured OK")
    else:
        print("No frame yet")

def toggle_bg():
    global use_bg
    use_bg = not use_bg
    print("Use BG:", use_bg)

# ================= UI =================
root = tk.Tk()
root.title("Color Detection System")
root.geometry("800x800")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

# ===== VIDEO =====
video_frame = tk.Frame(main_frame)
video_frame.pack(fill="both", expand=True)

video_label = tk.Label(video_frame, bg="black")
video_label.pack(fill="both", expand=True)

# ===== ROW 1: Camera + COM =====
row1 = tk.Frame(main_frame)
row1.pack(fill="x", pady=5)

tk.Label(row1, text="Camera").pack(side="left", padx=5)
cam_combo = ttk.Combobox(row1, values=[0,1,2,3], width=5)
cam_combo.current(0)
cam_combo.pack(side="left")

tk.Label(row1, text="COM").pack(side="left", padx=5)
ports = [p.device for p in serial.tools.list_ports.comports()]
port_combo = ttk.Combobox(row1, values=ports, width=10)
port_combo.pack(side="left")

tk.Button(row1, text="Disconnect", command=disconnect_serial).pack(side="left", padx=10)

# ===== ROW 2: Background control (GIỮA) =====
row2 = tk.Frame(main_frame)
row2.pack(fill="x", pady=5)

tk.Button(row2, text="Chụp nền", width=15, command=capture_background).pack(side="left", expand=True)
tk.Button(row2, text="Bật/Tắt BG", width=15, command=toggle_bg).pack(side="left", expand=True)

# ===== ROW 3: Start / Stop =====
row3 = tk.Frame(main_frame)
row3.pack(fill="x", pady=5)

tk.Button(row3, text="Start", width=10, command=start).pack(side="left", padx=10)
tk.Button(row3, text="Stop", width=10, command=stop).pack(side="left", padx=10)


# ===== ROW 4: Serial log + Scrollbar =====
row4 = tk.Frame(main_frame)
row4.pack(fill="both", expand=False)

tk.Label(row4, text="Serial Log").pack(anchor="w")

log_frame = tk.Frame(row4)
log_frame.pack(fill="both", padx=5, pady=5)

# Text box
log_text = tk.Text(log_frame, height=8)
log_text.pack(side="left", fill="both", expand=True)

# Scrollbar
scrollbar = tk.Scrollbar(log_frame, command=log_text.yview)
scrollbar.pack(side="right", fill="y")

# Liên kết 2 thằng với nhau
log_text.config(yscrollcommand=scrollbar.set)

root.mainloop()