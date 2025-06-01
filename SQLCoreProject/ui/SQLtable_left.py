from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import os
from SQLCoreProject.utils.path_utils import resource_path
from language.lang import lang

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_icon(name):
    resources_dir = resource_path("resources")
    icon_path = os.path.join(resources_dir, f"{name}.png")
    if not os.path.exists(icon_path):
        # 기본 아이콘으로 대체
        icon_path = os.path.join(resources_dir, "db.png" if name in ["db", "duckdb", "sqlite"] else "table.png" if name == "table" else "column.png")
    return QIcon(icon_path)

class SQLTableLeftPanel(QWidget):
    db_switched = Signal(str)
    table_selected = Signal(str)
    column_selected = Signal(str, str)

    def __init__(self, db_list_provider, field_fetcher, db_switcher, parent_ref):
        super().__init__()
        self.get_db_list = db_list_provider
        self.get_fields = field_fetcher
        self.switch_db = db_switcher
        self.parent_ref = parent_ref

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        layout = QVBoxLayout()
        self.title = QLabel(lang.LABEL_DATABASE_STRUCTURE)
        layout.addWidget(self.title)
        layout.addWidget(self.tree)
        self.setLayout(layout)

        self.current_db = None
        self.rebuild_tree()

    def rebuild_tree(self):
        self.tree.clear()
        gate = self.parent_ref.gate
        mode = getattr(gate, 'mode', 'file')
        current_db = gate.get_current_db_name()
        if mode == 'memory':
            # 온보딩/분석 모드: 오직 :memory: 노드만, 그 하위에 메모리 DB의 모든 테이블 표시
            db_item = self._create_item(':memory:', 'db', get_icon('db'))
            self.tree.addTopLevelItem(db_item)
            try:
                for table_name in gate.get_fields(':memory:', ''):
                    table_item = self._create_item(table_name, 'table', get_icon('table'), ':memory:')
                    db_item.addChild(table_item)
                    self._add_columns(':memory:', table_name, table_item)
            except Exception:
                db_item.addChild(QTreeWidgetItem(["[Load Failed]"]))
        else:
            for db_name in self.get_db_list():
                # 아이콘 선택
                if db_name == ":memory:":
                    icon = get_icon("db")
                elif db_name.endswith('.duckdb'):
                    icon = get_icon("duckdb")
                elif db_name.endswith(('.sqlite', '.db', '.sqlite3')):
                    icon = get_icon("sqlite")
                else:
                    icon = get_icon("db")
                db_item = self._create_item(db_name, 'db', icon)
                self.tree.addTopLevelItem(db_item)
                # 현재 연결된 DB만 하위 트리 표시
                if db_name == current_db:
                    try:
                        for table_name in self.get_fields(db_name, ""):
                            table_item = self._create_item(table_name, 'table', get_icon("table"), db_name)
                            db_item.addChild(table_item)
                            self._add_columns(db_name, table_name, table_item)
                    except Exception:
                        db_item.addChild(QTreeWidgetItem(["[Load Failed]"]))
        self.tree.expandToDepth(1)
        self._collapse_all_tables()

    def _create_item(self, text, item_type, icon, db=None, table=None, column=None):
        item = QTreeWidgetItem([text])
        item.setIcon(0, icon)
        if item_type == 'db':
            item.setData(0, Qt.UserRole, (item_type, text))
        elif item_type == 'table':
            item.setData(0, Qt.UserRole, (item_type, db, text))
        elif item_type == 'column':
            item.setData(0, Qt.UserRole, (item_type, db, table, column))
        return item

    def _add_columns(self, db_name, table_name, table_item):
        try:
            for col, col_type in self.get_fields(db_name, table_name):
                label = f"{col} : {col_type}"
                col_item = self._create_item(label, 'column', get_icon("column"), db_name, table_name, col)
                table_item.addChild(col_item)
        except Exception:
            table_item.addChild(QTreeWidgetItem(["[Column Load Failed]"]))

    def _collapse_all_tables(self):
        for i in range(self.tree.topLevelItemCount()):
            db_item = self.tree.topLevelItem(i)
            for j in range(db_item.childCount()):
                self.tree.collapseItem(db_item.child(j))

    def on_item_double_clicked(self, item, column):
        info = item.data(0, Qt.UserRole)
        if info and info[0] == 'db':
            db_name = info[1]
            db_path = os.path.join(self.parent_ref.gate.base_dir, db_name) if db_name != ":memory:" else db_name
            if db_name.endswith('.duckdb'):
                self.parent_ref.plugin_controller.activate_only("DuckDB")
                self.parent_ref.plugin_controller.get_active_plugin().connect(db_path)
                self.parent_ref.gate.switch_database(db_name, dbtype='duckdb')
            elif db_name.endswith(('.sqlite', '.db', '.sqlite3')):
                self.parent_ref.plugin_controller.activate_only("SQLite")
                self.parent_ref.plugin_controller.get_active_plugin().connect(db_path)
                self.parent_ref.gate.switch_database(db_name, dbtype='sqlite')
            elif db_name == ":memory:":
                self.parent_ref.gate.switch_database(":memory:")
            self.parent_ref.log(f"[INFO] DB switched: {db_name}")
            self.parent_ref.refresh_table_list()
            self.rebuild_tree()  # 트리 즉시 갱신
        else:
            try:
                self.switch_db(info[1])
            except Exception as e:
                print(lang.MSG_DB_SWITCH_FAIL.format(db=info[1], error=e))

    def on_item_clicked(self, item, column):
        info = item.data(0, Qt.UserRole)
        if not info:
            return
        if info[0] == 'table':
            self.table_selected.emit(info[2])
        elif info[0] == 'column':
            self.column_selected.emit(info[2], info[3])
