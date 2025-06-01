from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QLineEdit, QPushButton, QCheckBox
)
try:
    from PySide6.QtGui import QKeySequence, QShortcut
    QKEYSEQUENCE_FROM = 'QtGui'
except ImportError:
    from PySide6.QtWidgets import QKeySequence, QShortcut
    QKEYSEQUENCE_FROM = 'QtWidgets'

from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt
import pandas as pd

class SQLWideResultDialog(QDialog):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.df = df
        self.setWindowTitle("🔍 Expanded Result")
        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout(self)

        # 검색 UI
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter keyword")
        self.search_next_btn = QPushButton("Next")
        self.search_all_checkbox = QCheckBox("Highlight All")

        search_bar.addWidget(self.search_input)
        search_bar.addWidget(self.search_next_btn)
        search_bar.addWidget(self.search_all_checkbox)
        layout.addLayout(search_bar)

        self.search_next_btn.clicked.connect(self.search_next)
        self.search_input.returnPressed.connect(self.search_next)
        self.search_input.textChanged.connect(self.reset_search_state)

        self.search_matches = []
        self.search_index = -1

        # 테이블
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.populate_table()

        # 단축키: Ctrl + Shift + E → 엑셀로 저장
        QShortcut(QKeySequence("Ctrl+Shift+E"), self, self.export_to_excel)

        # 단축키: Ctrl + F → 검색창 포커스
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.search_input.setFocus())

    def populate_table(self):
        if self.df.empty:
            return
        self.table.setColumnCount(len(self.df.columns))
        self.table.setHorizontalHeaderLabels(self.df.columns.tolist())
        self.table.setRowCount(len(self.df))

        for i, row in self.df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(i, j, item)

        # 열 전체 너비 합산
        total_width = sum([self.table.columnWidth(i) for i in range(self.table.columnCount())])
        total_height = self.table.rowHeight(0) * min(self.table.rowCount(), 30) + 70
        margin = 70
        self.resize(total_width + margin, total_height)

    def export_to_excel(self):
        if self.df.empty:
            QMessageBox.warning(self, "Save Failed", "No result to save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save as Excel", "query_result.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                self.df.to_excel(path, index=False)
                QMessageBox.information(self, "Saved", f"Saved to Excel:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Failed", f"Failed to save to Excel: {e}")

    def reset_search_state(self):
        self.search_matches.clear()
        self.search_index = -1

        default_bg = self.palette().base()
        default_fg = self.palette().text()

        for i in range(self.table.rowCount()):
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item:
                    item.setBackground(QBrush(default_bg))
                    item.setForeground(QBrush(default_fg))

    def search_next(self):
        text = self.search_input.text().strip()
        if not text:
            return

        if not self.search_matches:
            for i in range(self.table.rowCount()):
                for j in range(self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item and text in item.text():
                        self.search_matches.append((i, j))

        if not self.search_matches:
            QMessageBox.information(self, "No Results", f"'{text}' not found.")
            return

        if self.search_all_checkbox.isChecked():
            for i, j in self.search_matches:
                item = self.table.item(i, j)
                item.setBackground(QBrush(QColor("#ffcc00")))
                item.setForeground(QBrush(QColor("#000000")))

        self.search_index = (self.search_index + 1) % len(self.search_matches)
        i, j = self.search_matches[self.search_index]
        self.table.setCurrentCell(i, j)
        item = self.table.item(i, j)
        item.setBackground(QBrush(QColor("#ffcc00")))  # 현재 강조
        item.setForeground(QBrush(QColor("#000000")))
