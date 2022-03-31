from PySide6.QtCore import QThread

import pyaudio


class VoiceEmotionDetectionThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)

        self._channels = 1
        self._frame_rate = 16000
        self._frames_per_buffer = 1024
        self._pyAudioObject = pyaudio.PyAudio()
        self._audio_input_stream = None
        self._frames = []

    def run(self):
        self._audio_input_stream = self._pyAudioObject.open(
            format=pyaudio.paInt16,
            channels=self._channels,
            rate=self._frame_rate,
            input=True,
            frames_per_buffer=self._frames_per_buffer)
        self._audio_input_stream.start_stream()

        while self._audio_input_stream.is_active():
            data = self._audio_input_stream.read(self._frames_per_buffer)
            self._frames.append(data)

        print(len(self._frames))

        if __debug__:
            from utils.Wave import Wave
            wave = Wave()
            wave.write_wave("test.wav", self._frames)

        self._frames.clear()

    def stop_recording(self):
        self._audio_input_stream.stop_stream()
        self._audio_input_stream.close()
