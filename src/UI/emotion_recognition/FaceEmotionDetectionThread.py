from PySide6.QtCore import QObject
from reports import DataStoreManager
from utils import Manager


class FaceEmotionDetectionThread(QObject):
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent

        self._manager = Manager()
        self._data_store_manager = DataStoreManager()

        self._is_running = False
        self._classes = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Sad', 5: 'Surprise', 6: 'Neutral'}

        self._data_to_predict_list = []  # [(timestamp, y),...]
        self._predictions = []

    def _predict(self, data):
        return self._manager.video_model.predict(data)

    def work(self):
        self._is_running = True
        while self._is_running or len(self._data_to_predict_list) > 0:

            timestamp, data = self._data_to_predict_list.pop(0)
            if data is None or len(data) == 0:
                continue

            predictions = self._predict(data)
            if predictions is not None:
                prediction = predictions[0]
                self._predictions.append(prediction)

    def queue_data(self, data):
        self._data_to_predict_list.append(data)

    def abort(self):
        self._is_running = False

    def get_latest_prediction(self):
        if len(self._predictions) == 0:
            return None

        return self._predictions.pop(0)
