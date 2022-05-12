import speech_recognition as sr

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox
import time

from utils import Manager, Settings
from utils.Logger import Logger

from utils.Timer import Timer

from reports import DataStoreManager

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
        self._data_store_manager = DataStoreManager()

        self._recognizer.energy_threshold = 1000  # minimum audio energy to consider for recording
        self._recognizer.pause_threshold = 0.1  # seconds of non-speaking audio before a phrase is considered complete
        self._recognizer.phrase_threshold = 0.3  # minimum seconds of speaking audio
        self._recognizer.non_speaking_duration = 0.1  # seconds of non-speaking audio being recorded

    def get_new_text(self):
        if len(self._textPredictions) > 0:
            return self._textPredictions.pop(0)
        return None

    def _get_microphone_index(self):
        if Settings.MICROPHONE_INDEX_AND_NAME[0] > -1:
            index = 0
            for _, microphone in enumerate(sr.Microphone.list_microphone_names()):
                print(str(microphone))
                if str(microphone) == Settings.MICROPHONE_INDEX_AND_NAME[1]:
                    return index
        return None

    def work(self):
        if self._recognizer is None:  # This "If" is not tested
            QMessageBox.warning(None, "Text", "Text recognizer not available")
            self._calling_window.ui.emotioTextEdit.appendPlainText("Text recognizer error")
            return

        self._is_running = True
        self._is_paused = False
        print("Index: " + str(self._get_microphone_index()))
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        with sr.Microphone(device_index=self._get_microphone_index()) as source:
            timer = Timer()
            timer.start()

            self._recognizer.adjust_for_ambient_noise(source=source)
            while self._is_running and Settings.TEXT_PREDICTION:
                if self._is_paused:
                    time.sleep(1)
                    continue
                try:
                    audio_text = self._recognizer.listen(source)
                    text = self._recognizer.recognize_google(audio_text)
                    # self._manager.window.ui.emotioTextEdit.insertPlainText(text + ". ")
                    self._textPredictions.append(text)
                    self._data_store_manager.insert_text([timer.record_time(), text])

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
