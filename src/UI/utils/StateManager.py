from utils import Singleton
from transitions import Machine


# pip install transitions
class StateManager(metaclass=Singleton):
    # To be added: Reports, Report_View, Report_Delete
    states = ['Home', 'Recognition', 'Recognition_Start', 'Recognition_Pause', 'Recognition_Stop', 'Reports', 'Exit']

    def __init__(self, main_window):
        self._main_window = main_window

        self._state_machine = Machine(model=self, states=StateManager.states, initial='Home')

        self._state_machine.add_transition(trigger='button_recognition_clicked', source='Home', dest='Recognition')
        self._state_machine.add_transition(trigger='button_recognition_clicked', source='Reports', dest='Recognition')

        self._state_machine.add_transition(trigger='button_exit_clicked', source='Home', dest='Exit')
        self._state_machine.add_transition(trigger='button_exit_clicked', source='Recognition', dest='Exit')
        self._state_machine.add_transition(trigger='button_exit_clicked', source='Reports', dest='Exit')

        self._state_machine.add_transition(trigger='button_home_clicked', source='Recognition', dest='Home')
        self._state_machine.add_transition(trigger='button_home_clicked', source='Reports', dest='Home')

        self._state_machine.add_transition(trigger='button_start_recognition_clicked', source='Recognition', dest='Recognition_Start', before='start_recognition')

        self._state_machine.add_transition(trigger='button_pause_recognition_clicked', source='Recognition_Start', dest='Recognition_Pause', before='pause_recognition')
        self._state_machine.add_transition(trigger='button_stop_recognition_clicked', source='Recognition_Start', dest='Recognition_Stop', before='stop_recognition')

        self._state_machine.add_transition(trigger='button_start_recognition_clicked', source='Recognition_Pause', dest='Recognition_Start', before='start_recognition')
        self._state_machine.add_transition(trigger='button_stop_recognition_clicked', source='Recognition_Pause', dest='Recognition_Stop', before='stop_recognition')

        # after report has been generated, trigger report_generated to move to Recognition state
        self._state_machine.add_transition(trigger='report_generated', source='Recognition_Stop', dest='Recognition', after='after_report_generated')

        # TO DO: add transition from/to Reports(done), Reports_View(When you click a report,
        # it will open/switched to a frame with infos about that report)
        self._state_machine.add_transition(trigger='button_reports_clicked', source='Home', dest='Reports')
        self._state_machine.add_transition(trigger='button_reports_clicked', source='Recognition', dest='Reports')

    def start_recognition(self):
        if self.state == 'Recognition':
            print("Starting recognition")

        if self.state == 'Recognition_Pause':
            print("Starting recognition after pause")

    def pause_recognition(self):
        print("Pausing recognition")

    def stop_recognition(self):
        print("Stoping recognition")

    def after_report_generated(self):
        print("Report generated ! going back to initial Recognition state")