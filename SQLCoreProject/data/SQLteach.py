from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtWidgets import QPlainTextEdit
from SQLCoreProject.utils.sql_constants import SQL_KEYWORDS, SQL_FUNCTIONS
import re

_global_table_patterns = []
_global_column_patterns = []

def set_global_patterns(tables, columns):
    global _global_table_patterns, _global_column_patterns
    _global_table_patterns = tables or []
    _global_column_patterns = columns or []

class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keyword_fmt = QTextCharFormat()
        self.keyword_fmt.setForeground(QColor("#2979FF"))
        self.keyword_fmt.setFontWeight(QFont.Bold)

        self.func_fmt = QTextCharFormat()
        self.func_fmt.setForeground(QColor("#bd41d2"))
        self.func_fmt.setFontWeight(QFont.Bold)

        self.str_fmt = QTextCharFormat()
        self.str_fmt.setForeground(QColor("#FF5252"))

        self.num_fmt = QTextCharFormat()
        self.num_fmt.setForeground(QColor("#FF9100"))

        self.comment_fmt = QTextCharFormat()
        self.comment_fmt.setForeground(QColor("#90A4AE"))
        self.comment_fmt.setFontItalic(True)

        self.table_fmt = QTextCharFormat()
        self.table_fmt.setForeground(QColor("#43A047"))

        self.column_fmt = QTextCharFormat()
        self.column_fmt.setForeground(QColor("#FFD600"))

    def highlightBlock(self, text):
        # 1. 문자열 먼저 칠한다.
        string_matches = []
        string_pattern = re.compile(r"'[^']*'|\"[^\"]*\"")
        for match in string_pattern.finditer(text):
            start, end = match.span()
            self.setFormat(start, end - start, self.str_fmt)
            string_matches.append((start, end))
        
        def is_in_string(pos):
            for s, e in string_matches:
                if s <= pos < e:
                    return True
            return False

        # 별칭.컬럼명 패턴을 먼저 처리
        alias_col_pattern = re.compile(r"(\b\w+\b)\.(\b\w+\b)")
        for match in alias_col_pattern.finditer(text):
            alias, col = match.groups()
            alias_start, alias_end = match.span(1)
            col_start, col_end = match.span(2)
            # 문자열 내부는 무시
            if any(is_in_string(pos) for pos in range(alias_start, alias_end)):
                continue
            if any(is_in_string(pos) for pos in range(col_start, col_end)):
                continue
            # 별칭이 테이블/CTE/alias 목록에 있으면 테이블 색상
            if alias in _global_table_patterns:
                self.setFormat(alias_start, alias_end - alias_start, self.table_fmt)
            # 컬럼명이 컬럼 패턴에 있으면 컬럼 색상
            if col in _global_column_patterns:
                self.setFormat(col_start, col_end - col_start, self.column_fmt)

        patterns = [
            (re.compile(r"\b(" + "|".join(SQL_KEYWORDS) + r")\b", re.IGNORECASE), self.keyword_fmt),
            (re.compile(r"\b(" + "|".join(SQL_FUNCTIONS) + r")\b", re.IGNORECASE), self.func_fmt),
            (re.compile(r"\b\d+(\.\d+)?\b"), self.num_fmt),
            (re.compile(r"--[^\n]*"), self.comment_fmt)
        ]
        if _global_table_patterns:
            patterns.append((re.compile(r"\b(" + "|".join(_global_table_patterns) + r")\b", re.IGNORECASE), self.table_fmt))
        if _global_column_patterns:
            patterns.append((re.compile(r"\b(" + "|".join(_global_column_patterns) + r")\b", re.IGNORECASE), self.column_fmt))

        for pattern, fmt in patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                # 문자열 내부는 무시
                if any(is_in_string(pos) for pos in range(start, end)):
                    continue
                self.setFormat(start, end - start, fmt)

def capitalize_sql_keywords(text):
    for word in SQL_KEYWORDS + SQL_FUNCTIONS:
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        text = pattern.sub(word.upper(), text)
    return text

class AutoCapitalizingTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self.auto_capitalize_keywords)

    def auto_capitalize_keywords(self):
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()
        new_text = capitalize_sql_keywords(text)
        if new_text != text:
            self.blockSignals(True)
            self.setPlainText(new_text)
            cursor.setPosition(pos)
            self.setTextCursor(cursor)
            self.blockSignals(False)
