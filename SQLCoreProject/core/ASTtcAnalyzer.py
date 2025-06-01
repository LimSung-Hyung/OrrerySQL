from SQLCoreProject.utils.sql_constants import SQL_FUNCTIONS
from SQLCoreProject.utils.walker_core import ConditionFormatter
from language.lang import lang

class SQLTCAnalyzer:
    def __init__(self, ast_dict):
        self.ast = ast_dict
        self.tables = set()          # 메인 SELECT의 테이블만!
        self.cte_tables = {}         # CTE명 → set(테이블)
        self.aliases = {}
        self.columns = []
        self.functions = []
        self.conditions = []

        self._current_cte = None     # 현재 CTE명 (in_cte일 때만)
        self._in_with_block = False  # WITH 루트인지 여부 (for reset)
        self._traverse(self.ast, in_where=False, in_cte=False)

    def _traverse(self, node, in_where=False, in_cte=False):
        if isinstance(node, dict):
            self._traverse_dict(node, in_where=in_where, in_cte=in_cte)
        elif isinstance(node, list):
            for item in node:
                self._traverse(item, in_where=in_where, in_cte=in_cte)

    def _traverse_dict(self, node, in_where=False, in_cte=False):
        cls = node.get("class", "")

        # WITH 블록 진입: in_cte True
        if cls == "With":
            self._in_with_block = True
            in_cte = True

        # CTE 정의 노드 진입: CTE명 추출
        if cls == "CTE":
            in_cte = True
            alias = node.get("args", {}).get("alias", {}).get("args", {}).get("this", {}).get("args", {}).get("this")
            if alias:
                self._current_cte = alias
                if alias not in self.cte_tables:
                    self.cte_tables[alias] = set()
        # WITH/CTE 밖이면 해제
        if not in_cte:
            self._current_cte = None

        # WHERE(CTE 외부)
        if cls == "Where" and not in_cte:
            in_where = True
            cond = ConditionFormatter()
            target = node.get("args", {}).get("this")
            if target is None:
                target = node.get("args", {})
            if isinstance(target, list):
                for item in target:
                    cond.format(item)
            elif isinstance(target, dict):
                cond.format(target)
            self.conditions.extend(cond.result)

        # 테이블 추출: CTE별 or 메인
        if cls == "Table":
            self._extract_table(node, in_cte)

        elif cls == "Column":
            self._extract_column(node)

        if cls and cls.upper() in SQL_FUNCTIONS:
            self._extract_function(cls)

        # 내부 순회
        for key, val in node.items():
            if key == "args":
                self._traverse(val, in_where=in_where, in_cte=in_cte)
                break
        else:
            for val in node.values():
                self._traverse(val, in_where=in_where, in_cte=in_cte)

        # WITH 루트 해제(한 바퀴 끝나면)
        if cls == "With":
            self._in_with_block = False

    def _extract_table(self, node, in_cte):
        args = node.get("args", {})
        table = args.get("this", {}).get("args", {}).get("this")
        alias = args.get("alias", {}).get("args", {}).get("this", {}).get("args", {}).get("this")
        if table:
            if in_cte and self._current_cte:
                self.cte_tables[self._current_cte].add(table)
            elif not in_cte and not self._in_with_block:
                self.tables.add(table)
            if alias:
                self.aliases[table] = alias

    def _extract_column(self, node):
        args = node.get("args", {})
        this = args.get("this", {})
        left = this.get("args", {}).get("this")
        right = this.get("args", {}).get("expression")
        if isinstance(left, dict):
            left_val = left.get("args", {}).get("this")
        else:
            left_val = left
        if isinstance(right, dict):
            right_val = right.get("args", {}).get("this")
        else:
            right_val = right

        col = f"{left_val}.{right_val}" if left_val and right_val else left_val or right_val
        if col and col not in self.columns:
            self.columns.append(col)

    def _extract_function(self, func_name):
        upper = func_name.upper()
        if upper not in self.functions:
            self.functions.append(upper)

    def summary(self):
        return {
            "tables": list(self.tables),                       # 메인 SELECT 테이블만
            "cte_tables": {k: list(v) for k, v in self.cte_tables.items()},
            "aliases": self.aliases,
            "columns": self.columns,
            "functions": self.functions,
            "conditions": self.conditions
        }
