# CTEkeywords.py

from language.lang import lang

def analyze_cte_clauses(ast):
    """
    CTE 내부의 WHERE, GROUP, ORDER, LIMIT 등 절에 대한 요약 설명 리스트 반환
    """
    if not isinstance(ast, dict):
        return []

    used = []
    _extract_keywords(ast, used)

    results = []
    for kw, node in used:
        kw_upper = kw.upper()
        try:
            if kw_upper in {"WHERE", "HAVING"}:
                walker = CTEConditionWalker()
                walker.traverse(node.get("args", {}).get("this", {}))  # ✅ 핵심
                results.append(f"{kw_upper} {lang.MSG_CONDITION_USE} ↓")
                results.extend([f"↳ {c}" for c in walker.conditions])
            elif kw_upper == "GROUP":
                desc = _describe_group(node)
                if desc:   # 빈 문자열 아닐 때만 추가
                    results.append(desc)
            elif kw_upper == "ORDERED":
                results.append(_describe_order(node))
            elif kw_upper == "LIMIT":
                results.append(_describe_limit(node))
        except Exception:
            results.append(f"{lang.MSG_ERROR_PARSE.format(target=kw_upper)}")

    return results


def _extract_keywords(node, result):
    """
    AST 내에서 절 관련 키워드를 전부 수집
    """
    if isinstance(node, dict):
        cls = node.get("class", "")
        if cls:
            result.append((cls, node))
        for val in node.values():
            _extract_keywords(val, result)
    elif isinstance(node, list):
        for item in node:
            _extract_keywords(item, result)

def _describe_group(node):
    # expressions 리스트(복수 group by) 지원
    exprs = node.get("args", {}).get("expressions")
    target_cols = []
    if isinstance(exprs, list) and exprs:
        for expr in exprs:
            col = expr.get("args", {}).get("this", {})
            col_name = None
            if isinstance(col, dict):
                cls = col.get("class", "")
                args = col.get("args", {})
                if cls == "Column":
                    table = args.get("table")
                    if isinstance(table, dict):
                        table = table.get("args", {}).get("this", None)
                    elif isinstance(table, str):
                        pass
                    else:
                        table = None
                    c = args.get("this")
                    if isinstance(c, dict):
                        c = c.get("args", {}).get("this", None)
                    elif isinstance(c, str):
                        pass
                    else:
                        c = str(c)
                    if table:
                        col_name = f"{table}.{c}"
                    else:
                        col_name = f"{c}"
                elif cls == "Identifier":
                    val = args.get("this")
                    if isinstance(val, str):
                        col_name = val
                    elif isinstance(val, dict):
                        col_name = val.get("args", {}).get("this", str(val))
                    else:
                        col_name = str(val)
                else:
                    col_name = str(col)
            else:
                col_name = str(col)
            if col_name:
                if isinstance(col_name, str):
                    col_name = col_name.replace("기준", "").replace("[", "").replace("]", "").strip()
                target_cols.append(col_name)
    elif "this" in node.get("args", {}):
        # 단일 컬럼(group by col) 지원
        col = node["args"]["this"]
        col_name = None
        if isinstance(col, dict):
            cls = col.get("class", "")
            args = col.get("args", {})
            if cls == "Column":
                table = args.get("table")
                if isinstance(table, dict):
                    table = table.get("args", {}).get("this", None)
                elif isinstance(table, str):
                    pass
                else:
                    table = None
                c = args.get("this")
                if isinstance(c, dict):
                    c = c.get("args", {}).get("this", None)
                elif isinstance(c, str):
                    pass
                else:
                    c = str(c)
                if table:
                    col_name = f"{table}.{c}"
                else:
                    col_name = f"{c}"
            elif cls == "Identifier":
                val = args.get("this")
                if isinstance(val, str):
                    col_name = val
                elif isinstance(val, dict):
                    col_name = val.get("args", {}).get("this", str(val))
                else:
                    col_name = str(val)
            else:
                col_name = str(col)
        else:
            col_name = str(col)
        if col_name:
            if isinstance(col_name, str):
                col_name = col_name.replace("기준", "").replace("[", "").replace("]", "").strip()
            target_cols.append(col_name)
    # 최종 출력: "user_id 기준" or "user_id, order_date 기준"
    if target_cols:
        return lang.MSG_GROUP_BY_FULL_FORMAT.format(col=", ".join(target_cols), alias="")
    return ""

def _describe_order(node):
    base = node.get("args", {}).get("this", {}).get("args", {})
    col = base.get("this", {}).get("args", {}).get("this", lang.MSG_COLUMN)
    direction = lang.MSG_ASC if not node.get("args", {}).get("desc") else lang.MSG_DESC
    return f"ORDER BY {col} {direction} {lang.MSG_SORT}"


def _describe_limit(node):
    val = node.get("args", {}).get("expression", {}).get("args", {}).get("this", lang.MSG_VALUE)
    return f"LIMIT {val}{lang.MSG_LIMIT}"


class CTEConditionWalker:
    """
    CTE 내부의 WHERE/HAVING 절 내 논리 조건 분석기
    """
    def __init__(self):
        self.conditions = []

    def traverse(self, node):
        if isinstance(node, dict):
            cls = node.get("class", "")
            if cls in {"AND", "OR", "EQ", "LIKE", "IN", "BETWEEN", "NOT", "IS"}:
                self.conditions.append(
                    f"{cls} {lang.MSG_CONDITION_USE} {lang.MSG_CONDITION_LINK}" if cls in {"AND", "OR"} else f"{cls} {lang.MSG_CONDITION_USE}"
                )
            for val in node.values():
                self.traverse(val)
        elif isinstance(node, list):
            for item in node:
                self.traverse(item)
