import os
import json
from language.lang import lang

class SQLVault:
    def __init__(self, sqlgate):
        self.vault_path = os.path.join(sqlgate.base_dir, "sql_vault.json")
        self._load_vault()

    def _load_vault(self):
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, 'r', encoding='utf-8') as f:
                    self.vault = json.load(f)
            except Exception:
                self.vault = {}
        else:
            self.vault = {}

    def _save_vault(self):
        try:
            with open(self.vault_path, 'w', encoding='utf-8') as f:
                json.dump(self.vault, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(lang.MSG_VAULT_SAVE_FAIL.format(error=e))

    def save_query(self, name, query):
        self.vault[name] = query
        self._save_vault()

    def get_query(self, name):
        return self.vault.get(name, "")

    def delete_query(self, name):
        if name in self.vault:
            del self.vault[name]
            self._save_vault()
            return True
        return False

    def list_queries(self):
        return list(self.vault.keys())

    def overwrite_query(self, name, query):
        # 그냥 save_query와 동일
        self.save_query(name, query)

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QTextEdit, QInputDialog, QMessageBox

class VaultDialog(QDialog):
    def __init__(self, vault, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.setWindowTitle(lang.LABEL_QUERY_VAULT)
        self.setGeometry(200, 200, 550, 300)
        layout = QVBoxLayout(self)

        # 쿼리 리스트
        self.list = QListWidget()
        self.list.addItems(self.vault.list_queries())
        self.list.currentItemChanged.connect(self.load_selected_query)
        layout.addWidget(self.list)

        # 쿼리 에디터
        self.editor = QTextEdit()
        layout.addWidget(self.editor)

        # 버튼
        btns = QHBoxLayout()
        self.btn_load = QPushButton(lang.BTN_LOAD)
        self.btn_save = QPushButton(lang.BTN_SAVE_OVERWRITE)
        self.btn_delete = QPushButton(lang.BTN_DELETE)
        btns.addWidget(self.btn_load)
        btns.addWidget(self.btn_save)
        btns.addWidget(self.btn_delete)
        layout.addLayout(btns)

        self.btn_load.clicked.connect(self.load_query_to_parent)
        self.btn_save.clicked.connect(self.save_query)
        self.btn_delete.clicked.connect(self.delete_query)

    def load_selected_query(self, curr, prev):
        if curr:
            name = curr.text()
            self.editor.setPlainText(self.vault.get_query(name))
        else:
            self.editor.clear()

    def load_query_to_parent(self):
        text = self.editor.toPlainText()
        parent = self.parent()
        if parent and hasattr(parent, "tab_sheet"):
            query_input = parent.tab_sheet.get_current_query_input()
            if query_input:
                query_input.setPlainText(text)
        self.close()

    def save_query(self):
        name, ok = QInputDialog.getText(self, lang.MSG_ENTER_QUERY_NAME_TITLE, lang.MSG_ENTER_QUERY_NAME_LABEL)
        if ok and name:
            query = self.editor.toPlainText()
            self.vault.save_query(name, query)
            self.list.clear()
            self.list.addItems(self.vault.list_queries())

    def delete_query(self):
        curr = self.list.currentItem()
        if curr:
            name = curr.text()
            ok = QMessageBox.question(self, lang.MSG_DELETE_TITLE, lang.MSG_DELETE_CONFIRM.format(name=name))
            if ok:
                self.vault.delete_query(name)
                self.list.clear()
                self.list.addItems(self.vault.list_queries())
                self.editor.clear()

