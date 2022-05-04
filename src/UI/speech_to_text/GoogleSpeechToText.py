import speech_recognition as sr

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox
import time

from utils import Manager
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
        self._manager = Manager()

        self._recognizer.energy_threshold = 1000  # minimum audio energy to consider for recording
        self._recognizer.pause_threshold = 0.1  # seconds of non-speaking audio before a phrase is considered complete
        self._recognizer.phrase_threshold = 0.3  # minimum seconds of speaking audio
        self._recognizer.non_speaking_duration = 0.1  # seconds of non-speaking audio being recorded

        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

    def get_new_text(self):
        if len(self._textPredictions) > 0:
            return self._textPredictions.pop(0)
        return None

    def work(self):
        if self._recognizer is None:  # This "If" is not tested
            QMessageBox.warning(None, "Text", "Text recognizer not available")
            self._calling_window.ui.emotioTextEdit.appendPlainText("Text recognizer error")
            return

        self._is_running = True
        self._is_paused = False
        with sr.Microphone() as source:
            self._recognizer.adjust_for_ambient_noise(source=source)
            while self._is_running:
                if self._is_paused:
                    time.sleep(1)
                    continue
                try:
                    audio_text = self._recognizer.listen(source)
                    text = self._recognizer.recognize_google(audio_text)
                    self._manager.window.ui.emotioTextEdit.insertPlainText(text + ". ")
                except OSError as ex:
                    print(ex.args)
                    self._logger.log_error(ex)
                    self._is_running = False
                    raise Exception(ex)
                except sr.UnknownValueError:
                    # An exception that isn't bad at all (Recognizer couldn't detect the text)
                    pass
                except Exception as ex:
                    print(ex.args)
                    raise Exception(ex)

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def abort(self):
        self._is_running = False

    def stop(self):
        self._is_running = False
