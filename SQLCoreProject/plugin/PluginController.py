class PluginController:
    def __init__(self):
        self.plugins = {}  # {이름: {"module": 모듈, "enabled": bool}}

    def register_plugin(self, name, module):
        self.plugins[name] = {"module": module, "enabled": False}

    def get_plugin_names(self):
        return list(self.plugins.keys())

    def activate_only(self, name):
        for n in self.plugins:
            self.plugins[n]["enabled"] = (n == name)

    def get_active_plugin(self):
        for n, info in self.plugins.items():
            if info["enabled"]:
                return info["module"]
        return None

# 플러그인 예시 등록 (실제 사용 시 main에서 등록)
# from .company_data_loader import CompanyDataPlugin
# from .duckdb_plugin import DuckDBPlugin
# from .sqlite_plugin import SQLitePlugin
# controller = PluginController()
# controller.register_plugin("회사 데이터", CompanyDataPlugin())
# controller.register_plugin("DuckDB", DuckDBPlugin())
# controller.register_plugin("SQLite", SQLitePlugin()) 