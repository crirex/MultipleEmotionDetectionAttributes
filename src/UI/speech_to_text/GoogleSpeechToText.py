import speech_recognition as sr

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from utils.Logger import Logger


class GoogleSpeechToText(QObject):
    def __init__(self, parent=None):
        super().__init__()
        self._calling_window = parent
        self._is_running = False
        self._is_paused = False
        self._logger = Logger()
        self._recognizer = sr.Recognizer()
        self._textPredictions = []

    def get_new_text(self):
        if len(self._textPredictions) > 0:
            return self._textPredictions.pop(0)
        return None

    def work(self):
        if self._recognizer is None:  # This "If" is not tested
            QMessageBox.warning(None, "Text", "Text recognizer not available")
            self._calling_window.ui.labelVideo.setText("Text recognizer error")
            return

        self._is_running = True
        with sr.Microphone() as source:
            while self._is_running:
                if self._is_paused:
                    print("Text to speech is paused")
                    continue
                audio_text = self._recognizer.listen(source)
                try:
                    text = self._recognizer.recognize_google(audio_text)
                    self._textPredictions.append(text)
                except OSError as ex:
                    self._logger.log_error(ex)
                    self._is_running = False
                    raise Exception(ex)
                except Exception:
                    # Do nothing
                    pass

    def pause(self):
        self._is_paused = True

    def abort(self):
        self._is_running = False

    def stop(self):
        self._is_running = False
