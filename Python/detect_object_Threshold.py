import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # chuyển grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # làm mượt
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    # tách nền
    _, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)

    # tìm contour
    contours, _ = cv2.findContours(
        thresh, 
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area > 1000:   # lọc nhiễu

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
                "Object",
                (x,y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,255,0),
                2
            )

    cv2.imshow("Camera", frame)
    cv2.imshow("Threshold", thresh)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()