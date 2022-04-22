import os
import sys

import cv2
import numpy as np
from PySide6.QtCore import QThread

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QHeaderView, QApplication

from PIL import Image, ImageQt
from transitions import MachineError

from emotion_recognition import FaceDetectionThread
from modules import *
from speech_to_text import GoogleSpeechToText
from utils import Manager
from utils.Logger import Logger
from utils.StateManager import StateManager

os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%

widgets = None


def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class MainWindow(QMainWindow):
    logger = Logger()

    def __init__(self):
        QMainWindow.__init__(self)
        self.__threads = []
        self.face_detection_thread = FaceDetectionThread(self)
        self.speech_to_text_thread = GoogleSpeechToText(self)

        self.ui = Ui_MainWindow()

        self._video_timer = QTimer()
        self._speech_to_text_timer = QTimer()

        self.ui.setupUi(self)

        self._state_manager = StateManager(self)
        self._manager = Manager()

        global widgets
        widgets = self.ui

        Settings.ENABLE_CUSTOM_TITLE_BAR = False
        Settings.THREAD_REFERENCE = self.face_detection_thread

        title = "Multimodal Emotion Detection"
        self.setWindowTitle(title)

        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        UIFunctions.uiDefinitions(self)

        widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        widgets.btn_home.clicked.connect(self.button_click)
        widgets.btn_widgets.clicked.connect(self.button_click)
        widgets.btn_new.clicked.connect(self.button_click)
        widgets.btn_exit.clicked.connect(self.button_click)

        widgets.startButton.clicked.connect(self.button_click)
        widgets.cancelButton.clicked.connect(self.button_click)
        widgets.pauseButton.clicked.connect(self.button_click)

        self._button_to_action = {
            'btn_home': self.button_home_click,
            'btn_widgets': self.button_reports_click,
            'btn_new': self.button_recognition_click,
            'btn_exit': self.button_exit_click,
            'startButton': self.button_start_recognition_click,
            'cancelButton': self.button_stop_recognition_click,
            'pauseButton': self.button_pause_recognition_click
        }

        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)

        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)

        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)

        self.show()

        useCustomTheme = False
        themeFile = "themes\py_dracula_light.qss"

        if useCustomTheme:
            UIFunctions.theme(self, themeFile, True)

            AppFunctions.setThemeHack(self)

        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    def button_home_click(self, button, button_name):
        self._state_manager.button_home_clicked(button, button_name, widgets.home)

    def button_reports_click(self, button, button_name):
        self._state_manager.button_reports_clicked(button, button_name, widgets.widgets)

    def button_recognition_click(self, button, button_name):
        self._state_manager.button_recognition_clicked(button, button_name, widgets.new_page)

    def button_exit_click(self, button, button_name):
        self._state_manager.button_exit_clicked(button, button_name)
        self.abort_workers()

    def button_start_recognition_click(self, button, button_name):
        self._state_manager.button_start_recognition_clicked(button, button_name)

    def start_recognition(self):
        # Video
        self._video_timer.timeout.connect(self.display_video_stream)
        self._video_timer.start(30)

        # Audio
        self.ui.audioPlotterWidget.start_plotting()

        # SpeechToText
        self._speech_to_text_timer.timeout.connect(self.display_text_from_speech)
        self._speech_to_text_timer.start(2000)

        self.start_thread(self.face_detection_thread, "face_detection_thread")
        self.start_thread(self.speech_to_text_thread, "speech_to_text_thread")
        self.start_thread(self.ui.audioPlotterWidget.audio_recording_thread, "audio_detection_thread")
        self.start_thread(self.ui.audioPlotterWidget.audio_recording_thread.voice_prediction, "audio_prediction_thread")

    def resume_recognition(self):
        self.face_detection_thread.resume_running()
        self.ui.audioPlotterWidget.resume_prediction()
        self.speech_to_text_thread.resume()

    def button_stop_recognition_click(self, button, button_name):
        self._state_manager.button_stop_recognition_clicked(button, button_name)

    def stop_recognition(self):
        # Video
        self._video_timer.stop()
        self._speech_to_text_timer.stop()
        self.face_detection_thread.stop_running()

        # Speech to text
        self.speech_to_text_thread.stop()

        # Audio
        self.ui.audioPlotterWidget.stop_prediction()

    def button_pause_recognition_click(self, button, button_name):
        self._state_manager.button_pause_recognition_clicked(button, button_name)

    def pause_recognition(self):
        self.face_detection_thread.pause_running()
        self.ui.audioPlotterWidget.pause_prediction()
        self.speech_to_text_thread.pause()

    def button_click(self):
        button = self.sender()
        button_name = button.objectName()

        if button_name in self._button_to_action:
            try:
                self._button_to_action[button_name](button, button_name)
                print(self._state_manager.state)
            except MachineError as machine_error:
                MainWindow.logger.log_warning(machine_error.value)
            except Exception as exception:
                MainWindow.logger.log_error(exception.value)

    def display_text_from_speech(self):
        new_text = self.speech_to_text_thread.get_new_text()
        if new_text is not None:
            print(new_text)
            self.ui.emotioTextEdit.appendPlainText(new_text + ". ")

    def display_video_stream(self):
        frame = self.face_detection_thread.get_frame()
        if frame is None:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame.astype(np.uint8))
        qim = ImageQt.ImageQt(img)
        pm = QPixmap.fromImage(qim)
        self.ui.labelVideo.setPixmap(pm)

    def start_thread(self, worker, name):
        thread = QThread()
        thread.setObjectName('thread_' + name)
        self.__threads.append((thread, worker))  # need to store worker too otherwise will be gc'd
        worker.moveToThread(thread)

        # get read to start worker:
        thread.started.connect(worker.work)
        thread.start()  # this will emit 'started' and start thread's event loop

    def abort_workers(self):
        self.logger.log_debug('Asking each worker to abort')
        for thread, worker in self.__threads:  # note nice unpacking by Python, avoids indexing
            worker.abort()
            thread.quit()  # this will quit **as soon as thread event loop unblocks**
            thread.wait()  # <- so you need to wait for it to *actually* quit

        # even though threads have exited, there may still be messages on the main thread's
        # queue (messages that threads emitted before the abort):
        self.__threads.clear()
        self.logger.log_debug('All threads exited')

    def closeEvent(self, event):
        self._state_manager.button_exit_clicked(None, "Exit")
        self.abort_workers()

    def reset_style(self, button_name):
        UIFunctions.resetStyle(self, button_name)

    def select_menu_style(self, button):
        return UIFunctions.selectMenu(button.styleSheet())


if __name__ == "__main__":
    MainWindow.logger.log_info("Application starts")

    Manager.app = QApplication(sys.argv)
    Manager.app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(Manager.app.exec())
