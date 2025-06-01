from PySide6.QtWidgets import QToolBar, QFileDialog, QMessageBox, QInputDialog, QMenu, QToolButton
from PySide6.QtGui import QAction, QIcon, Qt
from SQLCoreProject.data.SQLvault import SQLVault, VaultDialog
from SQLCoreProject.plugin.memory_onboarding import MemoryOnboarding
from language.lang import lang
import importlib

import os

class SQLToolbarCapsule(QToolBar):
    def __init__(self, parent=None):
        super().__init__(lang.LABEL_SQL_TOOLS, parent)
        self.parent_ref = parent
        self.vault = SQLVault(self.parent_ref.gate)
        self.setMovable(False)
        # 메모리 온보딩 인스턴스 준비
        if not hasattr(self.parent_ref.gate, 'memory_onboarding'):
            self.parent_ref.gate.memory_onboarding = MemoryOnboarding(self.parent_ref.gate)

        # 메뉴 준비
        self.file_menu = QMenu()
        self.new_action = QAction(lang.BTN_CREATE_DB, self)
        self.new_action.triggered.connect(self.new_file)
        self.file_menu.addAction(self.new_action)
        self.open_action = QAction(lang.BTN_OPEN_DB, self)
        self.open_action.triggered.connect(self.open_db)
        self.file_menu.addAction(self.open_action)
        self.save_action = QAction(lang.BTN_SAVE_AS_EXCEL, self)
        self.save_action.triggered.connect(self.save_excel)
        self.file_menu.addAction(self.save_action)
        # 메모리 온보딩을 File 메뉴 하위로 이동
        self.memory_onboarding_action_item = QAction(lang.LABEL_MEMORY_ONBOARDING, self)
        self.memory_onboarding_action_item.triggered.connect(self.memory_onboarding_action)
        self.file_menu.addAction(self.memory_onboarding_action_item)

        # 설정 메뉴 및 언어 선택
        self.settings_menu = QMenu()
        self.language_menu = QMenu(lang.LABEL_LANGUAGE, self)
        self.lang_ko_action = QAction(lang.LABEL_KOREAN, self)
        self.lang_en_action = QAction(lang.LABEL_ENGLISH, self)
        self.language_menu.addAction(self.lang_ko_action)
        self.language_menu.addAction(self.lang_en_action)
        self.settings_menu.addMenu(self.language_menu)
        # 버튼 추가
        def add_button(text, triggered=None, menu=None):
            btn = QToolButton(self)
            btn.setText(text)
            btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
            btn.setFixedWidth(100)
            btn.setStyleSheet("margin: 0px; padding: 6px 10px;")
            if triggered:
                btn.clicked.connect(triggered)
            if menu:
                btn.setPopupMode(QToolButton.InstantPopup)
                btn.setMenu(menu)
            self.addWidget(btn)
            return btn  # 버튼 객체 반환

        # 실제 버튼 등록
        add_button(lang.LABEL_FILE, menu=self.file_menu)
        add_button(lang.LABEL_REFRESH, triggered=self.refresh_tables)
        add_button(lang.LABEL_RUN, triggered=self.run_query)
        add_button(lang.LABEL_QUERY_VAULT, triggered=self.open_vault_dialog)
        self.settings_btn = add_button(lang.LABEL_SETTINGS, menu=self.settings_menu)  # 인스턴스 변수로 저장

        # 언어 변경 핸들러
        self.lang_ko_action.triggered.connect(lambda: self.change_language('ko'))
        self.lang_en_action.triggered.connect(lambda: self.change_language('en'))

    # ------------------ 연결 함수들 ------------------
    def new_file(self):
        if self.parent_ref:
            self.parent_ref.create_db()  # SQLGate의 DB 생성 함수 호출

    def open_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, lang.MSG_OPEN_DB_TITLE, "", lang.MSG_DUCKDB_FILE_FILTER)
        if path:
            self.parent_ref.open_db(path)

    def open_vault_dialog(self):
        dlg = VaultDialog(self.vault, parent=self.parent_ref)
        dlg.exec()

    def save_excel(self):
        if self.parent_ref:
            self.parent_ref.export_to_excel()  # 쿼리 결과 엑셀 저장

    def refresh_tables(self):
        if self.parent_ref:
            self.parent_ref.refresh_table_list()

    def run_query(self):
        parent = self.parent_ref
        query_input = parent.tab_sheet.get_current_query_input()
        if not query_input:
            parent.log(lang.MSG_NO_TAB_SELECTED)
            return

        cursor = query_input.textCursor()
        selected = cursor.selectedText()
        query = selected.replace('\u2029', '\n') if selected.strip() else query_input.toPlainText().strip()

        if not query:
            parent.log(lang.MSG_NO_QUERY_ERROR)
            QMessageBox.warning(self, lang.MSG_NO_QUERY_TITLE, lang.MSG_NO_QUERY_BODY)
            return

        try:
            result = parent.execute_query(query)
            parent.display_result(result)
        except Exception as e:
            parent.log(lang.MSG_SQL_ERROR.format(error=e))
            QMessageBox.critical(self, lang.MSG_SQL_ERROR_TITLE, str(e))

    def memory_onboarding_action(self):
        base_dir = getattr(self.parent_ref.gate, 'base_dir', "")
        file_path, _ = QFileDialog.getOpenFileName(self, lang.MSG_ONBOARDING_FILE_SELECT, base_dir, "Data Files (*.csv *.xlsx *.xls *.parquet *.db *.sqlite *.duckdb);;All Files (*)")
        if file_path:
            try:
                self.parent_ref.gate.memory_onboarding.load_file_to_memory(file_path)
            except Exception as e:
                QMessageBox.critical(self, lang.MSG_ONBOARDING_FAIL_TITLE, lang.MSG_ONBOARDING_FAIL.format(error=e))

    def change_language(self, lang_code):
        lang.set_language(lang_code)
        # 주요 버튼/메뉴 라벨 갱신
        toolbar_buttons = [self.widgetForAction(a) for a in self.actions()]
        toolbar_buttons[0].setText(lang.LABEL_FILE)
        toolbar_buttons[1].setText(lang.LABEL_REFRESH)
        toolbar_buttons[2].setText(lang.LABEL_RUN)
        toolbar_buttons[3].setText(lang.LABEL_QUERY_VAULT)
        self.memory_onboarding_action_item.setText(lang.LABEL_MEMORY_ONBOARDING)
        self.settings_menu.setTitle(lang.LABEL_SETTINGS)
        self.language_menu.setTitle(lang.LABEL_LANGUAGE)
        self.lang_ko_action.setText(lang.LABEL_KOREAN)
        self.lang_en_action.setText(lang.LABEL_ENGLISH)
        self.settings_btn.setText(lang.LABEL_SETTINGS)  # 버튼 텍스트 동적 갱신
