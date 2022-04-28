from reports import Report
from reports.ReportPredictions import ReportPredictions
from utils.Singleton import Singleton


class DataStoreManager(metaclass=Singleton):
    def __init__(self):
        self.text = {}  # {Timestamp, Text}
        self.text_predictions = ()  # (First, Second)

        self.audio_path = ''
        self.audio_predictions = {}  # {Timestamp, ([Frame], Prediction)} ?

        self.video_predictions = {}  # {Timestamp, (Frame, Prediction)} ? Timestamp = time.time()

        self.start_date = -1
        self.end_date = -1

    def insert_audio(self, data):
        self.audio_predictions[data[0]] = data[1]

    def insert_video(self, data):
        self.video_predictions[data[0]] = data[1]

    def insert_text(self, data):
        self.text[data[0]] = data[1]

    def set_text_predictions(self, data):
        self.text_predictions = data

    def retrieve_data(self):
        report = Report()
        report.initialize(self)

        report_predictions = ReportPredictions()
        report_predictions.initialize(self)

        self.clear()
        return report, report_predictions

    def clear(self):
        self.__init__()
