from SQLCoreProject.utils.sql_constants import SQL_FUNCTIONS
from SQLCoreProject.core.ASTaggregation import parse_aggregation, CASE_KEYWORD
from language.lang import lang

class ConditionFormatter:
    def __init__(self):
        self.conditions = []

    def format(self, node, depth=0):
        for cond in self._flatten_logic(node):
            self.conditions.append(self._indent(depth) + cond)

    def _flatten_logic(self, node):
        if not isinstance(node, dict):
            return []

        cls = node.get("class", "").upper()

        if cls == "AND":
            left = node.get("args", {}).get("this", {})
            right = node.get("args", {}).get("expression", {})
            return self._flatten_logic(left) + self._flatten_logic(right)

        elif cls == "OR":
            left = node.get("args", {}).get("this", {})
            right = node.get("args", {}).get("expression", {})
            left_strs = self._flatten_logic(left)
            right_strs = self._flatten_logic(right)
            conds = left_strs + right_strs
            or_expr = " OR ".join(c.replace(lang.MSG_CONDITION_USE, "") for c in conds)
            return [f"({or_expr}) {lang.MSG_CONDITION_USE}"]

        elif cls == "PAREN":
            inner = node.get("args", {}).get("this", {})
            conds = self._flatten_logic(inner)
            if not conds or all("?" in c for c in conds):
                if isinstance(inner, dict):
                    inner_cls = inner.get("class", "").upper()
                    if inner_cls in {"IS", "EQ", "NEQ", "LIKE", "IN", "BETWEEN", "GT", "LT", "GTE", "LTE"}:
                        return [self._format_condition(inner_cls, inner) + f" {lang.MSG_CONDITION_USE}"]
            return conds if conds else ["() " + lang.MSG_CONDITION_USE]

        elif cls in {"EQ", "LIKE", "IN", "BETWEEN", "NOT", "IS", "GT", "LT", "GTE", "LTE", "NEQ"}:
            return [self._format_condition(cls, node) + f" {lang.MSG_CONDITION_USE}"]

        else:
            return []

    def _format_condition(self, cls, node):
        try:
            args = node.get("args", {})
            if isinstance(args, dict):
                left = args.get("this", {})
                right = args.get("expression", {})
            elif isinstance(args, list) and len(args) == 2:
                left, right = args
            else:
                return f"{cls} {lang.MSG_CONDITION_USE}"

            if cls == "NOT":
                cond_node = left
                if isinstance(cond_node, dict):
                    cond_cls = cond_node.get("class", "").upper()
                    if cond_cls in {"IS", "EQ", "NEQ", "LIKE", "IN", "BETWEEN", "GT", "LT", "GTE", "LTE"}:
                        inner = self._format_condition(cond_cls, cond_node)
                        return f"NOT ({inner})"
                    elif cond_cls == "PAREN":
                        inner = cond_node.get("args", {}).get("this", {})
                        inner_cond_list = self._flatten_logic(inner)
                        if not inner_cond_list or all("?" in c for c in inner_cond_list):
                            if isinstance(inner, dict):
                                inner_cls = inner.get("class", "").upper()
                                if inner_cls in {"IS", "EQ", "NEQ", "LIKE", "IN", "BETWEEN", "GT", "LT", "GTE", "LTE"}:
                                    inner_expr = self._format_condition(inner_cls, inner)
                                    return f"NOT ({inner_expr})"
                        if inner_cond_list:
                            inner_expr = " AND ".join([c.replace(lang.MSG_CONDITION_USE, "") for c in inner_cond_list])
                            return f"NOT ({inner_expr})"
                        else:
                            return "NOT ()"
                    elif cond_cls == "EXISTS":
                        return "NOT EXISTS"
                    else:
                        inner_cond_list = self._flatten_logic(cond_node)
                        if inner_cond_list:
                            expr = " AND ".join([c.replace(lang.MSG_CONDITION_USE, "") for c in inner_cond_list])
                            return f"NOT ({expr})"
                        else:
                            expr = self._pretty_expr(cond_node)
                            return f"NOT ({expr})"
                else:
                    right_val = self._pretty_expr(cond_node)
                    return f"NOT ({right_val})"
            else:
                left_col = self._pretty_expr(left)
                right_val = self._pretty_expr(right)
                return f"{left_col} {self._symbol(cls)} {right_val}"
        except Exception as e:
            return f"{cls} {lang.MSG_ERROR_PARSE.format(target=cls)}: {e}"

    def _pretty_expr(self, node):
        if not isinstance(node, dict):
            if node is None:
                return ""
            if isinstance(node, str):
                return node
            return repr(node)
        cls = node.get("class", "")
        cls_upper = cls.upper()

        # 🟡 집계함수/CASE면 계층 설명으로 반환
        if cls_upper in SQL_FUNCTIONS or cls_upper == CASE_KEYWORD:
            lines = parse_aggregation(node)
            return "\n".join(lines)

        if cls_upper in SQL_FUNCTIONS:
            fn = cls_upper
            args = node.get("args", {})
            if "this" in args:
                arg_val = self._pretty_expr(args["this"])
                return f"{fn}({arg_val})"
            elif "expressions" in args:
                exprs = args["expressions"]
                if isinstance(exprs, list):
                    arg_val = ", ".join(self._pretty_expr(e) for e in exprs)
                else:
                    arg_val = self._pretty_expr(exprs)
                return f"{fn}({arg_val})"
            else:
                arg_val = ', '.join([self._pretty_expr(v) for v in args.values()]) if args else ""
                return f"{fn}({arg_val})"

        if cls == "Column":
            col_args = node.get("args", {})
            table = col_args.get("table")
            col_this = col_args.get("this")
            col_name = None
            table_name = None
            if isinstance(table, dict) and table.get("class") == "Identifier":
                table_name = table.get("args", {}).get("this", None)
            if isinstance(col_this, dict) and col_this.get("class") == "Identifier":
                col_name = col_this.get("args", {}).get("this", None)
            elif isinstance(col_this, str):
                col_name = col_this
            if table_name and col_name:
                return f"{table_name}.{col_name}"
            elif col_name:
                return f"{col_name}"
            else:
                return "?"

        if cls == "Literal":
            val = node.get("args", {}).get("this")
            return f"'{val}'" if isinstance(val, str) else str(val) if val is not None else "''"
        if cls == "Identifier":
            return node.get("args", {}).get("this", "?")
        if cls_upper == "NULL":
            return "NULL"
        if cls_upper == "TRUE":
            return "TRUE"
        if cls_upper == "FALSE":
            return "FALSE"
        if cls_upper in {"TUPLE", "LIST"}:
            exprs = node.get("args", {}).get("expressions", [])
            return "(" + ", ".join(self._pretty_expr(e) for e in exprs) + ")"
        if not cls and "args" in node:
            for v in node["args"].values():
                s = self._pretty_expr(v)
                if s and s != "?":
                    return s
            return "?"
        return "?"

    def _symbol(self, cls):
        return {
            "EQ": "=", "GT": ">", "GTE": ">=",
            "LT": "<", "LTE": "<=",
            "IS": "IS", "LIKE": "LIKE",
            "IN": "IN", "BETWEEN": "BETWEEN", "NOT": "NOT", "NEQ": "<>"
        }.get(cls, cls)

    def _indent(self, depth):
        return "↳ " + "↳ " * depth

    @property
    def result(self):
        return self.conditions
