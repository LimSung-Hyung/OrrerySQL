# ASTJoinAnalyzer.py

from language.lang import lang

def extract_join_detail(node):
    """
    JOIN 절 AST 노드를 해석하여 사람 친화적인 설명을 반환
    ex: "p.id = m.id 로 LEFT JOIN 수행"
    """
    try:
        join_type = node.get("args", {}).get("side", "").upper() or "INNER"
        on_clause = node.get("args", {}).get("on", {})

        if on_clause.get("class") == "EQ":
            left_expr = _parse_column_ref(on_clause.get("args", {}).get("this", {}))
            right_expr = _parse_column_ref(on_clause.get("args", {}).get("expression", {}))
            return f"{left_expr} = {right_expr} {lang.MSG_JOIN_TYPE.format(join_type=join_type)}"

        return f"{join_type} {lang.MSG_JOIN_USED}"
    except Exception:
        return lang.MSG_JOIN_USED


def _parse_column_ref(col_node):
    """
    컬럼 참조 노드를 문자열로 파싱: ex) table.column
    """
    if not isinstance(col_node, dict):
        return lang.MSG_UNKNOWN

    try:
        table = col_node.get("args", {}).get("table", {}).get("args", {}).get("this", lang.MSG_UNKNOWN)
        column = col_node.get("args", {}).get("this", {}).get("args", {}).get("this", lang.MSG_UNKNOWN)
        return f"{table}.{column}"
    except Exception:
        return lang.MSG_UNKNOWN
