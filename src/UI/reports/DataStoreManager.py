from reports import Report
from reports.ReportPredictions import ReportPredictions
from utils.Singleton import Singleton


class DataStoreManager(metaclass=Singleton):
    def __init__(self):
        self.text = {}  # {Timestamp, Text}
        self.text_predictions = {}  # {Emotion, True/False}

        self.audio_path = ''
        self.audio_predictions = {}  # {Timestamp, ([Frame], Prediction)} ?

        self.video_predictions = {}  # {Timestamp, (Frame, Prediction)} ? Timestamp = time.time()

        self.start_date = -1
        self.end_date = -1

        self.interviewee_name = "No Name"
        self.interviewer_name = "No Name"

    def insert_audio(self, data):
        self.audio_predictions[data[0]] = data[1]

    def insert_video(self, data):
        self.video_predictions[data[0]] = data[1]

    def insert_text(self, data):
        self.text[data[0]] = data[1]

    def set_text_predictions(self, data):
        self.text_predictions = data

    def set_interviewee_name(self, data):
        self.interviewee_name = data

    def set_interviewer_name(self, data):
        self.interviewer_name = data

    def retrieve_data(self):
        report = Report()
        report.initialize(self)

        report_predictions = ReportPredictions()
        report_predictions.initialize(self)

        self.clear()
        return report, report_predictions

    def clear(self):
        interviewee_name = self.interviewee_name
        interviewer_name = self.interviewer_name
        self.__init__()
        self.interviewee_name = interviewee_name
        self.interviewer_name = interviewer_name
