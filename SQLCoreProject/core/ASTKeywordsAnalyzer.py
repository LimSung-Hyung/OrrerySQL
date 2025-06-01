# ASTKeywordsAnalyzer.py

from SQLCoreProject.utils.sql_constants import SQL_FUNCTIONS
from language.lang import lang

def extract_clause_description(keyword, node):
    """
    키워드 종류와 해당 AST 노드를 받아서 설명을 문자열로 반환
    """
    try:
        if keyword == "WHERE" or keyword == "HAVING":
            return _extract_condition_description(node)
        elif keyword == "GROUP":
            group_args = node.get("args", {})
            exprs = group_args.get("expressions")
            group_cols = []
            if isinstance(exprs, list) and len(exprs) > 0:
                for expr in exprs:
                    col_node = expr.get("args", {}).get("this", {})
                    alias = expr.get("args", {}).get("alias")
                    col_name = _parse_column_ref(col_node)
                    alias_str = ""
                    if alias:
                        alias_val = alias.get("args", {}).get("this") if isinstance(alias, dict) else alias
                        if alias_val:
                            alias_str = f" (별칭: {alias_val})"
                    if col_name:
                        group_cols.append(f"{col_name}{alias_str}")
                if group_cols:
                    return lang.MSG_GROUP_BY_FULL_FORMAT.format(col=", ".join(group_cols), alias="")
                else:
                    return ""  # 컬럼명 없으면 무시
            elif "this" in group_args:
                col_node = group_args["this"]
                alias = group_args.get("alias")
                col_name = _parse_column_ref(col_node)
                alias_str = ""
                if alias:
                    alias_val = alias.get("args", {}).get("this") if isinstance(alias, dict) else alias
                    if alias_val:
                        alias_str = f" (별칭: {alias_val})"
                if col_name:
                    return lang.MSG_GROUP_BY_FULL_FORMAT.format(col=f"{col_name}{alias_str}", alias="")
                else:
                    return ""
            else:
                return ""
        elif keyword == "ORDERED":
            return _extract_order_by(node)
        elif keyword == "LIMIT":
            return _extract_limit(node)
        else:
            return f"{keyword} {lang.MSG_CLAUSE_USED}"
    except Exception:
        return f"{keyword} {lang.MSG_ERROR_PARSE.format(target=keyword)}"

def _extract_condition_description(node):
    cls = node.get("class", "")
    if cls in {"AND", "OR"}:
        return f"{cls} {lang.MSG_CONDITION_USE} {lang.MSG_CONDITION_LINK}"
    elif cls == "EQ":
        return lang.MSG_EQ_CONDITION
    elif cls == "LIKE":
        return lang.MSG_LIKE_CONDITION
    elif cls == "IN":
        return lang.MSG_IN_CONDITION
    elif cls == "BETWEEN":
        return lang.MSG_BETWEEN_CONDITION
    elif cls == "NOT":
        return lang.MSG_NOT_CONDITION
    else:
        return f"{cls.upper()} {lang.MSG_CONDITION_USE}"

def _parse_column_ref(col_node):
    """
    robust하게 table/alias와 column을 모두 추출 (ex: p.product_id),
    Column 타입이 아닐 경우 값만 반환
    """
    if not isinstance(col_node, dict):
        return str(col_node)
    cls = col_node.get("class", "")
    args = col_node.get("args", {})
    if cls == "Column":
        table = args.get("table")
        if isinstance(table, dict):
            table = table.get("args", {}).get("this", None)
        elif isinstance(table, str):
            pass
        else:
            table = None
        col = args.get("this")
        if isinstance(col, dict):
            col = col.get("args", {}).get("this", None)
        elif isinstance(col, str):
            pass
        else:
            col = str(col)
        if table:
            return f"{table}.{col}"
        else:
            return f"{col}"
    elif cls == "Identifier":
        val = args.get("this")
        if isinstance(val, str):
            return val
        elif isinstance(val, dict):
            return val.get("args", {}).get("this", str(val))
        return str(val)
    elif cls == "Literal":
        val = args.get("this")
        if isinstance(val, str):
            return val
        elif isinstance(val, dict):
            return val.get("args", {}).get("this", str(val))
        return str(val)
    else:
        return str(col_node)

def _extract_group_by(node):
    expr = node.get("args", {}).get("expressions", [{}])[0]
    col_node = expr.get("args", {}).get("this", {})
    alias = expr.get("args", {}).get("alias")
    alias_str = ""
    col_name = _parse_column_ref(col_node)
    if alias:
        alias_val = alias.get("args", {}).get("this") if isinstance(alias, dict) else alias
        if alias_val:
            alias_str = f" (별칭: {alias_val})"
    return lang.MSG_GROUP_BY_FULL_FORMAT.format(col=col_name, alias=alias_str)

def _extract_order_by(node):
    base = node.get("args", {}).get("this", {}).get("args", {})
    col = base.get("this", {}).get("args", {}).get("this", lang.MSG_COL)
    direction = lang.MSG_ASC if not node.get("args", {}).get("desc") else lang.MSG_DESC
    return f"{lang.MSG_ORDER_BY} {col} {direction} {lang.MSG_SORT}"

def _extract_limit(node):
    val = node.get("args", {}).get("expression", {}).get("args", {}).get("this", lang.MSG_VAL)
    return f"{lang.MSG_LIMIT} {val}{lang.MSG_LIMIT_UNIT}"
