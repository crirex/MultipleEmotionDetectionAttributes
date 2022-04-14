import os
import sys

import cv2
import numpy as np
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread

from PySide6.QtGui import QPixmap, QTextCursor
from PySide6.QtWidgets import QMainWindow, QHeaderView, QApplication

from PIL import Image, ImageQt

from emotion_recognition import FaceDetectionThread
from modules import *
from speech_to_text import GoogleSpeechToText
from utils import Manager
from utils.Logger import Logger

os.environ["QT_FONT_DPI"] = "96"  # FIX Problem for High DPI and Scale above 100%

# SET AS GLOBAL WIDGETS
# ///////////////////////////////////////////////////////////////
widgets = None


def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    print(args)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class MainWindow(QMainWindow):
    logger = Logger()
    sig_abort_workers = pyqtSignal()

    def __init__(self):
        QMainWindow.__init__(self)
        self.__threads = []
        self.face_detection_thread = FaceDetectionThread()
        self.text_to_speech_thread = GoogleSpeechToText(self)

        # SET AS GLOBAL WIDGETS
        # ///////////////////////////////////////////////////////////////
        self.ui = Ui_MainWindow()
        self.timer = QTimer()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        # USE CUSTOM TITLE BAR | USE AS "False" FOR MAC OR LINUX
        # ///////////////////////////////////////////////////////////////
        Settings.ENABLE_CUSTOM_TITLE_BAR = False
        Settings.THREAD_REFERENCE = self.face_detection_thread

        # APP NAME
        # ///////////////////////////////////////////////////////////////
        title = "Multimodal emotion detection"
        description = "TO DO"
        # APPLY TEXTS
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        # TOGGLE MENU
        # ///////////////////////////////////////////////////////////////
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        # SET UI DEFINITIONS
        # ///////////////////////////////////////////////////////////////
        UIFunctions.uiDefinitions(self)

        # QTableWidget PARAMETERS
        # ///////////////////////////////////////////////////////////////
        widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # BUTTONS CLICK
        # ///////////////////////////////////////////////////////////////

        # LEFT MENUS
        widgets.btn_home.clicked.connect(self.buttonClick)
        widgets.btn_widgets.clicked.connect(self.buttonClick)
        widgets.btn_new.clicked.connect(self.buttonClick)
        widgets.btn_save.clicked.connect(self.buttonClick)

        widgets.startButton.clicked.connect(self.buttonClick)
        widgets.cancelButton.clicked.connect(self.buttonClick)

        # EXTRA LEFT BOX
        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)

        widgets.toggleLeftBox.clicked.connect(openCloseLeftBox)
        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        # EXTRA RIGHT BOX
        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)

        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)

        # SHOW APP
        # ///////////////////////////////////////////////////////////////
        self.show()

        # SET CUSTOM THEME
        # ///////////////////////////////////////////////////////////////
        useCustomTheme = False
        themeFile = "themes\py_dracula_light.qss"

        # SET THEME AND HACKS
        if useCustomTheme:
            # LOAD AND APPLY STYLE
            UIFunctions.theme(self, themeFile, True)

            # SET HACKS
            AppFunctions.setThemeHack(self)

        # SET HOME PAGE AND SELECT MENU
        # ///////////////////////////////////////////////////////////////
        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    # BUTTONS CLICK
    # Post here your functions for clicked buttons
    # ///////////////////////////////////////////////////////////////
    def buttonClick(self):
        # GET BUTTON CLICKED
        btn = self.sender()
        btnName = btn.objectName()

        # SHOW HOME PAGE
        if btnName == "btn_home":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW WIDGETS PAGE
        if btnName == "btn_widgets":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        # SHOW NEW PAGE
        if btnName == "btn_new":
            MainWindow.logger.log_info("Emotion recognition panel clicked")
            widgets.stackedWidget.setCurrentWidget(widgets.new_page)  # SET PAGE
            UIFunctions.resetStyle(self, btnName)  # RESET ANOTHERS BUTTONS SELECTED
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))  # SELECT MENU

        if btnName == "startButton":
            MainWindow.logger.log_info("Start emotion recognition")

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
            print("after thread")

        if btnName == "cancelButton":
            MainWindow.logger.log_info("Stop emotion recognition")

            # Video
            self.timer.stop()
            self.face_detection_thread.stop_running()

            # Audio
            self.ui.audioPlotterWidget.stop_recording()
        if btnName == "btn_save":
            print("Save BTN clicked!")

        # PRINT BTN NAME
        print(f'Button "{btnName}" pressed!')

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

    # RESIZE EVENTS
    # ///////////////////////////////////////////////////////////////
    def resizeEvent(self, event):
        # Update Size Grips
        UIFunctions.resize_grips(self)

    # MOUSE CLICK EVENTS
    # ///////////////////////////////////////////////////////////////
    def mousePressEvent(self, event):
        # SET DRAG POS WINDOW
        self.dragPos = event.globalPos()

        # PRINT MOUSE EVENTS
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')

    def start_thread(self, worker, name):
        thread = QThread()
        thread.setObjectName('thread_' + name)
        self.__threads.append((thread, worker))  # need to store worker too otherwise will be gc'd
        worker.moveToThread(thread)

        # get progress messages from worker:
        worker.sig_msg.connect(self.logger.log_debug)

        # get read to start worker:
        thread.started.connect(worker.work)
        thread.start()  # this will emit 'started' and start thread's event loop

    @pyqtSlot()
    def abort_workers(self):
        self.logger.log_debug('Asking each worker to abort')
        for thread, worker in self.__threads:  # note nice unpacking by Python, avoids indexing
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
