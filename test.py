import cv2


vcap = cv2.VideoCapture("rtsp://176.103.33.12:554/ChocenPlaza")
while(1):
    ret, frame = vcap.read()
    frame = cv2.copyMakeBorder(frame, 0, 0, 0, 100, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.imshow('VIDEO', frame)
    cv2.waitKey(1)