from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap

from reports import Report
from reports.ReportPredictions import ReportPredictions

import datetime
from intervaltree import IntervalTree

import cv2
import numpy as np
from PIL import Image, ImageQt


def _initialize_interval(interval_tree, predictions):
    keys = list(predictions.keys())

    interval_tree[0:keys[0]] = predictions[keys[0]]
    for index in range(len(keys) - 1):
        first = keys[index]
        last = keys[index + 1]
        delta = last - first
        if delta > 8:
            new_last = last - 4
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
        self._report = Report()
        self._video_label = None
        self._audio_label = None
        # text area
        # button
        self._slider = None
        self._current_time = None
        self._total_time = None

    def initialize(self, main_window, report_data, predictions):
        if main_window is None or report_data is None or predictions is None:
            return

        self._main_window = main_window
        self._report.from_dict(report_data)
        self._predictions_data = predictions

        self._initialize_predictions_interval()
        self.initialize_widgets()

    def _initialize_predictions_interval(self):
        self._video_predictions_intervals = IntervalTree()
        self._audio_predictions_intervals = IntervalTree()
        _initialize_interval(self._video_predictions_intervals, self._predictions_data.video_predictions)
        _initialize_interval(self._audio_predictions_intervals, self._predictions_data.audio_predictions)

    def initialize_widgets(self):
        self._slider = self._main_window.ui.report_slider
        self._current_time = self._main_window.ui.label
        self._total_time = self._main_window.ui.label_2

        self._video_label = self._main_window.ui.video_label_report
        self._audio_label = self._main_window.ui.audio_label_report

        self._initialize_labels()
        self._initialize_time_labels()
        self._initialize_play_button()
        self._initialize_slider()

    def slider_position(self, seconds):
        str_current_time = str(datetime.timedelta(seconds=seconds))
        self._current_time.setText(str_current_time)

        for video_data in self._video_predictions_intervals[seconds]:
            if video_data.data is None:
                self._video_label.setText("No data")
                continue
            video_frame = video_data.data[0]
            prediction = video_data.data[1]
            self._display_frame(video_frame)
            break

    def _display_frame(self, frame):
        if frame is None:
            self._video_label.setText("No data")
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame.astype(np.uint8))
        qim = ImageQt.ImageQt(img)
        pm = QPixmap.fromImage(qim)
        self._video_label.setPixmap(pm)

    def _initialize_labels(self):
        self._video_label.clear()
        self._audio_label.clear()

    def _initialize_time_labels(self):
        str_start_time = str(datetime.timedelta(seconds=0))
        str_end_time = str(datetime.timedelta(seconds=round(self._report.interview_length)))

        self._current_time.setText(str_start_time)
        self._total_time.setText(str_end_time)

    def _initialize_play_button(self):
        pass

    def _initialize_slider(self):
        self._slider.setValue(0)
        self._slider.setRange(0, self._report.interview_length)
        self._slider.sliderMoved.connect(self.slider_position)
