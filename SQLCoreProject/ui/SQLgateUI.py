from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QFileDialog,
    QListWidget, QListWidgetItem, QPlainTextEdit, QStyle, QMainWindow, QToolBar, QComboBox
)
from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import QPainter, QColor, QTextFormat, QIcon, QPixmap
from SQLCoreProject.data.SQLteach import SQLHighlighter, AutoCapitalizingTextEdit, set_global_patterns, capitalize_sql_keywords
from SQLCoreProject.ui.SQLtoolbar import SQLToolbarCapsule
from SQLCoreProject.data.SQLgate import SQLgate, get_logs_dir
from SQLCoreProject.ui.SQLhotkey import SQLHotkeyManager
from SQLCoreProject.ui.SQLtabsheet import SQLTabSheet
from SQLCoreProject.ui.SQLmultibridge import SQLMultiBridge
from SQLCoreProject.ui.SQLtable_left import SQLTableLeftPanel
from SQLCoreProject.ui.SQLmulti_result import SQLMultiResult
from SQLCoreProject.data.SQLresultToWide import SQLWideResultDialog
from SQLCoreProject.ui.SQLhint import SQLAutoCompleter
from SQLCoreProject.data.SQLqueryinput import QueryInputWithLineNumber
from SQLCoreProject.plugin.company_log_plugin import log_company_history
import sys, os, json, datetime
from SQLCoreProject.utils.path_utils import resource_path
from language.lang import lang

class SQLGateUI(QMainWindow):
    def __init__(self, plugin_controller):
        super().__init__()
        self.plugin_controller = plugin_controller
        self.gate = SQLgate()
        self.base_dir = self.gate.base_dir
        self.setWindowTitle("Orrery SQL Developer")
        self.gate.log = self.log

        # QMainWindow에서는 QWidget을 만들어 centralWidget으로 등록해야 함
        central_widget = QWidget()
        vbox = QVBoxLayout(central_widget)

        self.main_layout = QHBoxLayout()
        # 툴바는 QMainWindow에만 추가
        self.toolbar = SQLToolbarCapsule(self)
        self.addToolBar(self.toolbar)
        vbox.addLayout(self.main_layout)
        self.setLayout(vbox)

        self.table_panel = SQLTableLeftPanel(
            db_list_provider=self.gate.get_db_list,
            field_fetcher=self.gate.get_fields,
            db_switcher=self.switch_database,
            parent_ref=self
        )
        self.main_layout.addWidget(self.table_panel, 2)
        self.resize(1440, 900)

        # LEFT LAYOUT (쿼리/탭/결과 전체)
        self.left_layout = QVBoxLayout()
        self.query_label = QLabel(lang.LABEL_QUERY_INPUT)
        self.left_layout.addWidget(self.query_label)

        self.tab_sheet = SQLTabSheet()
        self.tab_sheet.set_query_input_factory(self.create_query_input)
        self.left_layout.addWidget(self.tab_sheet)

        self.bridge = SQLMultiBridge(self.tab_sheet, self.run_query_from_bridge, self.gate)

        try:
            path = os.path.join(get_logs_dir(), "last_queries.txt")
            with open(path, "r", encoding="utf-8") as f:
                contents = f.read()
            blocks = [b.strip() for b in contents.split("\n\n---TAB---\n\n") if b.strip()]
            if blocks:
                for i, block in enumerate(blocks):
                    lines = block.splitlines()
                    tab_name = lines[0][4:].strip() if lines and lines[0].startswith("### ") else f"Console {i+1}"
                    query = "\n".join(lines[1:]) if lines and lines[0].startswith("### ") else block
                    query_input = self.create_query_input()
                    widget = self.tab_sheet._wrap_input(query_input)
                    index = self.tab_sheet.addTab(widget, tab_name)
                    self.tab_sheet.setCurrentIndex(index)
                    self.tab_sheet.query_inputs.append(query_input)
                    query_input.setPlainText(query)
            else:
                self.tab_sheet.create_new_console()
        except FileNotFoundError:
            self.tab_sheet.create_new_console()

        # ------[여기서 패널 구조를 올바르게 잡는다]------

        # 1. 상단 라벨+버튼 한 줄(HBox)
        result_top_bar = QHBoxLayout()
        self.result_label = QLabel(lang.LABEL_QUERY_RESULT_TABLE)
        result_top_bar.addWidget(self.result_label)
        result_top_bar.addStretch(1)
        self.inspect_btn = QPushButton()
        self.inspect_btn.setToolTip(lang.TOOLTIP_QUERY_ANALYSIS)
        self.inspect_btn.setFixedSize(32, 32)
        icon_path = resource_path(os.path.join("resources", "telescope.png"))
        self.inspect_btn.setIcon(QIcon(QPixmap(icon_path)))
        self.inspect_btn.setIconSize(QSize(26, 26))
        self.inspect_btn.clicked.connect(self.show_sql_inspector)
        result_top_bar.addWidget(self.inspect_btn)

        # 2. 결과탭(테이블)
        self.result_tabs = SQLMultiResult()

        # 3. 패널 위-아래로 수직 결합(VBox)
        result_panel = QVBoxLayout()
        result_panel.addLayout(result_top_bar)         # 한 줄짜리 HBox
        result_panel.addWidget(self.result_tabs)       # 그 아래 결과탭

        # 4. 전체 left_layout에 이 패널만 추가
        self.left_layout.addLayout(result_panel)

        # 5. main_layout에 left_layout 추가(가로 8 비율)
        self.main_layout.addLayout(self.left_layout, 8)

        # ----- LOG 패널/오른쪽 -----
        self.log_panel = QVBoxLayout()
        self.log_label = QLabel(lang.LABEL_LOG_TERMINAL)
        self.log_panel.addWidget(self.log_label)
        self.log_console = QueryInputWithLineNumber(highlight=False)
        self.log_console.setReadOnly(True)
        self.log_console.setPlaceholderText(lang.PLACEHOLDER_LOG_CONSOLE)
        self.log_panel.addWidget(self.log_console)
        self.main_layout.addLayout(self.log_panel, 3)

        self.hotkey_manager = SQLHotkeyManager(self)
        self.refresh_table_list()

        # QMainWindow에 centralWidget 등록
        self.setCentralWidget(central_widget)

    def create_query_input(self):
        query_input = QueryInputWithLineNumber()
        completer = SQLAutoCompleter(query_input)
        query_input.completer = completer  # 이걸로만 사용

        self.completer = completer
        self.completer.update_keywords(
            self.gate.get_table_names(),
            self.gate.get_all_column_names()
        )
        
        query_input.execute_query_signal.connect(self.bridge.run_current_query)

        self.completer = SQLAutoCompleter(query_input)
        tables = self.gate.get_table_names()
        columns = self.gate.get_all_column_names()
        self.completer.update_keywords(tables, columns)  # ✅ 완전히 동일 객체 참조
        return query_input

    def run_query_from_bridge(self, sql):
        if not sql:
            self.log(lang.MSG_NO_QUERY_ERROR)
            QMessageBox.warning(self, lang.MSG_NO_QUERY_TITLE, lang.MSG_NO_QUERY_BODY)
            return
        try:
            self.last_executed_query = sql
            result = self.execute_query(sql)
            self.display_result(result)
        except Exception as e:
            self.log(lang.MSG_SQL_ERROR.format(error=e))
            QMessageBox.critical(self, lang.MSG_SQL_ERROR_TITLE, str(e))

    def log(self, msg):
        self.log_console.appendPlainText(str(msg))

    def switch_database(self, filename):
        self.gate.switch_database(filename)
        self.log(lang.MSG_DB_SWITCHED.format(filename=filename))
        self.refresh_table_list()

        # ✅ 자동완성 키워드 갱신
        current_input = self.tab_sheet.get_current_query_input()
        if current_input and hasattr(current_input, "completer"):
            current_input.completer.update_keywords(
                self.gate.get_table_names(),
                self.gate.get_all_column_names()
            )

    def switch_to_raw_world(self):
        """[INFO] Switched to raw world (file-based)"""
        self.gate.switch_to_raw_world()
        self.log(lang.MSG_SWITCHED_RAW_WORLD)
        self.refresh_table_list()

    def create_db(self):
        path, _ = QFileDialog.getSaveFileName(self, lang.MSG_CREATE_DB_TITLE, "newfile.duckdb", lang.MSG_DUCKDB_FILE_FILTER)
        if not path:
            return
        if not path.endswith('.duckdb'):
            path += '.duckdb'
        try:
            self.gate.create_db(path)
            self.log(lang.MSG_NEW_DB_CONNECTED.format(path=path))
            self.refresh_table_list()
            QMessageBox.information(self, lang.MSG_CREATE_DB_COMPLETE_TITLE, lang.MSG_NEW_DB_CONNECTED_BODY.format(path=path))
        except Exception as e:
            self.log(lang.MSG_CREATE_DB_FAIL.format(error=e))
            QMessageBox.critical(self, lang.MSG_CREATE_DB_FAIL_TITLE, lang.MSG_CREATE_DB_FAIL_BODY.format(error=e))

    def show_current_result_wide(self):
        df = self.result_tabs.get_current_dataframe()
        if df is not None and not df.empty:
            dialog = SQLWideResultDialog(df, self)
            dialog.show()

    def open_db(self, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, lang.MSG_OPEN_DB_TITLE, "", lang.MSG_DUCKDB_FILE_FILTER)
            if not path:
                return
        self.gate.open_db(path)
        self.log(lang.MSG_DB_CONNECTED.format(path=path))
        self.refresh_table_list()

    def refresh_table_list(self):
        self.table_panel.rebuild_tree()

        try: # 패턴 전달 (table/column highlighting용)
            db = self.gate.get_current_db_name()
            tables = self.gate.refresh_table_list()
            columns = []
            for table in tables:
                fields = self.gate.get_fields(db, table)
                columns.extend([col[0] for col in fields])
            set_global_patterns(tables, columns)

            for query_input in self.tab_sheet.query_inputs:
                if hasattr(query_input, "highlighter"):
                    query_input.highlighter.rehighlight()
                if hasattr(query_input, "completer"):
                    query_input.completer.update_keywords(tables, columns)

        except Exception as e:
            self.log(lang.MSG_FAILED_GENERATE_TABLE_COLUMN_PATTERNS.format(error=e))

    def insert_column_to_query(self, table, column):
        query_input = self.tab_sheet.get_current_query_input()
        if query_input:
            query_input.insertPlainText(column)

    def handle_table_clicked(self, item):
        table = item.text()
        self.field_list.clear()
        fields = self.gate.get_fields(table)
        for col, col_type in fields:
            self.field_list.addItem(f"{col} : {col_type}")
        # *** 컬럼 클릭 시 컬럼명도 패턴 갱신 ***
        self.update_highlighter_patterns()

    def update_highlighter_patterns(self):
        tables = [self.table_list.item(i).text() for i in range(self.table_list.count())]
        columns = []
        for i in range(self.field_list.count()):
            col = self.field_list.item(i).text().split(":")[0].strip()
            columns.append(col)

        from SQLCoreProject.data.SQLteach import set_global_patterns
        set_global_patterns(tables, columns) 

    def auto_capitalize_keywords(self):
        query_input = self.tab_sheet.get_current_query_input()
        if not query_input:
            self.log(lang.MSG_NO_QUERY_INPUT_WINDOW)
            return

        cursor = query_input.textCursor()
        pos = cursor.position()
        text = query_input.toPlainText()

        new_text = capitalize_sql_keywords(text)

        if new_text != text:
            query_input.blockSignals(True)
            query_input.setPlainText(new_text)
            cursor.setPosition(pos)
            query_input.setTextCursor(cursor)
            query_input.blockSignals(False)
            self.log(lang.MSG_SQL_KEYWORDS_CAPITALIZED)
        else:
            self.log(lang.MSG_NO_KEYWORDS_TO_CAPITALIZE)

    def export_to_excel(self, df, path):
        return self.gate.export_to_excel(df, path)

    def run_query(self):
        query_input = self.tab_sheet.get_current_query_input()
        if query_input:
            cursor = query_input.textCursor()
            selected = cursor.selectedText()
            if selected.strip():
                query = selected.replace('\u2029', '\n')
            else:
                query = query_input.toPlainText().strip()

            if not query:
                self.log(lang.MSG_NO_QUERY_ERROR)
                return
            try:
                self.last_executed_query = query
                result = self.execute_query(query)
                self.display_result(result)

                # ✅ 자동완성 키워드 갱신
                self.completer.update_keywords(
                    self.gate.get_table_names(),
                    self.gate.get_all_column_names()
                )

            except Exception as e:
                self.log(lang.MSG_SQL_ERROR.format(error=e))

    def execute_query(self, query):   
        self.last_executed_query = query    # 내부적으로 gate의 execute_query 사용
        return self.gate.execute_query(query)

    def switch_to_raw_world(self):
        self.gate.switch_to_raw_world()
        self.log(lang.MSG_SWITCHED_RAW_WORLD)
        self.refresh_table_list()

    def show_sql_inspector(self):
        try:
            from SQLCoreProject.core.SQLquery_analysis import SQLInspectorUI
            self.inspector_window = SQLInspectorUI()
            self.inspector_window.setWindowModality(Qt.ApplicationModal)
            self.inspector_window.setAttribute(Qt.WA_DeleteOnClose)
            self.inspector_window.show()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            import traceback
            tb = traceback.format_exc()
            QMessageBox.critical(self, lang.MSG_SQL_INSPECTOR_ERROR_TITLE,
                f"{lang.MSG_SQL_INSPECTOR_ERROR_BODY}\n\n{e}\n\n{tb}")

    def display_result(self, df):
        if df is None:
            self.log(lang.MSG_SQL_ERROR.format(error="쿼리 결과가 None입니다. (execute_query 반환값 확인 필요)"))
            return
        if df.empty:
            self.log(lang.MSG_NO_RESULT)
            QMessageBox.information(self, lang.MSG_NO_RESULT_TITLE, lang.MSG_NO_RESULT_BODY)
            return

        self.result_tabs.add_result(df)

        try:
            query_text = getattr(self, "last_executed_query", lang.MSG_NO_QUERY_CAPTURED)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            json_path = os.path.join(get_logs_dir(), "query_log.json")
            log_entry = {
                "timestamp": timestamp,
                "query": query_text,
                "summary": {
                    "row_count": len(df),
                    "columns": list(df.columns)
                }
            }

            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []

            data.append(log_entry)
            data = data[-5:]

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.log(lang.MSG_FAILED_SAVE_QUERY_LOG.format(error=e))


    def export_to_excel(self):
        df = self.result_tabs.get_current_dataframe()
        if df.empty:
            self.log(lang.MSG_EXPORT_NO_RESULT)
            QMessageBox.warning(self, lang.MSG_EXPORT_NO_RESULT_TITLE, lang.MSG_EXPORT_NO_RESULT_BODY)
            return
        path, _ = QFileDialog.getSaveFileName(self, lang.MSG_EXPORT_EXCEL_TITLE, "query_result.xlsx", lang.MSG_EXCEL_FILE_FILTER)
        if path:
            try:
                self.gate.export_to_excel(df, path)
                self.log(lang.MSG_EXPORT_SUCCESS.format(path=path))
                QMessageBox.information(self, lang.MSG_EXPORT_SUCCESS_TITLE, lang.MSG_EXPORT_SUCCESS_BODY.format(path=path))
            except Exception as e:
                self.log(lang.MSG_EXPORT_FAIL.format(error=e))
                QMessageBox.critical(self, lang.MSG_EXPORT_FAIL_TITLE, lang.MSG_EXPORT_FAIL_BODY.format(error=e))

    def closeEvent(self, event):
        path = os.path.join(get_logs_dir(), "last_queries.txt")
        try:
            os.makedirs(get_logs_dir(), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for i, q in enumerate(self.tab_sheet.query_inputs):
                    tab_name = self.tab_sheet.tabText(i)
                    f.write(f"### {tab_name}\n")
                    f.write(q.toPlainText().strip())
                    f.write("\n\n---TAB---\n\n")
        except Exception as e:
            self.log(lang.MSG_SAVE_FAIL.format(error=e))

        super().closeEvent(event)

    def on_plugin_selected(self, plugin_name):
        if plugin_name in ["DuckDB", "SQLite"]:
            file_path, _ = QFileDialog.getOpenFileName(self, lang.MSG_PLUGIN_FILE_SELECT_TITLE.format(plugin=plugin_name), "", lang.MSG_DB_FILE_FILTER)
            if file_path:
                self.plugin_controller.activate_only(plugin_name)
                self.plugin_controller.get_active_plugin().connect(file_path)
        elif plugin_name == "회사 데이터":
            folder_path = QFileDialog.getExistingDirectory(self, lang.MSG_COMPANY_DATA_FOLDER_SELECT)
            if folder_path:
                self.plugin_controller.activate_only(plugin_name)
                self.plugin_controller.get_active_plugin().load(folder_path)

def load_theme(theme_path):
    import os
    from PySide6.QtWidgets import QApplication
    
    print(f"[DEBUG] Theme loading started: {theme_path}")
    print(f"[DEBUG] sys._MEIPASS exists: {hasattr(__import__('sys'), '_MEIPASS')}")
    
    resources_dir = resource_path("resources")
    print(f"[DEBUG] Resources directory: {resources_dir}")
    
    qss_path = os.path.join(resources_dir, os.path.basename(theme_path))
    print(f"[DEBUG] QSS file path: {qss_path}")
    print(f"[DEBUG] QSS file exists: {os.path.exists(qss_path)}")
    
    if os.path.exists(resources_dir):
        print(f"[DEBUG] Files in resources dir: {os.listdir(resources_dir)}")
    else:
        print(f"[DEBUG] Resources directory does not exist!")
    
    try:
        with open(qss_path, 'r', encoding='utf-8') as f:
            qss = f.read()
        print(f"[DEBUG] QSS file read successfully, length: {len(qss)}")
        
        qss = qss.replace("{RES_PATH}", resources_dir.replace("\\", "/"))
        normalized_path = resources_dir.replace("\\", "/")
        print(f"[DEBUG] QSS resource path replaced: {normalized_path}")
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
            print(f"[INFO] Theme loaded successfully: {qss_path}")
        else:
            print("[ERROR] No QApplication instance found")
    except FileNotFoundError:
        print(f"[ERROR] Theme file not found: {qss_path}")
    except Exception as e:
        print(f"[ERROR] Failed to load theme: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    from SQLCoreProject.plugin.PluginController import PluginController
    from SQLCoreProject.plugin.company_data_loader import CompanyDataPlugin
    from SQLCoreProject.plugin.duckdb_plugin import DuckDBPlugin
    from SQLCoreProject.plugin.sqlite_plugin import SQLitePlugin

    app = QApplication(sys.argv)
    load_theme("resources/theme_dark.qss")  # 또는 "resources/theme_light.qss"

    controller = PluginController()
    controller.register_plugin("회사 데이터", CompanyDataPlugin())
    controller.register_plugin("DuckDB", DuckDBPlugin())
    controller.register_plugin("SQLite", SQLitePlugin())

    win = SQLGateUI(controller)

    def save_all_queries_and_tab_names():    # 모든 탭의 쿼리 구문 저장
        path = os.path.join(win.base_dir, "last_queries.txt")
        try:
            os.makedirs(win.base_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for i, q in enumerate(win.tab_sheet.query_inputs):
                    tab_name = win.tab_sheet.tabText(i)
                    f.write(f"### {tab_name}\n")
                    f.write(q.toPlainText().strip())
                    f.write("\n\n---TAB---\n\n")
        except Exception as e:
            print(f"[ERROR] Save failed: {e}")

    win.show()
    sys.exit(app.exec())
