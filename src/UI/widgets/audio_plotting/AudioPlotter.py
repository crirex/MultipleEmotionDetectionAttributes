from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QValueAxis)
from PySide6.QtCore import (QPointF, Slot)
from PySide6.QtMultimedia import (QAudioFormat, QAudioSource, QMediaDevices)
from PySide6.QtWidgets import QMessageBox

import pyaudio
import threading

SAMPLE_COUNT = 2000
RESOLUTION = 4


def get_audio_format(no_channels=1, sample_rate=16000, sample_format=QAudioFormat.Int16):
    format_audio = QAudioFormat()
    format_audio.setChannelCount(no_channels)
    format_audio.setSampleRate(sample_rate)
    format_audio.setSampleFormat(sample_format)
    return format_audio


class AudioPlotter(QChartView):
    def __init__(self, parent):
        super().__init__(parent=parent)

        input_devices = QMediaDevices.audioInputs()
        if not input_devices:
            QMessageBox.warning(None, "audio", "There is no audio input device available.")

        self.device = input_devices[0]
        self._io_device_plotting = None
        self._audio_input_thread = None
        self._buffer = [QPointF(x, 0) for x in range(SAMPLE_COUNT)]
        self._series = QLineSeries()
        self._chart = QChart()
        self._chart.addSeries(self._series)

        self._axis_x = QValueAxis()
        self._axis_x.setRange(0, SAMPLE_COUNT)
        self._axis_x.setLabelFormat("%g")
        self._axis_x.setTitleText("Samples")

        self._axis_y = QValueAxis()
        self._axis_y.setRange(-1, 1)
        self._axis_y.setTitleText("Audio level")

        self._chart.setAxisX(self._axis_x, self._series)
        self._chart.setAxisY(self._axis_y, self._series)
        self._chart.legend().hide()

        name = self.device.description()
        self._chart.setTitle(f"Data from the microphone ({name})")
        self.setChart(self._chart)
        self._series.append(self._buffer)

        self._audio_input_plotting = QAudioSource(self.device, get_audio_format(1, 8000, QAudioFormat.UInt8), self)

        self._channels = 1
        self._frame_rate = 16000
        self._frames_per_buffer = 1024

        self._pyAudioObject = pyaudio.PyAudio()
        self._audio_input_stream = self._pyAudioObject.open(
            format=pyaudio.paInt16,
            channels=self._channels,
            rate=self._frame_rate,
            input=True,
            frames_per_buffer=self._frames_per_buffer)
        self._frames = []

    def record_voice(self):
        self._audio_input_stream.start_stream()
        while self._audio_input_stream.is_active():
            data = self._audio_input_stream.read(self._frames_per_buffer)
            self._frames.append(data)

    def start_recording(self):
        self._io_device_plotting = self._audio_input_plotting.start()
        self._io_device_plotting.readyRead.connect(self._readyRead)

        self._audio_input_thread = threading.Thread(target=self.record_voice)
        self._audio_input_thread.start()

    def stop_recording(self):
        if self._audio_input_plotting is not None and self._audio_input_stream is not None:
            self._audio_input_plotting.stop()

            self._audio_input_stream.stop_stream()
            self._audio_input_stream.close()

            if __debug__:
                from utils.Wave import Wave
                wave = Wave()
                wave.write_wave("test.wav", self._frames)

    def closeEvent(self, event):
        self.stop_recording()
        event.accept()

    @Slot()
    def _readyRead(self):
        data = self._io_device_plotting.readAll()

        available_samples = data.size() // RESOLUTION
        start = 0
        if available_samples < SAMPLE_COUNT:
            start = SAMPLE_COUNT - available_samples
            for s in range(start):
                self._buffer[s].setY(self._buffer[s + available_samples].y())

        data_index = 0
        for s in range(start, SAMPLE_COUNT):
            value = (ord(data[data_index]) - 128) / 128
            self._buffer[s].setY(value)
            data_index = data_index + RESOLUTION
        self._series.replace(self._buffer)
