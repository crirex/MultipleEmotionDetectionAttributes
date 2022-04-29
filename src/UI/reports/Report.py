import uuid


class Report:
    def __init__(self):
        self._id = str(uuid.uuid4())
        self.predictions_id = None

        self.interviewee_name = ''
        self.interviewer_name = ''

        self.interview_start_date = -1  # time.time()
        self.interview_end_date = -1    # time.time()

        self.interview_length = -1

    def from_dict(self, report_dict):
        for key in report_dict:
            setattr(self, key, report_dict[key])
        return self

    def initialize(self, data_store_manager):
        # Alternative until we can get both names from settings
        self.interviewee_name = "Test_interviewee_name"
        self.interviewer_name = "Test_interviewer_name"

        self.interview_start_date = data_store_manager.start_date
        self.interview_end_date = data_store_manager.end_date

        self.interview_length = self.interview_end_date - self.interview_start_date
