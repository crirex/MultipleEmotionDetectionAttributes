from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont
from PySide6.QtCore import Qt
import re


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.format = QTextCharFormat()
        self.format.setForeground(Qt.yellow)
        self.format.setFontWeight(QFont.Bold)

        self.text_mapping = ''

    def set_text(self, text):
        self.text_mapping = text

    def highlightBlock(self, text_block):
        if self.text_mapping == '':
            return

        for match in re.finditer(self.text_mapping, text_block):
            start, end = match.span()
            self.setFormat(start, end - start, self.format)

    def clear_highlight(self):
        self.text_mapping = ''
        self.rehighlight()
