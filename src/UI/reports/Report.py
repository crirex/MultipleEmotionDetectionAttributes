import uuid


class Report:
    def __init__(self):
        self._id = str(uuid.uuid4())
        self.predictions_id = None

        self.interviewee_name = 'No Name'
        self.interviewer_name = 'No Name'

        self.interview_start_date = -1  # time.time()
        self.interview_end_date = -1    # time.time()

        self.interview_length = -1

    def from_dict(self, report_dict):
        for key in report_dict:
            setattr(self, key, report_dict[key])
        return self

    def initialize(self, data_store_manager):
        self.interviewee_name = data_store_manager.interviewee_name
        self.interviewer_name = data_store_manager.interviewer_name

        self.interview_start_date = data_store_manager.start_date
        self.interview_end_date = data_store_manager.end_date

        self.interview_length = self.interview_end_date - self.interview_start_date
