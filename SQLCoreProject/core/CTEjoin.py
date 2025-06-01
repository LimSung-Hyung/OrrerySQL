# CTEjoin.py

from language.lang import lang

def analyze_cte_joins(ast):
    """
    CTE 내부 JOIN 절 해석.
    ex: "emp.id = dept.emp_id 로 LEFT JOIN 수행"
    """
    joins = _extract_joins(ast)
    if not joins:
        return ""

    results = []
    for join_node in joins:
        desc = _parse_join(join_node)
        results.append(desc)

    return " / ".join(results)


def _extract_joins(node):
    """
    AST 내 JOIN 블록들을 모두 찾아 리스트로 반환
    """
    result = []
    if isinstance(node, dict):
        if node.get("class") == "Join":
            result.append(node)
        for val in node.values():
            result.extend(_extract_joins(val))
    elif isinstance(node, list):
        for item in node:
            result.extend(_extract_joins(item))
    return result


def _parse_join(node):
    """
    JOIN 노드에서 JOIN TYPE과 ON 조건 파싱
    """
    try:
        join_type = node.get("args", {}).get("side", "").upper() or "INNER"
        on_clause = node.get("args", {}).get("on", {})

        if on_clause.get("class") == "EQ":
            left = _col_ref(on_clause.get("args", {}).get("this", {}))
            right = _col_ref(on_clause.get("args", {}).get("expression", {}))
            return _describe_join(left, right, join_type)
        return lang.MSG_ERROR_PARSE.format(target="JOIN")
    except Exception:
        return _describe_join_fail()


def _col_ref(col_node):
    if not isinstance(col_node, dict):
        return "UNKNOWN"
    try:
        table = col_node.get("args", {}).get("table", {}).get("args", {}).get("this", "❓")
        col = col_node.get("args", {}).get("this", {}).get("args", {}).get("this", "❓")
        return f"{table}.{col}"
    except Exception:
        return "UNKNOWN"


def _describe_join(left, right, join_type):
    return f"{left} = {right} {lang.MSG_JOIN_TYPE} {join_type}"


def _describe_join_fail():
    return lang.MSG_ERROR_PARSE.format(target="JOIN")
