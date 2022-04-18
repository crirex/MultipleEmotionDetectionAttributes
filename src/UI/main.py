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


def log_button_click(button, button_name):
    MainWindow.logger.log_info(f"{button} - {button_name} panel clicked")


class MainWindow(QMainWindow):
    logger = Logger()

    def __init__(self):
        QMainWindow.__init__(self)
        self.__threads = []
        self.face_detection_thread = FaceDetectionThread()
        self.text_to_speech_thread = GoogleSpeechToText(self)
        self.ui = Ui_MainWindow()
        self.timer = QTimer()
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

    def change_frame(self, widget, button, button_name):
        log_button_click(button, button_name)
        widgets.stackedWidget.setCurrentWidget(widget)
        UIFunctions.resetStyle(self, button_name)
        button.setStyleSheet(UIFunctions.selectMenu(button.styleSheet()))

    def button_home_click(self, button, button_name):
        self._state_manager.button_home_clicked()
        self.change_frame(widgets.home, button, button_name)

    def button_reports_click(self, button, button_name):
        self._state_manager.button_reports_clicked()
        self.change_frame(widgets.widgets, button, button_name)

    def button_recognition_click(self, button, button_name):
        self._state_manager.button_recognition_clicked()
        self.change_frame(widgets.new_page, button, button_name)

    def button_exit_click(self, button, button_name):
        self._state_manager.button_exit_clicked()
        log_button_click(button, button_name)
        self._manager.release_resources()
        self._manager.quit_app()
        self.close()

    def button_start_recognition_click(self, button, button_name):
        self._state_manager.button_start_recognition_clicked()
        log_button_click(button, button_name)
        MainWindow.logger.log_info("Starting emotion recognition")

        # Video
        self.timer.timeout.connect(self.display_video_stream)
        self.timer.start(30)

        # Audio
        self.ui.audioPlotterWidget.start_recording()

        # SpeechToText
        self.timer.timeout.connect(self.display_text_from_speech)
        self.timer.start(30)

        self.start_thread(self.face_detection_thread, "face_detection_thread")
        self.start_thread(self.text_to_speech_thread, "text_to_speech_thread")

    def button_stop_recognition_click(self, button, button_name):
        self._state_manager.button_stop_recognition_clicked()
        log_button_click(button, button_name)
        MainWindow.logger.log_info("Stop emotion recognition")

        # Video
        self.timer.stop()
        self.face_detection_thread.stop_running()

        # Audio
        self.ui.audioPlotterWidget.stop_recording()

        # After the report has been generated
        self._state_manager.report_generated()

    def button_pause_recognition_click(self, button, button_name):
        self._state_manager.button_pause_recognition_clicked()
        log_button_click(button, button_name)
        MainWindow.logger.log_info("Pause emotion recognition")

        # TO DO: implement a way to hide voice and face prediction
        # ...

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
        new_text = self.text_to_speech_thread.get_new_text()
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
        self.logger.log_debug('All threads exited')


if __name__ == "__main__":
    MainWindow.logger.log_info("Application starts")

    Manager.app = QApplication(sys.argv)
    Manager.app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(Manager.app.exec())
