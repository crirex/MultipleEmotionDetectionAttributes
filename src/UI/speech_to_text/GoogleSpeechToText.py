import speech_recognition as sr
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox

from utils.Logger import Logger


class GoogleSpeechToText(QObject):
    sig_step = pyqtSignal(int, str)  # worker id, step description: emitted every step through work() loop
    sig_done = pyqtSignal(int)  # worker id: emitted at end of work()
    sig_msg = pyqtSignal(str)  # message to be shown to user

    def __init__(self, parent=None):
        super().__init__()
        self._calling_window = parent
        self._is_running = True
        self._logger = Logger()
        self._recognizer = sr.Recognizer()

        self._textPredictions = []

    def get_new_text(self):
        if len(self._textPredictions) > 0:
            return self._textPredictions.pop(0)
        return None

    @pyqtSlot()
    def work(self):
        print("working")
        if self._recognizer is None:  # This "If" is not tested
            QMessageBox.warning(None, "Text", "Text recognizer not available")
            self._calling_window.ui.labelVideo.setText("Text recognizer error")
            return

        self._is_running = True
        with sr.Microphone() as source:
            while self._is_running:
                audio_text = self._recognizer.listen(source)
                try:
                    text = self._recognizer.recognize_google(audio_text)
                    self._textPredictions.append(text)
                    print(text)
                except OSError as ex:
                    self._logger.log_error(ex)
                    self._is_running = False
                    raise Exception(ex)
                except Exception:
                    # Do nothing
                    print("Bad text")

    def abort(self):
        self.sig_msg.emit('Worker FaceDetection notified to abort')
        self._abort = True
        self._is_running = False
