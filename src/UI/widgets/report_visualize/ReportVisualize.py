import os
import uuid

from PySide6.QtCore import QUrl, QSize
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from reports import Report
from reports.ReportPredictions import ReportPredictions

import re
import datetime
from intervaltree import IntervalTree

import cv2
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
from PIL import Image, ImageQt

from utils.SyntaxHighlighter import SyntaxHighlighter


def _initialize_interval(interval_tree, predictions, is_not_text=False):
    keys = list(predictions.keys())

    if len(predictions) < 2:
        return

    threshold = 6000
    size_of_frame = 4000
    interval_tree[0:keys[0]] = predictions[keys[0]]
    for index in range(len(keys) - 1):
        first = keys[index]
        last = keys[index + 1]
        delta = last - first
        if delta > threshold and not is_not_text:
            new_last = last - size_of_frame
            interval_tree[first:new_last] = None
            interval_tree[new_last:last] = predictions[last]
        else:
            interval_tree[first:last] = predictions[last]


class ReportVisualize(QWidget):
    def __init__(self):
        super().__init__()
        self._main_window = None

        self._predictions_data = ReportPredictions()
        self._video_predictions_intervals = IntervalTree()
        self._audio_predictions_intervals = IntervalTree()
        self._text_intervals = IntervalTree()

        self._video_current_interval = None
        self._audio_current_interval = None
        self._text_current_interval = None

        self._report = Report()
        self._video_label = None
        self._audio_label = None
        self._text_area = None
        self._play_button = None
        self._slider = None
        self._current_time = None
        self._total_time = None

        self._player = None
        self._syntax_highlighter = None
        self._slider_is_pressed = False

        self._sample_rate = 16000
        self._no_data_str = str()

    def initialize(self, main_window, report_data, predictions):
        if main_window is None or report_data is None or predictions is None:
            return

        self._main_window = main_window
        self._report.from_dict(report_data)
        self._predictions_data = predictions

        self._initialize_predictions_interval()
        self._initialize_widgets()

    def _initialize_predictions_interval(self):
        self._video_predictions_intervals = IntervalTree()
        self._audio_predictions_intervals = IntervalTree()
        self._text_intervals = IntervalTree()
        _initialize_interval(self._video_predictions_intervals, self._predictions_data.video_predictions)
        _initialize_interval(self._audio_predictions_intervals, self._predictions_data.audio_predictions)
        _initialize_interval(self._text_intervals, self._predictions_data.text, True)

    def _initialize_widgets(self):
        self._slider = self._main_window.ui.report_slider
        self._current_time = self._main_window.ui.label
        self._total_time = self._main_window.ui.label_2

        self._video_label = self._main_window.ui.video_label_report
        self._audio_label = self._main_window.ui.audio_label_report
        self._text_area = self._main_window.ui.text_speech
        self._current_video_prediction = self._main_window.ui.video_label_prediction
        self._current_audio_prediction = self._main_window.ui.audio_label_prediction
        self._text_prediction = self._main_window.ui.text_label_prediction

        self._initialize_labels()
        self._initialize_time_labels()
        self._initialize_play_button()
        self._initialize_slider()

    def _initialize_labels(self):
        self._video_label.clear()
        self._audio_label.clear()
        self._text_area.clear()

        self._text_area.setPlainText('. '.join(self._predictions_data.text.values()))
        self._syntax_highlighter = SyntaxHighlighter(self._text_intervals)
        self._syntax_highlighter.setDocument(self._text_area.document())

        self._text_prediction.setText(
            "Text Emotions Predictions: " + re.sub("[{}']", "", str(self._predictions_data.text_predictions)))

    def _initialize_time_labels(self):
        str_start_time = str(datetime.timedelta(seconds=0))
        str_end_time = str(datetime.timedelta(seconds=round(self._report.interview_length)))

        self._current_time.setText(str_start_time)
        self._total_time.setText(str_end_time)

    def _initialize_play_button(self):
        self._play_button = self._main_window.ui.play_button
        self._play_button.clicked.connect(self.play_audio)

        filename = self._predictions_data.audio_path
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._player.setSource(QUrl.fromLocalFile(filename))

        self._player.mediaStatusChanged.connect(self._media_state_changed)
        self._player.positionChanged.connect(self._position_changed)

    def play_audio(self):
        state = self._player.playbackState()
        if state == QMediaPlayer.StoppedState or state == QMediaPlayer.PausedState:
            self._player.play()
        elif state == QMediaPlayer.PlayingState:
            self._player.pause()

        self._media_state_changed(state)

    def _media_state_changed(self, state):
        icon = QIcon()
        path = u":/icons/images/icons/cil-media-pause.png" if \
            self._player.playbackState() == QMediaPlayer.PlayingState else u":/icons/images/icons/cil-media-play.png"
        icon.addFile(path, QSize(), QIcon.Normal, QIcon.Off)
        self._play_button.setIcon(icon)

    def _position_changed(self, position):
        self._slider.setValue(position)

    def _initialize_slider(self):
        self._slider.setValue(0)
        self._slider.setRange(0, self._report.interview_length * 1000)
        self._slider.valueChanged.connect(self._slider_position)
        self._slider.sliderMoved.connect(self._slider_moved)
        self._slider.sliderPressed.connect(self._slider_pressed)
        self._slider.sliderReleased.connect(self._slider_released)

    def _slider_position(self, value):
        str_current_time = str(datetime.timedelta(seconds=value//1000))
        self._current_time.setText(str_current_time)

        for video_data in self._video_predictions_intervals[value]:
            if video_data.data is None:
                self._video_label.setText("No data")
                self._current_video_prediction.setText(self._no_data_str)
                continue

            if video_data != self._video_current_interval:
                video_frame = video_data.data[0]
                prediction = video_data.data[1]
                self._current_video_prediction.setText("Video Emotion Prediction: " + prediction)
                self._display_frame(video_frame)
                self._video_current_interval = video_data
                break

        for text_data in self._text_intervals[value]:
            if text_data.data is None:
                continue

            if text_data != self._text_current_interval:
                self._text_current_interval = text_data
                text = text_data.data

                self._syntax_highlighter.set_text(text)
                self._syntax_highlighter.set_interval(self._text_current_interval)

                self._text_area.setPlainText(self._text_area.toPlainText())
                break

        for audio_data in self._audio_predictions_intervals[value]:
            if audio_data.data is None:
                self._audio_label.setText("No data")
                self._current_audio_prediction.setText(self._no_data_str)
                continue

            if audio_data != self._audio_current_interval:
                audio_frames = audio_data.data[0]
                prediction = audio_data.data[1]
                self._current_audio_prediction.setText("Audio Emotion Prediction: " + prediction)
                self._audio_current_interval = audio_data

                if not self._slider_is_pressed:
                    self._display_audio_plot(audio_frames)

    def _slider_moved(self, value):
        self._player.setPosition(value)

    def _display_frame(self, frame):
        if frame is None:
            self._video_label.setText("No data")
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame.astype(np.uint8))
        qim = ImageQt.ImageQt(img)
        pm = QPixmap.fromImage(qim)
        self._video_label.setPixmap(pm)

    def _display_audio_plot(self, audio_frames):
        mel_spect = np.abs(
            librosa.stft(audio_frames, n_fft=512, window='hamming', win_length=256, hop_length=128)) ** 2

        # Compute mel spectrogram
        mel_spect = librosa.feature.melspectrogram(S=mel_spect, sr=16000, n_mels=128, fmax=4000)

        # Compute log-mel spectrogram (Convert a power spectrogram (amplitude squared) to decibel (dB) units)
        mel_spect = librosa.power_to_db(mel_spect, ref=np.max)

        dpi = 96
        x_pixels = 650
        y_pixels = 700

        id = str(uuid.uuid4())
        path = "./temp/"
        if not os.path.exists(path):
            os.makedirs(path)
        path = f"./temp/{id}.png"

        plt.figure(figsize=(x_pixels // dpi, y_pixels // dpi), dpi=dpi, frameon=False)
        librosa.display.specshow(mel_spect, y_axis='linear')
        plt.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)

        pixmap = QPixmap(path)
        os.remove(path)
        self._audio_label.setPixmap(pixmap)

    def _slider_pressed(self):
        self._player.pause()
        self._slider_is_pressed = True
        state = self._player.playbackState()
        self._media_state_changed(state)

    def _slider_released(self):
        self._slider_is_pressed = False
        if self._player.position() != 0:
            self._player.play()
            state = self._player.playbackState()
            self._media_state_changed(state)

    def reset(self):
        if self._player is not None:
            self._play_button.clicked.disconnect()

            if self._player.playbackState() == QMediaPlayer.PlayingState:
                self._player.stop()

        if self._slider is not None:
            self._slider.valueChanged.disconnect()
            self._slider.sliderMoved.disconnect()
            self._slider.sliderPressed.disconnect()
            self._slider.sliderReleased.disconnect()
