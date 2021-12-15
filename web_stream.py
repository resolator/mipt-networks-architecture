#!/usr/bin/env python3
# -*- coding: utf-8 -*
"""Raspberry Pi web streaming server."""
import io
import time
import logging
import argparse
import socketserver

from http import server
from picamera import PiCamera
from threading import Condition
from picamera import PiCamera
from picamera.array import PiRGBArray


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        '--resolution',
        default='640x480',
        choices=['640x480', '1280x720', '1920x1080'],
        help='Camera resolution. Default - 640x480.'
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=25,
        choices=[25, 30, 60],
        help='Frames per second. Default - 25.'
    )
    parser.add_argument(
        '--rotation',
        type=int,
        default=0,
        choices=[0, 90, 180, 270],
        help='Frame rotation. Default - 0.'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for web server.'
    )

    return parser.parse_args()


class StreamingOutput():
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()

            self.buffer.seek(0)

        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()

        elif self.path == '/index.html':
            content = self.page.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type',
                             'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()

            try:
                while True:
                    with self.output.condition:
                        self.output.condition.wait()
                        frame = self.output.frame

                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')

            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address,
                    str(e)
                )
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    def __init__(self, address, handler, output, width=640, height=480):
        super().__init__(address, handler)

        self.allow_reuse_address = True
        self.daemon_threads = True

        handler.output = output
        handler.page = f"""\
            <html>
            <head>
            <title>rpi MJPEG stream</title>
            </head>
            <body>
            <center>
            <h1>RaspberryPi camera MJPEG stream</h1>
            <img src="stream.mjpg" width="{width}" height="{height}" />
            </center>
            </body>
            </html>
            """


def capture_frame(resolution):
    """Capture a single frame from the Pi camera."""

    # setup camera
    camera = PiCamera(resolution=resolution)
    camera.start_preview()
    time.sleep(2)

    stream = io.BytesIO()

    try:
        camera.capture(stream, 'jpeg')
        stream.seek(0)
    finally:
        camera.close()

    return stream.read()


def main():
    """Application entry point."""
    args = get_args()

    # setup camera
    camera = PiCamera(resolution=args.resolution, framerate=args.fps)
    camera.rotation = args.rotation

    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', args.port)
        width, height = map(int, args.resolution.split('x'))
        server = StreamingServer(
            address, StreamingHandler, output, width, height
        )
        print('Web server has been launched.')
        server.serve_forever()
    finally:
        camera.stop_recording()


if __name__ == '__main__':
    main()
