import time
import threading
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident
        
import cv2
import textwrap

from .settings import STREAM_URL

from .settings import TEXT_DATA_REFRESH
from .settings import TEXT_SPACE, TEXT_SIZE
from .settings import TEXT_FONT, TEXT_THICCNESS, TEXT_COLOR
from .settings import TEXT_DATA_FILENAMES
from .settings import TEXT_WRAP, TEXT_MARGINES, TEXT_MARGINES_BETWEEN_FILES
from .settings import TEXT_ALIGNMENTS, TEXT_ALIGNMENT_VERTICAL, TEXT_ALIGNMENT_HORIZONTAL

from .settings import OUTPUT_SCALE


class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    last_update = time.time()
    event = CameraEvent()

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            # start background frame thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()

        # wait for a signal from the camera thread
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        return BaseCamera.frame

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    @staticmethod
    def _update():
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def _thread(cls):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame = frame
            BaseCamera.event.set()  # send signal to clients
            time.sleep(0)

            if time.time() - BaseCamera.last_update > TEXT_DATA_REFRESH:
                BaseCamera.last_update = time.time()
                cls._update()
                
        BaseCamera.thread = None


class OverlayCamera(BaseCamera):
    textLines = ['']
    textData = (0, 0)
    offset = (0, 0)
    render_pos = [0, 0]
    width = 0
    height = 0
    
    @staticmethod
    def _update():
        OverlayCamera.textLines = []
        height = 0            
        max_width = 0
        number_of_lines = 0
        for textFileName in TEXT_DATA_FILENAMES:
            if textFileName == None:
                OverlayCamera.textLines.append([])
            try:
                with open(textFileName, 'r') as textData:
                    pureTextLines = [x.strip() for x in textData.readlines()]
                wrappedLines = []
                for pureTextLine in pureTextLines:
                    wrappedLines.extend(textwrap.wrap(pureTextLine, width=TEXT_WRAP))
                OverlayCamera.textLines.append(wrappedLines)

                number_of_lines += len(OverlayCamera.textLines[-1])
                for textLine in wrappedLines:
                    lineSize = cv2.getTextSize(textLine, TEXT_FONT, TEXT_SIZE, TEXT_THICCNESS)[0]
                    max_width = max(max_width, lineSize[0])
                    height = (lineSize[1] + 10) * TEXT_SIZE
            except:
                print(f'[ERROR] File {textFileName} not available')
        OverlayCamera.textData = (max_width, height)
        OverlayCamera.offset = (int(max_width), int(height * number_of_lines))
        # print('yes')
        # print(number_of_lines)
        # print(OverlayCamera.textData)

        OverlayCamera.render_pos = [0, 0]
        if TEXT_ALIGNMENT_VERTICAL == TEXT_ALIGNMENTS.START:
            OverlayCamera.render_pos[1] = 0
        elif TEXT_ALIGNMENT_VERTICAL == TEXT_ALIGNMENTS.CENTER:
            OverlayCamera.render_pos[1] = int(OverlayCamera.height / 2 - OverlayCamera.offset[1] / 2)
        elif TEXT_ALIGNMENT_VERTICAL == TEXT_ALIGNMENTS.END:
            OverlayCamera.render_pos[1] = int(OverlayCamera.height - OverlayCamera.offset[1])
    
        if TEXT_ALIGNMENT_HORIZONTAL == TEXT_ALIGNMENTS.START:
            OverlayCamera.render_pos[0] = 0 + OverlayCamera.width
        elif TEXT_ALIGNMENT_HORIZONTAL == TEXT_ALIGNMENTS.CENTER:
            OverlayCamera.render_pos[0] = int(TEXT_SPACE / 2 - OverlayCamera.offset[0]) + OverlayCamera.width + 1
        elif TEXT_ALIGNMENT_HORIZONTAL == TEXT_ALIGNMENTS.END:
            OverlayCamera.render_pos[0] = int(TEXT_SPACE - OverlayCamera.offset[0]) + OverlayCamera.width + 1
        
        OverlayCamera.render_pos[0] += (TEXT_MARGINES[3] - TEXT_MARGINES[1])
        OverlayCamera.render_pos[1] += (TEXT_MARGINES[0] - TEXT_MARGINES[2])
    
    @staticmethod
    def frames():
        vcap = cv2.VideoCapture(STREAM_URL)
        if not vcap.isOpened():
            raise RuntimeError('Could not start camera.')
        
        OverlayCamera.width = int(vcap.get(3))
        OverlayCamera.height = int(vcap.get(4))
        
        DIM = (int((TEXT_SPACE + vcap.get(3)) * OUTPUT_SCALE), int(vcap.get(4) * OUTPUT_SCALE))

        OverlayCamera._update()
        last_frame = None
        while True:
            # read current frame
            _, frame = vcap.read()
            frame = cv2.copyMakeBorder(frame, 0, 0, 0, TEXT_SPACE, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            y = 0
            x = 0
            try:
                for textFile in OverlayCamera.textLines:
                    for line in textFile:
                        cv2.putText(frame, line, (OverlayCamera.render_pos[0] + x, OverlayCamera.render_pos[1] + y), TEXT_FONT, TEXT_SIZE, TEXT_COLOR, TEXT_THICCNESS)
                        y += OverlayCamera.textData[1]
                    y += TEXT_MARGINES_BETWEEN_FILES[0] - TEXT_MARGINES_BETWEEN_FILES[2]
                    x += TEXT_MARGINES_BETWEEN_FILES[3] - TEXT_MARGINES_BETWEEN_FILES[1]
            except:
                print('[ERROR] Something wrong with text')

            frame = cv2.resize(frame, DIM, interpolation = cv2.INTER_AREA)
            
            # encode as a jpeg image and return it
            try:
                yield cv2.imencode('.jpg', frame)[1].tobytes()
            except:
                yield cv2.imencode('.jpg', last_frame)[1].tobytes()
            else:
                last_frame = frame
