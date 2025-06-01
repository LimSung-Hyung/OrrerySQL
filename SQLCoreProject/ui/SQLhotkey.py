try:
    from PySide6.QtGui import QKeySequence, QShortcut
    QKEYSEQUENCE_FROM = 'QtGui'
except ImportError:
    from PySide6.QtWidgets import QKeySequence, QShortcut
    QKEYSEQUENCE_FROM = 'QtWidgets'

class SQLHotkeyManager:
    def __init__(self, ui):
        self.ui = ui
        self.shortcuts = []
        self._register()

    def _register(self): #키 모음
        self.add_hotkey("Ctrl+Return", self.ui.run_query)
        self.add_hotkey("Ctrl+Enter", self.ui.run_query)
        self.add_hotkey("Ctrl+Shift+E", self.ui.export_to_excel)
        self.add_hotkey("Ctrl+O", self.ui.open_db)
        self.add_hotkey("Ctrl+N", self.ui.create_db)
        self.add_hotkey("Ctrl+R", self.ui.refresh_table_list)
        self.add_hotkey("Ctrl+W", self.ui.switch_to_raw_world)

        # Undo/Redo using current query input in tab
        self.add_hotkey("Ctrl+Z", lambda: self._safe_call("undo"))
        self.add_hotkey("Ctrl+Y", lambda: self._safe_call("redo"))

        self.add_hotkey("Ctrl+L", lambda: self.ui.log_console.setFocus())

        # 🔍 현재 결과 확대 보기
        self.add_hotkey("Ctrl+Space", self.ui.show_current_result_wide)

    def add_hotkey(self, keyseq, callback):
        sc = QShortcut(QKeySequence(keyseq), self.ui)
        sc.activated.connect(callback)
        self.shortcuts.append(sc)

    def _safe_call(self, method):
        query = self.ui.tab_sheet.get_current_query_input()
        if query and hasattr(query, method):
            getattr(query, method)()

