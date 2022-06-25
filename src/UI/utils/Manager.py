import cv2
import dlib
import numpy as np

from tensorflow.keras.models import load_model
from utils.Singleton import Singleton


class Manager(metaclass=Singleton):
    def __init__(self):
        self.app = None
        self.window = None

        self.video_model = load_model('Models/video.h5', compile=False)
        self.video_predictor_landmarks = dlib.shape_predictor("Models/face_landmarks.dat")
        self.active_camera = cv2.VideoCapture(0)

        self.lightTheme = False

        self.audio_model = load_model('Models/audio_v2.hdf5', compile=False)
        self.prepare_manager()

    def prepare_manager(self):
        _, _ = self.active_camera.read()  # Actually opening up the camera
        _ = self.video_model.predict(np.zeros((1, 48, 48, 1)))  # False prediction for spike lag
        _ = self.audio_model.predict(np.zeros((1, 5, 128, 128, 1)))

    def is_camera_available(self):
        if self.active_camera is None or not self.active_camera.isOpened():
            return False
        return True

    def release_resources(self):
        if self.is_camera_available():
            self.active_camera.release()
            self.active_camera = None

    def quit_app(self):
        if self.app is not None:
            self.app.quit()
