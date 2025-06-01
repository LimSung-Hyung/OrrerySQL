from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PySide6.QtGui import QTextFormat, QPainter, QColor, QPalette
from PySide6.QtCore import QSize, QRect, Signal, Qt
from SQLCoreProject.data.SQLteach import SQLHighlighter, capitalize_sql_keywords, AutoCapitalizingTextEdit
from SQLCoreProject.ui.SQLhint import SQLAutoCompleter


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class QueryInputWithLineNumber(AutoCapitalizingTextEdit):
    execute_query_signal = Signal()

    def __init__(self, completer=None, highlight=True):  # ✅ 플래그
        super().__init__()
        print(f"[DEBUG] QueryInputWithLineNumber document id: {id(self.document())}")
        if highlight:
            self.highlighter = SQLHighlighter(self.document())  # ✅ 조건적 적용
            print(f"[DEBUG] Highlighter created: {self.highlighter}, doc id: {id(self.document())}")
        else:
            self.highlighter = None
        if completer is not None:
            self.completer = completer
        else:
            self.completer = SQLAutoCompleter(self)
        self.textChanged.connect(self.auto_capitalize_keywords)
        # document가 바뀔 때마다 하이라이터 재연결
        self.document().documentLayoutChanged.connect(self._ensure_highlighter)

        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.setLineWrapMode(AutoCapitalizingTextEdit.NoWrap)

        # 드래그(선택) 색상 현대적으로 변경
        palette = self.palette()
        palette.setColor(QPalette.Highlight, QColor("#ab9a9a"))
        palette.setColor(QPalette.HighlightedText, QColor("#222222"))  # 선택된 글자색(진한 회색)
        self.setPalette(palette)

    def _ensure_highlighter(self):
        print(f"[DEBUG] _ensure_highlighter: doc id: {id(self.document())}")
        self.highlighter = SQLHighlighter(self.document())
        self.highlighter.rehighlight()

    def keyPressEvent(self, event):
        if self.completer.popup.isVisible():
            if event.key() in {Qt.Key_Up, Qt.Key_Down, Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab, Qt.Key_Escape}:
                self.completer.handle_post_keypress(event)
                return  # 콘솔로 전달 X
            elif event.key() in (Qt.Key_Left, Qt.Key_Right):
                self.completer.popup.hide()
                return

        # 일반 키: 자동완성 먼저 적용, 이후 콘솔 처리
        self.completer.handle_post_keypress(event)
        super().keyPressEvent(event)

    def line_number_area_width(self):
        digits = len(str(self.blockCount()))
        padding = 8  # ← 기본 3 → 8로 여유 확보
        space = padding + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)

        # ✅ 배경색을 본문 배경과 일치시킴
        editor_bg = QColor(30, 30, 30)  # #1e1e1e
        painter.fillRect(event.rect(), editor_bg)

        # ✅ 왼쪽 미묘한 구분선 추가
        border_color = QColor(43, 43, 43)  # #2b2b2b
        painter.setPen(border_color)
        painter.drawLine(
            self.line_number_area.width() - 1,  # 오른쪽 경계
            event.rect().top(),
            self.line_number_area.width() - 1,
            event.rect().bottom()
        )

        # ✅ 폰트 설정
        font = self.font()
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)

        # ✅ 숫자 렌더링
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(QColor(150, 150, 150))  # 라인 넘버 색

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, int(top),
                    self.line_number_area.width() - 4,
                    int(self.fontMetrics().height()),
                    Qt.AlignRight | Qt.AlignVCenter,
                    number
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def highlight_current_line(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(60, 60, 60)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)