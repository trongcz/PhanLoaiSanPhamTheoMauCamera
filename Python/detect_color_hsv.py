import cv2
import numpy as np

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

while True:

    ret, frame = cap.read()
    if not ret:
        break

    # chuyển sang HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # khoảng màu đỏ
    lower_red = np.array([0,120,70])
    upper_red = np.array([10,255,255])

    # tạo mask
    mask = cv2.inRange(hsv, lower_red, upper_red)

    # tìm contour
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area > 800:

            x,y,w,h = cv2.boundingRect(cnt)

            cv2.rectangle(
                frame,
                (x,y),
                (x+w,y+h),
                (0,255,0),
                2
            )

            cv2.putText(
                frame,
                "RED",
                (x,y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,255,0),
                2
            )

    cv2.imshow("Camera", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
