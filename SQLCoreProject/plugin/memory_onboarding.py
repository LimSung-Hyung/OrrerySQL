import psutil
import pandas as pd
import os

class MemoryOnboarding:
    def __init__(self, sqlgate):
        self.sqlgate = sqlgate  # SQLgate 인스턴스 참조

    def load_file_to_memory(self, file_path):
        orrery_dir = os.path.abspath(self.sqlgate.base_dir)
        file_path_abs = os.path.abspath(file_path)
        if not file_path_abs.startswith(orrery_dir):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "경로 제한", f"OrrerySQL 폴더 내부 파일만 온보딩 가능합니다.\n\n{orrery_dir} 내부로 파일을 복사해 주세요.")
            return
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(file_path)
            self.sqlgate.switch_database(":memory:")
            try:
                self.sqlgate.con.register("onboarded", df)
            except Exception as e:
                raise
            try:
                self.sqlgate.log(f"[INFO] CSV 파일을 메모리로 온보딩 완료: {file_path} (rows={len(df)})")
            except Exception as e:
                pass
        elif ext in ('.xlsx', '.xls'):
            df = pd.read_excel(file_path)
            self.sqlgate.switch_database(":memory:")
            try:
                self.sqlgate.con.register("onboarded", df)
            except Exception as e:
                raise
            try:
                self.sqlgate.log(f"[INFO] Excel 파일을 메모리로 온보딩 완료: {file_path} (rows={len(df)})")
            except Exception as e:
                pass
        elif ext == '.parquet':
            df = pd.read_parquet(file_path)
            self.sqlgate.switch_database(":memory:")
            try:
                self.sqlgate.con.register("onboarded", df)
            except Exception as e:
                raise
            try:
                self.sqlgate.log(f"[INFO] Parquet 파일을 메모리로 온보딩 완료: {file_path} (rows={len(df)})")
            except Exception as e:
                pass
        elif ext == '.duckdb':
            import duckdb
            file_con = duckdb.connect(file_path)
            tables = [row[0] for row in file_con.execute("SHOW TABLES").fetchall()]
            self.sqlgate.switch_database(":memory:")
            for table_name in tables:
                try:
                    df = file_con.execute(f"SELECT * FROM {table_name}").fetchdf()
                    self.sqlgate.con.register(table_name, df)
                except Exception as e:
                    raise
            file_con.close()
            try:
                self.sqlgate.log(f"[INFO] DuckDB 파일을 메모리로 온보딩 완료: {file_path} (tables={len(tables)})")
            except Exception as e:
                pass
        elif ext in ('.db', '.sqlite', '.sqlite3'):
            import sqlite3
            self.sqlgate.switch_database(":memory:")
            src_con = sqlite3.connect(file_path)
            tables = [row[0] for row in src_con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            for table in tables:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", src_con)
                    self.sqlgate.con.register(table, df)
                except Exception as e:
                    raise
            src_con.close()
            try:
                self.sqlgate.log(f"[INFO] SQLite 파일을 메모리로 온보딩 완료: {file_path} (tables={len(tables)})")
            except Exception as e:
                pass
        else:
            raise ValueError("지원하지 않는 파일 형식")
        self.sqlgate.mode = 'memory'  # 온보딩/분석 모드 진입 시 책임 분리
        self.check_memory_usage()
        try:
            parent = getattr(self.sqlgate, 'parent_ref', None)
            if parent:
                try:
                    if hasattr(parent, 'switch_database'):
                        parent.switch_database(":memory:")
                    if hasattr(parent, 'refresh_table_list'):
                        parent.refresh_table_list()
                    if hasattr(parent, 'table_panel'):
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(0, parent.table_panel.rebuild_tree)
                except Exception as e:
                    pass
        except Exception as e:
            raise

    def check_memory_usage(self, limit_mb=500):
        mem = psutil.Process().memory_info().rss / (1024 * 1024)
        if mem > limit_mb:
            self.sqlgate.log(f"[경고] 메모리 사용량 {mem:.1f}MB (임계치 {limit_mb}MB 초과!)")

    def is_write_query(self, query):
        return query.strip().split()[0].upper() in {"INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"}

    def execute_query(self, query):
        if self.is_write_query(query):
            self.sqlgate.log("[ERROR] :memory: 분석 모드에서는 쓰기 쿼리 금지!")
            return None
        return self.sqlgate.execute_query(query) 