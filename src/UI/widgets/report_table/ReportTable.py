from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMenu

import time
import datetime

from persistance import MongoDb

time_format = "%Y-%m-%d %H:%M:%S"


class ReportTable(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self._mongo_db = MongoDb()
        self._reports = []
        self.table_row = 0

        self.menu = QMenu(self)
        self.delete_action = self.menu.addAction("Delete Report")
        self.export_action = self.menu.addAction("Export Report")

        self.action_to_func = {
            self.delete_action: self.delete_report,
            self.export_action: self.export_report
        }

    def _reset(self):
        self._reports = []
        self.table_row = 0
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
        self.setItem(self.table_row, 0,
                     QTableWidgetItem(report["interviewee_name"]))
        self.setItem(self.table_row, 1,
                     QTableWidgetItem(report["interviewer_name"]))
        self.setItem(self.table_row, 2,
                     QTableWidgetItem(time.strftime(time_format, time.localtime(report["interview_start_date"]))))
        self.setItem(self.table_row, 3,
                     QTableWidgetItem(time.strftime(time_format, time.localtime(report["interview_end_date"]))))
        self.setItem(self.table_row, 4,
                     QTableWidgetItem(str(datetime.timedelta(seconds=report["interview_length"]))))
        self.table_row += 1

    def delete_report(self, report_index):
        if report_index >= 0 and len(self._reports) > 0:
            report_to_remove = self._reports[report_index]
            self._reports.remove(report_to_remove)
            self.removeRow(report_index)
            self._mongo_db.remove_report(report_to_remove)

    def export_report(self, report_index):
        print("Export " + str(report_index))

    def mouseDoubleClickEvent(self, event) -> None:
        super().mouseDoubleClickEvent(event)
        index = self.indexAt(event.pos())
        if len(self._reports) > 0 and index.row() >= 0:
            print(str(index.row()) + " " + str(self._reports[index.row()]))
            # print(index.model())

    def contextMenuEvent(self, event) -> None:
        action = self.menu.exec_(self.mapToGlobal(event.pos()))
        index = self.indexAt(event.pos()).row()
        self.action_to_func[action](index)
