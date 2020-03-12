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
from .settings import TEXT_DATA_FILENAME
from .settings import TEXT_WRAP


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
                
                
            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()
                print('Stopping camera thread due to inactivity.')
                break
        BaseCamera.thread = None


class OverlayCamera(BaseCamera):
    textLines = ['']
    textData = (0, 0)
    offset = (0, 0)
    
    @staticmethod
    def _update():
        try:
            with open(TEXT_DATA_FILENAME, 'r') as textData:
                pureTextLines = [x.strip() for x in textData.readlines()]
            OverlayCamera.textLines = []
            for pureTextLine in pureTextLines:
                OverlayCamera.textLines.extend(textwrap.wrap(pureTextLine, width=TEXT_WRAP))

            height = 0            
            max_width = 0
            for textLine in OverlayCamera.textLines:
                lineSize = cv2.getTextSize(textLine, TEXT_FONT, TEXT_SIZE, TEXT_THICCNESS)[0]
                max_width = max(max_width, lineSize[0])
                height = lineSize[1] + 10 * TEXT_SIZE
            OverlayCamera.textData = (max_width, height)
            OverlayCamera.offset = (int(max_width / 2), int(height * len(OverlayCamera.textLines) / 2))
        except:
            print('[ERROR] File not available')
    
    @staticmethod
    def frames():
        vcap = cv2.VideoCapture(STREAM_URL)
        if not vcap.isOpened():
            raise RuntimeError('Could not start camera.')
        
        width = int(vcap.get(3))
        height = int(vcap.get(4))
        
        OverlayCamera._update()
        last_frame = None
        while True:
            # read current frame
            _, frame = vcap.read()
            frame = cv2.copyMakeBorder(frame, 0, 0, 0, TEXT_SPACE, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            y = int(height / 2 - OverlayCamera.offset[1])
            for line in OverlayCamera.textLines:
                y += OverlayCamera.textData[1]
                cv2.putText(frame, line, (width + int(TEXT_SPACE / 2) - OverlayCamera.offset[0], y), TEXT_FONT, TEXT_SIZE, TEXT_COLOR, TEXT_THICCNESS)
            
            # encode as a jpeg image and return it
            try:
                yield cv2.imencode('.jpg', frame)[1].tobytes()
            except:
                yield cv2.imencode('.jpg', last_frame)[1].tobytes()
            else:
                last_frame = frame