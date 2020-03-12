from flask import Flask, render_template, Response

from .OverlayCamera import OverlayCamera

from .settings import ROUTE


app = Flask(__name__)

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route(ROUTE)
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(OverlayCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

