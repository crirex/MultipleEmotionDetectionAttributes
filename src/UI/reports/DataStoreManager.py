from utils.Singleton import Singleton


class DataStoreManager(metaclass=Singleton):
    def __init__(self):
        self.text = {}  # {Timestamp, Text}
        self.text_predictions = ()  # (First, Second)
        self.audio_predictions = {}  # {Timestamp, ([Frame], Prediction)} ?
        self.video_predictions = {}  # {Timestamp, ([Frame]/Frame, Prediction)} ?

    def insert_audio(self, data):
        self.audio_predictions[data[0]] = data[1]

    def insert_video(self, data):
        self.video_predictions[data[0]] = data[1]
        print(len(self.video_predictions))

    def insert_text(self, data):
        self.text[data[0]] = data[1]

    def set_text_predictions(self, data):
        self.text_predictions = data
