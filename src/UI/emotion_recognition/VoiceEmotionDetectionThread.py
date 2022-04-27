from PySide6.QtCore import QObject, QThread

import time
import librosa
import pyaudio
import numpy as np
from scipy.stats import zscore
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

    def frame(self, y, win_step=64, win_size=128):
        # Number of frames
        nb_frames = 1 + int((y.shape[2] - win_size) / win_step)

        # Framing
        frames = np.zeros((y.shape[0], nb_frames, y.shape[1], win_size)).astype(np.float16)
        for t in range(nb_frames):
            frames[:, t, :, :] = np.copy(y[:, :, (t * win_step):(t * win_step + win_size)]).astype(np.float16)

        return frames

    def mel_spectrogram(self, y, sr=16000, n_fft=512, win_length=256, hop_length=128, window='hamming', n_mels=128,
                        fmax=4000):

        # Compute spectogram
        mel_spect = np.abs(
            librosa.stft(y, n_fft=n_fft, window=window, win_length=win_length, hop_length=hop_length)) ** 2

        # Compute mel spectrogram
        mel_spect = librosa.feature.melspectrogram(S=mel_spect, sr=sr, n_mels=n_mels, fmax=fmax)

        # Compute log-mel spectrogram (Convert a power spectrogram (amplitude squared) to decibel (dB) units)
        mel_spect = librosa.power_to_db(mel_spect, ref=np.max)

        return np.asarray(mel_spect)

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
        try:
            while self._audio_input_stream.is_active():
                data = self._audio_input_stream.read(self._frames_per_buffer)
                self._frames.append(data)

                if self._is_paused and len(self._frames_to_predict) == 0:
                    start_time = time.time()
                    continue

                latest_prediction = self.voice_prediction.get_latest_prediction()
                if latest_prediction is not None:
                    str_prediction = f"Current voice emotion detect as: {latest_prediction}"
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

    def predict_audio(self, y):
        if y is None or len(y) < self._chunk_size:
            self._logger.log_warning(f"Data to predict is None or the length is smaller than {self._chunk_size}")
            return None

        # preprocess
        chunks = self.frame(y.reshape(1, 1, -1), self._chunk_step, self._chunk_size)
        chunks = chunks.reshape(chunks.shape[1], chunks.shape[-1])

        # ZScore - normalization
        y = np.asarray(list(map(zscore, chunks)))

        # MelSpectograms
        mel_spect = np.asarray(list(map(self.mel_spectrogram, y)))

        # Time distributed Framing
        mel_spectogram_time_distrib = self.frame(mel_spect)

        # predict
        x = mel_spectogram_time_distrib.reshape(mel_spectogram_time_distrib.shape[0],
                                                mel_spectogram_time_distrib.shape[1],
                                                mel_spectogram_time_distrib.shape[2],
                                                mel_spectogram_time_distrib.shape[3],
                                                1)
        predict = self._manager.audio_model.predict(x)
        predict = np.argmax(predict, axis=1)
        predict = [self._emotion.get(emotion) for emotion in predict]
        return predict

    def stop_prediction(self):
        self._audio_input_stream.stop_stream()
        # self._audio_input_stream.close()

    def pause_prediction(self):
        self._is_paused = True
        self._parent.chart.setTitle("Prediction is paused ")

    def resume_prediction(self):
        self._is_paused = False

    def abort(self):
        self.stop_prediction()
