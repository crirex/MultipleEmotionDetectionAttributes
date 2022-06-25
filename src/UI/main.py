import os
import sys
import argparse

import cv2
import numpy as np
from PySide6.QtCore import QThread

from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import QMainWindow, QHeaderView, QApplication, QMessageBox

from PIL import Image, ImageQt
from transitions import MachineError

from emotion_recognition import FaceDetectionThread
from modules import *
from reports import DataStoreManager
from speech_to_text import GoogleSpeechToText, TextEmotionDetection
from utils import Manager, Settings
from utils.Logger import Logger
from utils.StateManager import StateManager

os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%

widgets = None


def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug
no_name = "No Name"


class MainWindow(QMainWindow):
    logger = Logger()

    def __init__(self, theme_name):
        QMainWindow.__init__(self)
        self.__threads = []
        self.face_detection_thread = FaceDetectionThread(self)
        self.speech_to_text_thread = GoogleSpeechToText(self)
        self._data_store_manager = DataStoreManager()
        self.ui = Ui_MainWindow()

        self._video_timer = QTimer()
        self._text_timer = QTimer()

        self.ui.setupUi(self)

        self._state_manager = StateManager()
        self._state_manager.set_main_window(self)
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

        def saveHomeSettings():
            Settings.VIDEO_PREDICTION = widgets.video_prediction_checkbox.isChecked()
            widgets.labelVideo.setVisible(Settings.VIDEO_PREDICTION)

            Settings.AUDIO_PREDICTION = widgets.audio_prediction_checkbox.isChecked()
            widgets.audioPlotterWidget.setVisible(Settings.AUDIO_PREDICTION)

            Settings.TEXT_PREDICTION = widgets.speech_prediction_checkbox.isChecked()
            widgets.emotioTextEdit.setDisabled(not Settings.TEXT_PREDICTION)

            # Default Microphone added manually so all actual microphones are pushed 1 index further
            Settings.MICROPHONE_INDEX_AND_NAME = (widgets.microphone_combobox.currentIndex() - 1,
                                                  widgets.microphone_combobox.currentText())

            self._data_store_manager.set_interviewee_name(widgets.interviewee_name_plaintext.toPlainText() or no_name)
            self._data_store_manager.set_interviewer_name(widgets.interviewer_name_plaintext.toPlainText() or no_name)

            QMessageBox.information(self, "Settings", "Settings saved successfully.")

        def initializeHomeSettingsPage():
            widgets.home_save_button.clicked.connect(saveHomeSettings)

            widgets.microphone_combobox.addItem("Default Microphone")

            for microphone in QMediaDevices.audioInputs():
                widgets.microphone_combobox.addItem(microphone.description())

            icon = QPixmap("./images/images/logo.png")
            widgets.home_icon_label.setPixmap(icon)
            widgets.home_description_label.setText(Settings.DESCRIPTION)

        settingsButttonEnabled = True
        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)
        widgets.settingsTopBtn.setEnabled(settingsButttonEnabled)
        widgets.settingsTopBtn.setVisible(settingsButttonEnabled)

        initializeHomeSettingsPage()

        self.show()

        useLightTheme = True if len(theme_name) > 0 and theme_name.lower()[0] == 'l' else False
        themeFile = "themes\py_dracula_light.qss"

        if useLightTheme:
            UIFunctions.theme(self, themeFile, True)
            AppFunctions.setThemeHack(self)

        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    def button_home_click(self, button, button_name):
        self._state_manager.button_home_clicked(button, button_name, widgets.home)

    def button_reports_click(self, button, button_name):
        # to be changed with the username
        self.ui.tableWidget.load_reports(self._data_store_manager.interviewee_name)
        self._state_manager.button_reports_clicked(button, button_name, widgets.widgets)

    def button_recognition_click(self, button, button_name):
        self._state_manager.button_recognition_clicked(button, button_name, widgets.new_page)

    def button_exit_click(self, button, button_name):
        self._state_manager.button_exit_clicked(button, button_name)
        self.abort_workers()

    def button_start_recognition_click(self, button, button_name):
        self._state_manager.button_start_recognition_clicked(button, button_name)
        self.ui.event_label.setText("Running")

    def start_recognition(self):
        # Video
        self._video_timer.timeout.connect(self.display_video_stream)
        self._video_timer.start(30)

        # Text
        self._text_timer.timeout.connect(self.display_new_text)
        self._text_timer.start(500)

        # Audio
        self.ui.audioPlotterWidget.start_plotting()

        self.start_thread(self.face_detection_thread, "face_detection_thread")
        self.start_thread(self.face_detection_thread.video_prediction, "face_emotion_detection_thread")

        self.start_thread(self.speech_to_text_thread, "speech_to_text_thread")

        self.start_thread(self.ui.audioPlotterWidget.audio_recording_thread, "audio_detection_thread")
        self.start_thread(self.ui.audioPlotterWidget.audio_recording_thread.voice_prediction, "audio_prediction_thread")

    def resume_recognition(self):
        self.face_detection_thread.resume_running()
        self.ui.audioPlotterWidget.resume_prediction()
        self.speech_to_text_thread.resume()

    def button_stop_recognition_click(self, button, button_name):
        self.ui.event_label.setText("Stopping")
        self._state_manager.button_stop_recognition_clicked(button, button_name)

    def stop_recognition(self):
        self._video_timer.stop()
        self._text_timer.stop()

        # Video
        self.face_detection_thread.stop_running()
        self.ui.labelVideo.clear()

        # Speech to text
        self.speech_to_text_thread.stop()
        self.ui.emotioTextEdit.clear()

        # Audio
        self.ui.audioPlotterWidget.stop_prediction()
        # self.ui.audioPlotterWidget

        if Settings.TEXT_PREDICTION:
            print(self.ui.emotioTextEdit.toPlainText())
            print(TextEmotionDetection().run(self.ui.emotioTextEdit.toPlainText(), model_name="Personality_traits_NN"))

        self.ui.event_label.setText("Stopped")

    def button_pause_recognition_click(self, button, button_name):
        self._state_manager.button_pause_recognition_clicked(button, button_name)
        self.ui.event_label.setText("Paused")

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

    def display_video_stream(self):
        frame = self.face_detection_thread.get_frame()
        if frame is None:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame.astype(np.uint8))
        qim = ImageQt.ImageQt(img)
        pm = QPixmap.fromImage(qim)
        self.ui.labelVideo.setPixmap(pm)

    def display_new_text(self):
        text = self.speech_to_text_thread.get_new_text()
        if text is not None:
            self._manager.window.ui.emotioTextEdit.insertPlainText(text + ". ")

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
        self.abort_workers()

    def reset_style(self, button_name):
        UIFunctions.resetStyle(self, button_name)

    def select_menu_style(self, button):
        return UIFunctions.selectMenu(button.styleSheet())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multimodal Emotion Detection")
    parser.add_argument('--theme', type=str)
    args = parser.parse_args()
    theme_name_arg = ''
    if args.__contains__("theme") and args.theme is not None:
        theme_name_arg = args.theme

    import nltk

    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
    nltk.download('omw-1.4')

    MainWindow.logger.log_info("Application starts")
    manager = Manager()
    manager.app = QApplication(sys.argv)
    manager.app.setWindowIcon(QIcon("icon.ico"))
    manager.window = MainWindow(theme_name_arg)
    sys.exit(manager.app.exec())
