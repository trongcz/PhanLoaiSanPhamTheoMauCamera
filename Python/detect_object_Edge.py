import cv2
import numpy as np

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:

    ret, frame = cap.read()
    if not ret:
        break

    # chuyển grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # giảm nhiễu
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    # edge detection
    edges = cv2.Canny(blur, 50, 150)

    # kernel morphology
    kernel = np.ones((5,5), np.uint8)

    # đóng lỗ
    dilate = cv2.dilate(edges, kernel, iterations=2)
    closing = cv2.morphologyEx(dilate, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        closing,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area > 1500:

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
                f"Area:{int(area)}",
                (x,y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,255,0),
                2
            )

    cv2.imshow("Camera", frame)
    cv2.imshow("Edge", edges)
    cv2.imshow("Processed", closing)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()