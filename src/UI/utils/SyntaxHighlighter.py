from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont
from PySide6.QtCore import Qt
import re


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._format = QTextCharFormat()
        self._format.setForeground(Qt.yellow)
        self._format.setFontWeight(QFont.Bold)

        self._text_mapping = ''

    def set_text(self, text):
        self._text_mapping = text

    def highlightBlock(self, text_block):
        if self._text_mapping == '':
            return

        for match in re.finditer(self._text_mapping, text_block):
            start, end = match.span()
            self.setFormat(start, end - start, self._format)
