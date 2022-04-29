import time

from reports import DataStoreManager
from reports.report_utils import generate_report
from utils import Singleton, Logger, Manager
from transitions import Machine

widgets = None


def log_button_click(button, button_name):
    StateManager.logger.log_info(f"{button} - {button_name} panel clicked")


class StateManager(metaclass=Singleton):
    # To be added: Reports, Report_View, Report_Delete
    states = ['Home', 'Recognition', 'Recognition_Start', 'Recognition_Pause', 'Recognition_Stop', 'Reports', 'Exit']
    logger = Logger()

    def __init__(self, main_window):
        self._main_window = main_window
        global widgets
        widgets = self._main_window.ui

        self._manager = Manager()
        self._data_store_manager = DataStoreManager()

        self._state_machine = Machine(model=self, states=StateManager.states, initial='Home')

        self._state_machine.add_transition(trigger='button_recognition_clicked', source='Home', dest='Recognition',
                                           before="change_frame")
        self._state_machine.add_transition(trigger='button_recognition_clicked', source='Reports', dest='Recognition',
                                           before="change_frame")

        self._state_machine.add_transition(trigger='button_exit_clicked', source='Home', dest='Exit', after="exit_app")
        self._state_machine.add_transition(trigger='button_exit_clicked', source='Recognition', dest='Exit',
                                           after="exit_app")
        self._state_machine.add_transition(trigger='button_exit_clicked', source='Reports', dest='Exit',
                                           after="exit_app")

        self._state_machine.add_transition(trigger='button_home_clicked', source='Recognition', dest='Home',
                                           before="change_frame")
        self._state_machine.add_transition(trigger='button_home_clicked', source='Reports', dest='Home',
                                           before="change_frame")

        self._state_machine.add_transition(trigger='button_start_recognition_clicked', source='Recognition',
                                           dest='Recognition_Start', before='start_recognition')

        self._state_machine.add_transition(trigger='button_pause_recognition_clicked', source='Recognition_Start',
                                           dest='Recognition_Pause', before='pause_recognition')
        self._state_machine.add_transition(trigger='button_stop_recognition_clicked', source='Recognition_Start',
                                           dest='Recognition_Stop', after='stop_recognition')

        self._state_machine.add_transition(trigger='button_start_recognition_clicked', source='Recognition_Pause',
                                           dest='Recognition_Start', before='start_recognition')
        self._state_machine.add_transition(trigger='button_stop_recognition_clicked', source='Recognition_Pause',
                                           dest='Recognition_Stop', after='stop_recognition')

        # after report has been generated, trigger report_generated to move to Recognition state
        self._state_machine.add_transition(trigger='report_generated', source='Recognition_Stop', dest='Recognition',
                                           after='after_report_generated')

        # TO DO: add transition from/to Reports(done), Reports_View(When you click a report,
        # it will open/switched to a frame with infos about that report)
        self._state_machine.add_transition(trigger='button_reports_clicked', source='Home', dest='Reports',
                                           before="change_frame")
        self._state_machine.add_transition(trigger='button_reports_clicked', source='Recognition', dest='Reports',
                                           before="change_frame")

    def change_frame(self, button, button_name, widget):
        log_button_click(button, button_name)
        widgets.stackedWidget.setCurrentWidget(widget)
        self._main_window.reset_style(button_name)
        button.setStyleSheet(self._main_window.select_menu_style(button))

    def exit_app(self, button, button_name):
        log_button_click(button, button_name)
        self._manager.release_resources()
        self._manager.quit_app()
        self._main_window.close()

    def start_recognition(self, button, button_name):
        log_button_click(button, button_name)
        StateManager.logger.log_info("Starting emotion recognition")

        if self.state == 'Recognition':
            self._data_store_manager.start_date = time.time()
            self._main_window.start_recognition()
            return

        if self.state == 'Recognition_Pause':
            self._main_window.resume_recognition()
            return

    def pause_recognition(self, button, button_name):
        log_button_click(button, button_name)
        StateManager.logger.log_info("Pause emotion recognition")
        self._main_window.pause_recognition()

    def stop_recognition(self, button, button_name):
        log_button_click(button, button_name)
        StateManager.logger.log_info("Stop emotion recognition")
        self._data_store_manager.end_date = time.time()
        self._main_window.stop_recognition()

        print("Video: " + str(self._data_store_manager.video_predictions.keys()))
        print(len(self._data_store_manager.video_predictions))
        print("Audio: " + str(self._data_store_manager.audio_predictions.keys()))
        print(len(self._data_store_manager.audio_predictions))

        # here we should wait for some stuff
        generate_report()
        # after the report is generated
        self.report_generated()  # emit that the report has been generated

    def after_report_generated(self):
        print("Report generated ! going back to initial Recognition state")
        self._data_store_manager.clear()
