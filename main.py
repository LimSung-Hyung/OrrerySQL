from SQLCoreProject.plugin.PluginController import PluginController
# from SQLCoreProject.plugin.company_data_loader import CompanyDataPlugin
from SQLCoreProject.plugin.duckdb_plugin import DuckDBPlugin
from SQLCoreProject.plugin.sqlite_plugin import SQLitePlugin
from PySide6.QtWidgets import QApplication
import sys
import traceback

def main():
    """Main entry point for the application."""
    try:
        print("[DEBUG] Application starting...")
        
        print("[DEBUG] Importing SQLGateUI...")
        from SQLCoreProject.ui.SQLgateUI import SQLGateUI, load_theme
        print("[DEBUG] SQLGateUI imported successfully")
        
        print("[DEBUG] Creating PluginController...")
        controller = PluginController()
        print("[DEBUG] Registering plugins...")
        # controller.register_plugin("회사 데이터", CompanyDataPlugin())
        controller.register_plugin("DuckDB", DuckDBPlugin())
        controller.register_plugin("SQLite", SQLitePlugin())
        print("[DEBUG] Plugins registered successfully")

        print("[DEBUG] Creating QApplication...")
        app = QApplication(sys.argv)
        print("[DEBUG] QApplication created successfully")
        
        print("[DEBUG] Loading theme...")
        # 다크 테마 로드
        load_theme("resources/theme_dark.qss")
        print("[DEBUG] Theme loaded successfully")
        
        print("[DEBUG] Creating main window...")
        window = SQLGateUI(controller)
        print("[DEBUG] Main window created successfully")
        
        print("[DEBUG] Showing window...")
        window.show()
        print("[DEBUG] Window shown successfully")
        
        print("[DEBUG] Starting event loop...")
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"[ERROR] Application failed to start: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        input("Press Enter to continue...")

if __name__ == "__main__":
    main() 