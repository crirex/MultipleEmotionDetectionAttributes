from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMenu

import time
import datetime

from persistance import MongoDb
from utils.StateManager import StateManager
from utils import Manager

time_format = "%Y-%m-%d %H:%M:%S"


class ReportTable(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self._mongo_db = MongoDb()
        self._reports = []
        self._table_row = 0

        self._menu = QMenu(self)
        self._delete_action = self._menu.addAction("Delete Report")
        self._export_action = self._menu.addAction("Export Report")

        self._action_to_func = {
            self._delete_action: self.delete_report,
            self._export_action: self.export_report
        }

        self._manager = Manager()
        self._state_manager = StateManager()

    def _reset(self):
        self._reports = []
        self._table_row = 0
        # self.clear()
        self.setRowCount(0)

    def load_reports(self, candidate_name):
        self._reset()
        self._reports = self._mongo_db.get_all_reports_of_candidate(candidate_name)
        if self._reports is None or len(self._reports) == 0:
            return

        self.setRowCount(self.rowCount() + len(self._reports))
        for report in self._reports:
            self.insert_report(report)

    def insert_report(self, report):
        self.setItem(self._table_row, 0,
                     QTableWidgetItem(report["interviewee_name"]))
        self.setItem(self._table_row, 1,
                     QTableWidgetItem(report["interviewer_name"]))
        self.setItem(self._table_row, 2,
                     QTableWidgetItem(time.strftime(time_format, time.localtime(report["interview_start_date"]))))
        self.setItem(self._table_row, 3,
                     QTableWidgetItem(time.strftime(time_format, time.localtime(report["interview_end_date"]))))
        self.setItem(self._table_row, 4,
                     QTableWidgetItem(str(datetime.timedelta(seconds=report["interview_length"]))))
        self._table_row += 1

    def delete_report(self, report_index):
        if report_index >= 0 and len(self._reports) > 0:
            report_to_remove = self._reports[report_index]
            self._reports.remove(report_to_remove)
            self.removeRow(report_index)
            self._mongo_db.remove_report(report_to_remove)

    def export_report(self, report_index):
        print("Export " + str(report_index))

    def reset_report_view(self):
        if self._manager.window is None:
            return

        report_view = self._manager.window.ui.report_view
        report_view.reset()

    def mouseDoubleClickEvent(self, event) -> None:
        super().mouseDoubleClickEvent(event)
        index = self.indexAt(event.pos()).row()

        if len(self._reports) > 0 and index >= 0:
            report = self._reports[index]

            predictions = self._mongo_db.get_prediction(report['predictions_id'])

            self.reset_report_view()
            self._manager.window.ui.report_view.initialize(self._manager.window, report, predictions)
            self._state_manager.report_double_clicked(None, f"Line {index} clicked", self._manager.window.ui.report_view, False)

    def contextMenuEvent(self, event) -> None:
        action = self._menu.exec_(self.mapToGlobal(event.pos()))
        index = self.indexAt(event.pos()).row()
        self._action_to_func[action](index)
