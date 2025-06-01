# CTEconditions.py
from SQLCoreProject.utils.sql_constants import SQL_FUNCTIONS
from language.lang import lang

class CTEConditionWalker:
    def __init__(self):
        self.conditions = []
        self.functions = []

    def analyze(self, ast):
        self._traverse(ast)
        results = []
        if self.conditions:
            results.append("WHERE " + lang.MSG_CONDITION_USE + " ↓")
            for cond in self.conditions:
                results.append(f"↳ {cond} {lang.MSG_CONDITION_USE}")
        if self.functions:
            results.append(lang.MSG_FUNC_USED + " ↓")
            for fn in self.functions:
                results.append(f"↳ {fn}")
        return results

    def _traverse(self, node):
        if isinstance(node, dict):
            cls = node.get("class", "")
            if cls in {"EQ", "LIKE", "IS", "AND", "OR", "NOT", "GT", "LT", "GTE", "LTE", "IN", "BETWEEN"}:
                left = node.get("args", {}).get("this", {})
                right = node.get("args", {}).get("expression", {})
                left_val = self._extract_identifier(left)
                right_val = self._extract_literal(right)
                if left_val and right_val:
                    self.conditions.append(f"{cls}: {left_val} {self._symbol(cls)} {right_val}")
                else:
                    self.conditions.append(cls)

            if cls.upper() in SQL_FUNCTIONS:
                self.functions.append(cls.upper())

            for val in node.values():
                self._traverse(val)

        elif isinstance(node, list):
            for item in node:
                self._traverse(item)

    def _extract_identifier(self, node):
        if not isinstance(node, dict): return ""
        if node.get("class") == "Column":
            col = node.get("args", {}).get("this", {}).get("args", {}).get("this")
            return col
        return ""

    def _extract_literal(self, node):
        if not isinstance(node, dict): return ""
        if node.get("class") == "Literal":
            return f"'{node.get('args', {}).get('this', '')}'"
        return ""

    def _symbol(self, cls):
        return {
            "GT": ">", "LT": "<", "GTE": ">=", "LTE": "<=", "EQ": "=", "IS": "IS"
        }.get(cls, cls)
