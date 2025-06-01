import os
from SQLCoreProject.ui.SQLtabsheet import SQLTabSheet
from language.lang import lang

class SQLMultiBridge:
    def __init__(self, tab_sheet: SQLTabSheet, query_runner, sqlgate):
        """
        :param tab_sheet: SQLTabSheet 인스턴스 (멀티 콘솔 탭)
        :param query_runner: 쿼리 실행 함수 (sql: str) -> None
        :param sqlgate: SQLgate 인스턴스
        """
        self.tab_sheet = tab_sheet
        self.query_runner = query_runner
        self.sqlgate = sqlgate

    def run_current_query(self):
        """현재 탭의 쿼리만 실행"""
        query_input = self.tab_sheet.get_current_query_input()
        if query_input:
            sql = query_input.toPlainText().strip()
            if sql:
                self.query_runner(sql)

    def get_all_queries(self):
        """모든 탭의 쿼리 리스트 반환"""
        return [q.toPlainText().strip() for q in self.tab_sheet.query_inputs if q.toPlainText().strip()]

    def save_last_queries(self):
        """모든 탭의 마지막 쿼리를 저장 (파일 저장 연동용)"""
        queries = self.get_all_queries()
        path = os.path.join(self.sqlgate.base_dir, "last_queries.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                for query in queries:
                    f.write(query + "\n\n---\n\n")
        except Exception as e:
            print(f"{lang.MSG_SAVE_QUERY_FAIL} → {e}")
