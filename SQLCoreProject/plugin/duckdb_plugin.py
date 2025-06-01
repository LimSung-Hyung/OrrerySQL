class DuckDBPlugin:
    def __init__(self):
        self.conn = None
    def connect(self, file_path):
        import duckdb
        self.conn = duckdb.connect(file_path)
        # 추가: 테이블 목록, 쿼리 등 메서드 구현 가능 