class SQLPatterns:
    def __init__(self):
        self.tables = []
        self.columns = []

    def set_patterns(self, tables, columns):
        self.tables = tables or []
        self.columns = columns or []

    def get_tables(self):
        return self.tables

    def get_columns(self):
        return self.columns

sql_patterns = SQLPatterns() 