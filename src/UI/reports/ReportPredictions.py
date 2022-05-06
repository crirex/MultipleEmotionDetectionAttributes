class ReportPredictions:
    def __init__(self):
        self.text = {}  # {Timestamp, Text}
        self.text_predictions = {}  # (First, Second)

        self.audio_path = ''
        self.audio_predictions = {}  # {Timestamp, ([Frame], Prediction)}

        self.video_predictions = {}  # {Timestamp, (Frame, Prediction)}

    def initialize(self, data_store_manager):
        self.text = data_store_manager.text
        self.text_predictions = data_store_manager.text_predictions

        self.audio_path = data_store_manager.audio_path

        self.audio_predictions = data_store_manager.audio_predictions

        self.video_predictions = data_store_manager.video_predictions

    def from_dict(self, prediction_dict):
        for key in prediction_dict:
            setattr(self, key, prediction_dict[key])
        return self
