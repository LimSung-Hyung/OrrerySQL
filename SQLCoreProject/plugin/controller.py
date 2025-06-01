from SQLCoreProject.plugin.company_data_loader import load_company_data_files
from SQLCoreProject.plugin.company_log_plugin import log_company_history

class PluginController:
    def __init__(self, base_dir, key):
        self.base_dir = base_dir
        self.key = key

    def load_company_data(self):
        return load_company_data_files(self.base_dir, self.key)

    def log_company(self, msg):
        log_company_history(msg) 