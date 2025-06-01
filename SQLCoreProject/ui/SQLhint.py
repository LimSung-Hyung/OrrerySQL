from PySide6.QtCore import Qt, QPoint, QTimer, QEvent, QObject
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QTextEdit, QApplication
from PySide6.QtGui import QTextCursor, QKeyEvent
from SQLCoreProject.utils.sql_constants import SQL_KEYWORDS, SQL_FUNCTIONS
from SQLCoreProject.data.SQLpatterns import sql_patterns

class SQLAutoCompleter(QObject):  # ⬅ 반드시 QObject 상속
    def __init__(self, text_edit):
        super().__init__()  # ⬅ 부모 생성자 호출도 꼭 필요
        self.text_edit = text_edit
        self.words = set(SQL_KEYWORDS + SQL_FUNCTIONS)

        self.popup = QListWidget()
        self.popup.setWindowFlags(Qt.ToolTip)
        self.popup.setFocusPolicy(Qt.NoFocus)
        self.popup.setMouseTracking(True)
        self.popup.setSelectionMode(QListWidget.SingleSelection)
        self.popup.itemClicked.connect(self.complete_text)

        self.popup.installEventFilter(self)
        self.text_edit.installEventFilter(self)

    def complete_text(self, item: QListWidgetItem):
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        cursor.insertText(item.text())
        self.text_edit.setTextCursor(cursor)
        self.popup.hide()

    def handle_post_keypress(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.popup.hide()
            return

        elif event.key() in (Qt.Key_Up, Qt.Key_Down):
            if self.popup.isVisible():
                self.navigate_popup(event.key())
            return

        elif event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
            if self.popup.isVisible() and self.popup.count() > 0:
                if not self.popup.currentItem():
                    self.popup.setCurrentRow(0)
                self.complete_text(self.popup.currentItem())
            return

        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        prefix = cursor.selectedText()
        if event.text().isprintable():
            prefix += event.text()

        if not prefix.strip():
            self.popup.hide()
            return

        matches = [w for w in self.words if w.lower().startswith(prefix.lower()) and w.lower() != prefix.lower()]
        self.show_popup(matches)

    def update_keywords(self, table_names=None, column_names=None):
        sql_patterns.set_patterns(table_names, column_names)
        self.words = set(SQL_KEYWORDS + SQL_FUNCTIONS)
        if table_names:
            self.words.update(table_names)
        if column_names:
            self.words.update(column_names)

    def navigate_popup(self, key):
        direction = -1 if key == Qt.Key_Up else 1
        new_row = self.popup.currentRow() + direction
        new_row = max(0, min(self.popup.count() - 1, new_row))
        self.popup.setCurrentRow(new_row)

    def show_popup(self, matches):
        if matches:
            self.popup.clear()
            for match in sorted(matches):
                self.popup.addItem(match)

            cursor_rect = self.text_edit.cursorRect()
            popup_pos = self.text_edit.mapToGlobal(cursor_rect.bottomLeft())
            self.popup.setCurrentRow(0)
            self.popup.move(popup_pos)
            self.popup.resize(240, self.popup.sizeHintForRow(0) * min(6, len(matches)))
            self.popup.show()
        else:
            self.popup.hide()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            self.popup.hide()

        elif event.type() == QEvent.MouseButtonPress:
            if self.popup.isVisible() and not self.popup.geometry().contains(event.globalPos()):
                self.popup.hide()

        return False


class CustomTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.completer = SQLAutoCompleter(self)
        self._close_popup_on_arrow = False

    def keyPressEvent(self, event):
        if self.completer.popup.isVisible() and event.key() in {
            Qt.Key_Up, Qt.Key_Down, Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab, Qt.Key_Escape
        }:
            self.completer.handle_post_keypress(event)
            return

        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            if self.completer.popup.isVisible():
                self.completer.popup.hide()
            self._close_popup_on_arrow = True
        else:
            self._close_popup_on_arrow = False

        super().keyPressEvent(event)

        if not self._close_popup_on_arrow:
            QTimer.singleShot(0, lambda: self.completer.handle_post_keypress(event))