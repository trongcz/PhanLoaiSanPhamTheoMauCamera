import cv2

# mở camera (0 = camera mặc định)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Không mở được camera")
        break

    cv2.imshow("Camera Test", frame)

    # nhấn q để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()