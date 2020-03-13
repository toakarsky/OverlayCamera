import enum

import cv2

# OverlayCamera
STREAM_URL = 'rtsp://176.103.33.12:554/ChocenPlaza'

OUTPUT_SCALE = 0.6

TEXT_DATA_REFRESH = 1
TEXT_SPACE = 600
TEXT_SIZE = 1
TEXT_FONT = cv2.FONT_HERSHEY_TRIPLEX 
TEXT_COLOR = (0, 0, 0)
TEXT_THICCNESS = 2
TEXT_WRAP = int(TEXT_SPACE / (18.5 * (TEXT_SIZE + 0.5)))

class TEXT_ALIGNMENTS(enum.Enum):
    CENTER = 0
    START = 1
    END = 2

TEXT_ALIGNMENT_HORIZONTAL = TEXT_ALIGNMENTS.CENTER
TEXT_ALIGNMENT_VERTICAL = TEXT_ALIGNMENTS.CENTER
TEXT_MARGINES = [
    # TOP
    100,
    # RIGHT
    0,
    # BOTTOM
    0,
    # LEFT
    200,
]
TEXT_MARGINES_BETWEEN_FILES = [
    # TOP
    200,
    # RIGHT
    0,
    # BOTTOM
    0,
    # LEFT
    200,
]

TEXT_DATA_FILENAMES = ['static_test_file.txt', 'test_text_file.txt']

# Server
ROUTE = '/overlay_stream'
