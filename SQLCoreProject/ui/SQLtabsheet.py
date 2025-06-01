from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QToolButton, QHBoxLayout, QMessageBox, QInputDialog
from PySide6.QtCore import Qt
from SQLCoreProject.data.SQLteach import SQLHighlighter
from language.lang import lang


class SQLTabSheet(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)
        self.tabBarDoubleClicked.connect(self.rename_tab)
        self.query_inputs = []
        self.query_input_factory = None
        self.console_count = 1

        self._create_button_bar()

    def _create_button_bar(self):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.btn_add = QToolButton()
        self.btn_add.setText(lang.BTN_ADD_SHEET)
        self.btn_add.setToolTip(lang.TOOLTIP_ADD_SHEET)
        self.btn_add.clicked.connect(self.create_new_console)

        self.btn_del = QToolButton()
        self.btn_del.setText(lang.BTN_CLOSE_SHEET)
        self.btn_del.setToolTip(lang.TOOLTIP_CLOSE_SHEET)
        self.btn_del.clicked.connect(self.remove_current_tab)

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_del)
        self.setCornerWidget(bar, Qt.TopRightCorner)

    def set_query_input_factory(self, factory_func):
        self.query_input_factory = factory_func

    def create_new_console(self):
        if not self.query_input_factory:
            return
        query_input = self.query_input_factory()
        title = f"{lang.LABEL_SHEET} {self.get_next_console_number()}"
        widget = self._wrap_input(query_input)
        index = self.addTab(widget, title)
        self.query_inputs.insert(index, query_input)
        self.setCurrentIndex(index)
        query_input.setFocus()

    def remove_current_tab(self):
        if self.count() <= 1:
            QMessageBox.warning(self, lang.MSG_CANNOT_DELETE, lang.MSG_MUST_HAVE_ONE_CONSOLE_TAB)
            return
        index = self.currentIndex()
        if 0 <= index < len(self.query_inputs):
            self.removeTab(index)

    def removeTab(self, index):
        if self.count() <= 1:
            return  # 방어 코드 (직접 removeTab 호출하는 경우 대비)
        if 0 <= index < len(self.query_inputs):
            self.query_inputs.pop(index)
        super().removeTab(index)

    def get_current_query_input(self):
        index = self.currentIndex()
        if 0 <= index < len(self.query_inputs):
            return self.query_inputs[index]
        return None

    def _wrap_input(self, query_input):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # 하이라이터는 query_input 생성 시 이미 연결됨
        layout.addWidget(query_input)
        widget.setLayout(layout)
        return widget

    def rename_tab(self, index):
        if index < 0 or index >= self.count():
            return
        current_title = self.tabText(index)
        new_title, ok = QInputDialog.getText(self, lang.MSG_RENAME_TAB_TITLE, lang.MSG_RENAME_TAB_LABEL, text=current_title)
        if ok and new_title.strip():
            self.setTabText(index, new_title.strip())

    def get_next_console_number(self):
        used_numbers = set()
        for i in range(self.count()):
            title = self.tabText(i)
            if title.startswith(f"{lang.LABEL_SHEET} "):
                try:
                    number = int(title.split(f"{lang.LABEL_SHEET} ")[1])
                    used_numbers.add(number)
                except:
                    pass
        for i in range(1, 1000):
            if i not in used_numbers:
                return i
        return self.count() + 1  # fallback

