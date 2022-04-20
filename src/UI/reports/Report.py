import uuid


class Report:
    def __init__(self):
        self.id = uuid.uuid4()

        self.interviewee_name = ''
        self.interviewer_name = ''

        self.interview_start_date = -1  # time.time()
        self.interview_end_date = -1    # time.time()

        self.text = {}  # {Timestamp, Text}
        self.text_predictions = None  # (First, Second)

        self.audio_path = ''
        self.audio_predictions = {}  # {Timestamp, ([Frame], Prediction)} ?

        self.video_path = ''
        self.video_predictions = {}  # {Timestamp, ([Frame]/Frame, Prediction)} ?

    @property
    def interview_length(self):
        return self.interview_end_date - self.interview_start_date
