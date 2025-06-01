from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox, QTabBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import os
import pandas as pd
from language.lang import lang

class SQLMultiResult(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)
        self.tabBarDoubleClicked.connect(self.rename_tab)
        self.result_tables = []
        self._set_custom_close_icon()
        self.setDocumentMode(False)  # 닫기 버튼이 탭 안에 보이도록 (SQLTabSheet와 동일)
        self.tabBar().setElideMode(Qt.ElideRight)
        self.setUsesScrollButtons(True)
        # 스타일시트 제거

    def _set_custom_close_icon(self):
        # 왼쪽 X 아이콘 완전히 제거 (기본 닫기 버튼만 사용)
        pass

    def add_result(self, df: pd.DataFrame, title=None):
        table = QTableWidget()
        self._populate_table(table, df)
        index = self.addTab(table, title or self._default_tab_name())
        self.setCurrentIndex(index)
        self.result_tables.insert(index, table)
        table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        # 탭 추가 시에도 아이콘 적용
        self._set_custom_close_icon()

    def _populate_table(self, table: QTableWidget, df: pd.DataFrame):
        if df.empty:
            table.setRowCount(0)
            table.setColumnCount(0)
            return
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())
        table.setRowCount(len(df))

        for i, row in df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                table.setItem(i, j, item)

    def get_current_dataframe(self):
        index = self.currentIndex()
        if 0 <= index < len(self.result_tables):
            table = self.result_tables[index]
            return self._extract_table_data(table)
        return pd.DataFrame()

    def _extract_table_data(self, table: QTableWidget):
        rows = table.rowCount()
        cols = table.columnCount()
        data = []
        headers = [table.horizontalHeaderItem(i).text() for i in range(cols)]
        for i in range(rows):
            row_data = []
            for j in range(cols):
                item = table.item(i, j)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return pd.DataFrame(data, columns=headers)

    def remove_current_tab(self):
        if self.count() <= 1:
            QMessageBox.warning(self, lang.MSG_CANNOT_DELETE, lang.MSG_MUST_HAVE_ONE_RESULT_TAB)
            return
        index = self.currentIndex()
        self.removeTab(index)

    def removeTab(self, index):
        if 0 <= index < len(self.result_tables):
            self.result_tables.pop(index)
        super().removeTab(index)

    def rename_tab(self, index):
        if index < 0 or index >= self.count():
            return
        current_title = self.tabText(index)
        new_title, ok = QInputDialog.getText(self, lang.MSG_RENAME_TAB_TITLE, lang.MSG_RENAME_TAB_LABEL, text=current_title)
        if ok and new_title.strip():
            self.setTabText(index, new_title.strip())

    def _default_tab_name(self):
        base = "Result"
        used = set()
        for i in range(self.count()):
            title = self.tabText(i)
            if title.startswith(base):
                try:
                    num = int(title.split(base)[1])
                    used.add(num)
                except:
                    pass
        for i in range(1, 1000):
            if i not in used:
                return f"{base} {i}"
        return f"{base}{self.count()+1}"
