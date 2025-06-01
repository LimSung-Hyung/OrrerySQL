import sys
import os
import json
import sqlparse

from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTextEdit, QLabel, QMessageBox, QPushButton, QDialog, QSplitter
)
from PySide6.QtCore import Qt
from SQLCoreProject.core.SQLInterpreterCore import SQLQueryInterpreter

from SQLCoreProject.core.SQLFlowVisualizer import SQLFlowVisualizer
from SQLCoreProject.core.ASTtcAnalyzer import SQLTCAnalyzer
from SQLCoreProject.core.ASTKeywordsAnalyzer import extract_clause_description
from SQLCoreProject.core.ASTaggregation import parse_aggregation
from SQLCoreProject.core.ASTselectAnalyzer import extract_select_fields
from SQLCoreProject.core.ASTjoinAnalyzer import extract_join_detail
from SQLCoreProject.core.CTEjoin import _extract_joins
from SQLCoreProject.data.SQLgate import get_logs_dir
from language.lang import lang

BASE_DIR = Path(get_logs_dir())
QUERY_LOG_PATH = BASE_DIR / "query_log.json"

class QueryLogAnalyzer:
    def __init__(self, path=QUERY_LOG_PATH):
        self.path = path
        self.entries = self._load_entries()
        self.enriched_entries = self._enrich_entries_with_structure()

    def _load_entries(self):
        if not self.path.exists():
            # 파일이 없으면 빈 리스트 반환 (에러 발생 X)
            return []
        with open(self.path, encoding='utf-8') as f:
            return json.load(f)

    def _enrich_entries_with_structure(self):
        enriched = []
        for entry in self.entries:
            query = entry.get("query", "")
            interpreter = SQLQueryInterpreter(query)
            ast = interpreter.get_ast()

            # === AST 내 "NOT" 블록 우항 검사 및 경고 삽입 ===
            def ast_has_empty_not(node):
                if not isinstance(node, dict):
                    return False
                if node.get("class", "").upper() == "NOT":
                    right = node.get("args", {}).get("this", {})
                    if isinstance(right, dict) and not right.get("class"):
                        return True
                for v in node.values():
                    if isinstance(v, dict) and ast_has_empty_not(v):
                        return True
                    if isinstance(v, list):
                        for i in v:
                            if ast_has_empty_not(i):
                                return True
                return False

            empty_not_detected = ast_has_empty_not(ast)

            flow = interpreter.get_logical_flow()
            nl = interpreter.get_natural_description()

            # 경고 메시지 삽입
            if empty_not_detected:
                flow = lang.MSG_WARNING + ": AST에 NOT 조건식 우항이 비어있음. 파서 오류 가능성 99%\n" + str(flow)
                nl = lang.MSG_WARNING + ": NOT 조건 해석 불가: AST 파싱 실패(파서/입력/라이브러리 확인 요망)\n" + str(nl)

            enriched.append({
                **entry,
                "query_analysis": {
                    "raw_ast": ast,
                    "flow": flow,
                    "nl": nl,
                }
            })
        return enriched

class ASTDialog(QDialog):
    def __init__(self, ast_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(lang.MSG_AST_READONLY)
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        text_box = QTextEdit()
        text_box.setReadOnly(True)
        text_box.setPlainText(ast_str)
        layout.addWidget(text_box)

class SQLInspectorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQL Inspector")
        self.setMinimumSize(1400, 900)

        self.analyzer = QueryLogAnalyzer()

        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # 쿼리 리스트(왼쪽)
        self.query_list = QListWidget()
        self.query_list.setMaximumWidth(130)
        self.query_list.itemClicked.connect(self.handle_selection)
        top_layout.addWidget(self.query_list)

        # QSplitter: 쿼리/해석/아스키 3분할
        self.splitter = QSplitter(Qt.Horizontal)

        # 1. 쿼리 원본
        self.query_box = QTextEdit()
        self.query_box.setReadOnly(True)
        self.query_box.setFontFamily("Consolas")
        self.query_box.setFontPointSize(9)
        self.query_box.setPlaceholderText(lang.MSG_SQL_QUERY)
        self.splitter.addWidget(self.query_box)

        # 2. 논리 해석 결과(처음엔 숨김)
        self.flow_box = QTextEdit()
        self.flow_box.setReadOnly(True)
        self.flow_box.setFontFamily("Consolas")
        self.flow_box.setFontPointSize(9)
        self.flow_box.setPlaceholderText(lang.MSG_LOGIC_FLOW)
        self.splitter.addWidget(self.flow_box)
        self.flow_box.hide()  # 초기에는 숨김

        # 3. 아스키 시각화
        self.ascii_box = QTextEdit()
        self.ascii_box.setReadOnly(True)
        self.ascii_box.setFontFamily("Consolas")
        self.ascii_box.setFontPointSize(9)
        self.ascii_box.setPlaceholderText(lang.MSG_ASCII_VIEW)
        self.splitter.addWidget(self.ascii_box)

        self.splitter.setSizes([500, 0, 900])  # 해석은 숨겨져 있으니 0

        top_layout.addWidget(self.splitter)

        # ===== 하단 버튼 =====
        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)
        self.toggle_btn = QPushButton(lang.MSG_EXPAND)
        self.toggle_btn.clicked.connect(self.toggle_flow_box)
        bottom_layout.addWidget(self.toggle_btn, alignment=Qt.AlignLeft)

        self.ast_btn = QPushButton(lang.MSG_AST_VIEW)
        self.ast_btn.clicked.connect(self.show_ast)
        bottom_layout.addWidget(self.ast_btn, alignment=Qt.AlignLeft)

        bottom_layout.addStretch(1)

        self._current_ast_str = ""      # AST 캐싱용
        self._current_flow_steps = None # 논리 흐름 시각화용

        self.populate_queries()

    def populate_queries(self):
        self.query_list.clear()
        for i, entry in enumerate(reversed(self.analyzer.enriched_entries)):
            ts = entry["timestamp"]
            self.query_list.addItem(f"{ts}")  # 날짜/시간만

    def handle_selection(self, item):
        index = self.query_list.currentRow()
        true_index = len(self.analyzer.enriched_entries) - 1 - index
        try:
            entry = self.analyzer.enriched_entries[true_index]
            query = entry["query"]
            analysis = entry["query_analysis"]
            raw_ast = analysis.get("raw_ast", {})
            if isinstance(raw_ast, str):
                try:
                    raw_ast = json.loads(raw_ast)
                except json.JSONDecodeError:
                    raw_ast = {"error": "Invalid AST string"}
            ast_str = json.dumps(raw_ast, indent=2, ensure_ascii=False)
            self._current_ast_str = ast_str

            # 읽기 좋은 형태로 표시
            formatted_query = sqlparse.format(query, reindent=True, keyword_case='upper')
            self.query_box.setPlainText(formatted_query)
            self.flow_box.setPlainText(analysis.get("flow", ""))

            # 아스키박스 시각화
            flow = analysis.get("flow", "")
            self._current_flow_steps = flow.splitlines()
            viz = SQLFlowVisualizer(self._current_flow_steps)
            ascii_text = viz.as_ascii_pipeline()
            self.ascii_box.setPlainText(ascii_text)

        except Exception as e:
            QMessageBox.critical(self, lang.MSG_EXPLAIN_ERROR, str(e))

    def toggle_flow_box(self):
        if self.flow_box.isVisible():
            self.flow_box.hide()
            self.toggle_btn.setText(lang.MSG_COLLAPSE)
            self.splitter.setSizes([700, 0, 1100])
        else:
            self.flow_box.show()
            self.toggle_btn.setText(lang.MSG_EXPAND)
            self.splitter.setSizes([500, 600, 700])  # 비율 적당히 조절

    def show_ast(self):
        if not self._current_ast_str:
            QMessageBox.information(self, lang.MSG_AST_INFO_NONE, lang.MSG_SELECT_QUERY_FIRST)
            return
        dlg = ASTDialog(self._current_ast_str, self)
        dlg.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    inspector = SQLInspectorUI()
    inspector.show()
    sys.exit(app.exec())
