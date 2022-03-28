import cv2
import dlib
import numpy as np

from tensorflow.keras.models import load_model
from utils.Singleton import Singleton

# class Manager(Singleton):
class Manager(metaclass=Singleton):

    def __init__(self):
        self.videoThread = None
        self.videoModel = load_model('Models/video.h5', compile=False)
        self.videoPredictorLandmarks = dlib.shape_predictor("Models/face_landmarks.dat")
        self.activeCamera = cv2.VideoCapture(0)

        self.prepareManager()

    def prepareManager(self):
        _, _ = self.activeCamera.read()  # Actually opening up the camera
        _ = self.videoModel.predict(np.zeros((1, 48, 48, 1)))  # False prediction for spike lag
