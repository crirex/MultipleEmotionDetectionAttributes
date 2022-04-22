from PySide6.QtCore import QObject

import numpy as np
from scipy.stats import zscore
import librosa

from reports import DataStoreManager
from utils import Manager
import time


class VoiceEmotionPredictionThread(QObject):
    def __init__(self, parent=None):
        super().__init__()
        self._parent = parent
        self._chunk_step = 16000
        self._chunk_size = 49100

        self._manager = Manager()
        self._data_store_manager = DataStoreManager()

        self._emotion = {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Neutral', 5: 'Sad', 6: 'Surprise'}
        self._is_running = False

        self._data_to_predict_list = []  # [(timestamp, y),...]
        self._predictions = []

    def _frame(self, y, win_step=64, win_size=128):
        # Number of frames
        nb_frames = 1 + int((y.shape[2] - win_size) / win_step)

        # Framing
        frames = np.zeros((y.shape[0], nb_frames, y.shape[1], win_size)).astype(np.float16)
        for t in range(nb_frames):
            frames[:, t, :, :] = np.copy(y[:, :, (t * win_step):(t * win_step + win_size)]).astype(np.float16)

        return frames

    def _mel_spectrogram(self, y, sr=16000, n_fft=512, win_length=256, hop_length=128, window='hamming', n_mels=128,
                        fmax=4000):

        # Compute spectogram
        mel_spect = np.abs(
            librosa.stft(y, n_fft=n_fft, window=window, win_length=win_length, hop_length=hop_length)) ** 2

        # Compute mel spectrogram
        mel_spect = librosa.feature.melspectrogram(S=mel_spect, sr=sr, n_mels=n_mels, fmax=fmax)

        # Compute log-mel spectrogram (Convert a power spectrogram (amplitude squared) to decibel (dB) units)
        mel_spect = librosa.power_to_db(mel_spect, ref=np.max)

        return np.asarray(mel_spect)

    def _predict_audio(self, y):
        if y is None or len(y) < self._chunk_size:
            return None

        # preprocess
        chunks = self._frame(y.reshape(1, 1, -1), self._chunk_step, self._chunk_size)
        chunks = chunks.reshape(chunks.shape[1], chunks.shape[-1])

        # ZScore - normalization
        y = np.asarray(list(map(zscore, chunks)))

        # MelSpectograms
        mel_spect = np.asarray(list(map(self._mel_spectrogram, y)))

        # Time distributed Framing
        mel_spectogram_time_distrib = self._frame(mel_spect)

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

    def work(self):
        self._is_running = True
        while self._is_running or len(self._data_to_predict_list) > 0:
            if self._is_running:
                print("Sleeping for 2 seconds zzz")
                time.sleep(2)

            if len(self._data_to_predict_list) == 0:
                continue

            timestamp, data = self._data_to_predict_list.pop(0)
            if data is None or len(data) == 0:
                continue

            if self._predict_audio(data) is not None:
                prediction = self._predict_audio(data)[0]
                self._predictions.append(prediction)
                self._data_store_manager.insert_audio((timestamp, (data, prediction)))

    def queue_data(self, data):
        self._data_to_predict_list.append(data)

    def abort(self):
        self._is_running = False

    def get_latest_prediction(self):
        if len(self._predictions) == 0:
            return None

        return self._predictions.pop(0)
