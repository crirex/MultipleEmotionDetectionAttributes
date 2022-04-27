from PySide6.QtCore import QObject

import time
import pyaudio
import uuid
import os

from emotion_recognition.VoiceEmotionPredictionThread import VoiceEmotionPredictionThread
from reports import DataStoreManager
from utils import Manager, Logger
from utils.Wave import WaveUtils


class VoiceEmotionDetectionThread(QObject):
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent
        self._logger = Logger()

        self._channels = 1
        self._frame_rate = 16000
        self._frames_per_buffer = 1024
        self._no_sec_predict = 3

        self._pyAudioObject = pyaudio.PyAudio()
        self._audio_input_stream = None
        self._is_paused = False

        self._frames_to_predict = []
        self._frames = []

        self._emotion = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Neutral', 5: 'Sad', 6: 'Surprise'}
        self._chunk_step = 16000
        self._chunk_size = 49100

        self.voice_prediction = VoiceEmotionPredictionThread()
        self._voice_prediction_thread = None
        self._manager = Manager()
        self._data_store_manager = DataStoreManager()

    def read_intermediate_wave(self, wave_utils):
        path = "./temp/"
        if not os.path.exists(path):
            os.makedirs(path)
        file_name = path + str(uuid.uuid4()) + '.wav'
        wave_utils.write_wave(file_name, self._frames_to_predict[:])
        data, _ = wave_utils.load_wave(file_name)
        os.remove(file_name)
        return data

    def work(self):
        self._is_paused = False
        self._audio_input_stream = self._pyAudioObject.open(
            format=pyaudio.paInt16,
            channels=self._channels,
            rate=self._frame_rate,
            input=True,
            frames_per_buffer=self._frames_per_buffer)
        self._audio_input_stream.start_stream()

        wave_utils = WaveUtils()
        start_time = time.time()
        time_format = "%Y-%m-%d %H:%M:%S"
        try:
            while self._audio_input_stream.is_active():
                data = self._audio_input_stream.read(self._frames_per_buffer)
                self._frames.append(data)

                if self._is_paused and len(self._frames_to_predict) == 0:
                    start_time = time.time()
                    continue

                latest_prediction = self.voice_prediction.get_latest_prediction()
                if latest_prediction is not None:
                    date = time.localtime(time.time())
                    str_prediction = f"Current voice emotion detect as: {latest_prediction} | {time.strftime(time_format, date)} "
                    self._parent.chart.setTitle(str_prediction)
                    print(str_prediction)

                self._frames_to_predict.append(data)
                current_time = time.time()
                seconds_passed = current_time - start_time
                if seconds_passed > 4:
                    print("4 seconds passed")
                    if not self._is_paused:
                        # data = wave_utils.convert_to_wave(self._frames)
                        # Alternative method until I fix the stuff with reading from byte class
                        data = self.read_intermediate_wave(wave_utils)
                        self.voice_prediction.queue_data((current_time, data))

                    self._frames_to_predict.clear()
                    start_time = time.time()

            self.voice_prediction.abort()
            path = "./candidate_speech/"
            if not os.path.exists(path):
                os.makedirs(path)
            wave_utils.write_wave(path + str(uuid.uuid4()) + ".wav", self._frames)
            self._frames.clear()

        except Exception as ex:
            self._logger.log_error(ex)
            raise Exception(ex)

    def process_audio_file(self, filename):
        # load audio file
        y, _ = WaveUtils().load_wave(filename)
        return self.predict_audio(y)

    def stop_prediction(self):
        self._audio_input_stream.stop_stream()

        # This caused the app to close when you stopped/paused,
        # self._audio_input_stream.close()

    def pause_prediction(self):
        self._is_paused = True
        self._parent.chart.setTitle("Prediction is paused ")

    def resume_prediction(self):
        self._is_paused = False

    def abort(self):
        self.stop_prediction()
