import cv2

# OverlayCamera
STREAM_URL = 'rtsp://176.103.33.12:554/ChocenPlaza'

TEXT_DATA_REFRESH = 3
TEXT_SPACE = 600
TEXT_SIZE = 2
TEXT_FONT = cv2.FONT_HERSHEY_TRIPLEX 
TEXT_COLOR = (0, 0, 0)
TEXT_THICCNESS = 2
TEXT_WRAP = int(TEXT_SPACE / (18.5 * (TEXT_SIZE + 0.5)))

TEXT_DATA_FILENAME = 'textFile.txt'

# Server
ROUTE = '/overlay_stream'