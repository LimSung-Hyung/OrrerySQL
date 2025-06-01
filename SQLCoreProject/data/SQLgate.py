import pandas as pd
import duckdb
import os, json
import time
# from SQLCoreProject.data.ERPEdu import decrypt_json  # ERP 관련이므로 주석 처리 또는 삭제
# from SQLCoreProject.data.Key_loader import load_key
# from SQLCoreProject.plugin.company_log_plugin import log_company_history
# from SQLCoreProject.plugin.company_data_loader import load_company_data_files
from SQLCoreProject.utils.path_utils import get_user_data_dir, get_logs_dir, get_cache_dir, get_company_data_dir
# from SQLCoreProject.plugin.controller import PluginController
from language.lang import lang

# 사용자 데이터 폴더 결정 함수 (OS별 표준)
def get_user_data_dir(app_name='OrrerySQL'):
    import sys
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
    elif sys.platform == 'darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    data_dir = os.path.join(base, app_name)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_logs_dir():
    base = get_user_data_dir()
    logs = os.path.join(base, 'logs')
    os.makedirs(logs, exist_ok=True)
    return logs

def get_cache_dir():
    base = get_user_data_dir()
    cache = os.path.join(base, 'cache')
    os.makedirs(cache, exist_ok=True)
    return cache

class SQLgate:
    def __init__(self):
        self.base_dir = get_user_data_dir()  # DB 파일(duckdb) 경로
        # self.company_data_dir = get_company_data_dir()  # 회사 데이터 파일 경로
        # self.KEY = load_key()
        # self.plugin = PluginController(self.company_data_dir, self.KEY)
        self.con = duckdb.connect()
        self.last_result = None
        self.mode = "file"  # 'file' 또는 'memory' 모드로 책임 분리
        # self.setup_database()

    def log(self, msg):  # 더미. 실제 로그는 UI에서 덮어씀
        print(msg)

    def refresh_table_list(self):
        try:
            # DB 타입 판별
            if 'duckdb' in str(type(self.con)).lower():
                # 1. information_schema.tables 시도
                try:
                    df = self.con.execute(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchdf()
                    if not df.empty:
                        return df['table_name'].tolist()
                except Exception:
                    pass
                # 2. PRAGMA show_tables 시도 (DuckDB)
                try:
                    tables = [row[0] for row in self.con.execute("PRAGMA show_tables").fetchall()]
                    if tables:
                        return tables
                except Exception:
                    pass
                return []
            elif 'sqlite' in str(type(self.con)).lower():
                cur = self.con.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                return [row[0] for row in cur.fetchall()]
            else:
                return []
        except Exception as e:
            self.log(lang.MSG_TABLE_LIST_LOAD_FAIL.format(error=e))
            return []
        
    def get_table_names(self):
        return self.refresh_table_list()

    def get_fields(self, db_name=None, table=None):
        current = self.get_current_db_name()
        # db_name이 None이거나 현재 연결된 DB와 같거나 :memory:면 테이블 반환
        if db_name and db_name != current and db_name != ":memory:":
            return []  # 현재 연결된 DB와 다르면 무시

        if not table:
            return self.refresh_table_list()

        try:
            if 'duckdb' in str(type(self.con)).lower():
                df = self.con.execute(f"PRAGMA table_info('{table}')").fetchdf()
                return [(row['name'], row['type']) for _, row in df.iterrows()]
            elif 'sqlite' in str(type(self.con)).lower():
                cur = self.con.cursor()
                cur.execute(f"PRAGMA table_info('{table}')")
                return [(row[1], row[2]) for row in cur.fetchall()]  # (name, type)
            else:
                return []
        except Exception as e:
            self.log(lang.MSG_FIELD_LIST_LOAD_FAIL.format(error=e))
            return []

    def get_all_column_names(self):
        columns = set()
        for table in self.get_table_names():
            try:
                if 'duckdb' in str(type(self.con)).lower():
                    df = self.con.execute(f"PRAGMA table_info('{table}')").fetchdf()
                    columns.update(df['name'].tolist())
                elif 'sqlite' in str(type(self.con)).lower():
                    cur = self.con.cursor()
                    cur.execute(f"PRAGMA table_info('{table}')")
                    columns.update([row[1] for row in cur.fetchall()])  # row[1] = name
            except Exception as e:
                self.log(lang.MSG_COLUMN_EXTRACT_FAIL.format(table=table, error=e))
        return list(columns)
    
    def setup_database(self):
        # 회사 전용 파일 로딩/병합/해석은 플러그인 컨트롤러에 위임
        dataframes = self.plugin.load_company_data()
        for name, df in dataframes.items():
            if df is not None:
                self.con.register(name, df)

    def get_current_db_name(self):
        try:
            path = self.con.execute("PRAGMA database_list").fetchone()[2]
            return os.path.basename(path) if path else ":memory:"
        except Exception as e:
            self.log(f"[WARN] DB 이름 가져오기 실패 → {e}")
            return ":memory:"

    def get_db_list(self):
        # RSU 원칙: 모드에 따라 DB 소스 분리
        if getattr(self, 'mode', 'file') == 'memory':
            return [":memory:"]
        db_dir = get_user_data_dir()  # OrrerySQL 폴더
        db_files = []
        for fname in os.listdir(db_dir):
            if fname.endswith(('.duckdb', '.sqlite', '.db', '.sqlite3')):
                db_files.append(fname)
        return [":memory:"] + db_files

    def switch_database(self, filename, dbtype='duckdb'):
        try:
            self.mode = 'file'  # DB 파일 전환 시 파일 모드로 복귀
            if filename == ":memory:":
                if self.con:
                    self.con.close()
                self.con = duckdb.connect(database=':memory:')
                self.log(lang.MSG_RAW_DB_CONNECTED)
                return
            db_path = os.path.join(self.base_dir, filename)
            if self.con:
                self.con.close()
            if dbtype == 'duckdb':
                self.con = duckdb.connect(db_path)
                self.log(lang.MSG_DUCKDB_CONNECTED.format(path=db_path))
            elif dbtype == 'sqlite':
                import sqlite3
                self.con = sqlite3.connect(db_path)
                self.log(lang.MSG_SQLITE_CONNECTED.format(path=db_path))
        except Exception as e:
            raise

    def execute_query(self, query):
        start = time.time()  # ⏱️ 시작 시간 기록
        try:
            if 'duckdb' in str(type(self.con)).lower():
                result = self.con.execute(query).fetchdf()
            elif 'sqlite' in str(type(self.con)).lower():
                import pandas as pd
                cur = self.con.cursor()
                cur.execute(query)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                result = pd.DataFrame(rows, columns=columns)
            else:
                result = None
        except Exception as e:
            self.log(f"[SQL ERROR] {e}")
            result = None
        elapsed = time.time() - start  # ⏱️ 경과 시간
        self.last_result = result
        self.log(f"[QUERY] {query}")
        if result is not None:
            self.log(f"[SUCCESS]: result shape={getattr(result, 'shape', None)}, {elapsed:.3f}s")
        return result


    def export_to_excel(self, df, path):
        df.to_excel(path, index=False)

    def create_db(self, path):
        if self.con:
            self.con.close()
        self.con = duckdb.connect(path)
        self.log(f"[INFO] 새 DB 파일 생성 및 연결: {path}")

    def open_db(self, path):
        if self.con:
            self.con.close()
        self.con = duckdb.connect(path)
        self.log(f"[INFO] DB 파일 연결: {path}")

    def switch_to_raw_world(self):
        if self.con:
            self.con.close()
        self.con = duckdb.connect(database=':memory:')
        self.log("[INFO] 원시 world(파일 기반)로 이동: 임시 DB 연결됨")
        self.setup_database()

