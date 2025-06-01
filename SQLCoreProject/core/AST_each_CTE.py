from SQLCoreProject.core.CTEselect import analyze_cte_select_fields
from SQLCoreProject.core.CTEjoin import analyze_cte_joins
from SQLCoreProject.core.CTEkeywords import analyze_cte_clauses
from SQLCoreProject.core.CTEconditions import CTEConditionWalker
from language.lang import lang

def multiline_list(label, items, tail=""):
    if not isinstance(items, list):
        return f"{label} [{items}]{tail}"
    if len(items) > 3:
        item_lines = ",\n    ".join(str(i) for i in items)
        return f"{label} [\n    {item_lines}\n]{tail}"
    else:
        return f"{label} [{', '.join(str(i) for i in items)}]{tail}"

def extract_from_tables(ast):
    tables = []
    from_node = ast.get("args", {}).get("from", {}).get("args", {})
    if "expressions" in from_node:
        for tbl in from_node["expressions"]:
            tbl_name = None
            if isinstance(tbl, dict):
                tbl_name = tbl.get("args", {}).get("this")
                if isinstance(tbl_name, dict):
                    tbl_name = tbl_name.get("args", {}).get("this")
                if tbl_name:
                    tables.append(tbl_name)
    elif "this" in from_node:
        tbl = from_node["this"]
        tbl_name = None
        if isinstance(tbl, dict):
            tbl_name = tbl.get("args", {}).get("this")
            if isinstance(tbl_name, dict):
                tbl_name = tbl_name.get("args", {}).get("this")
            if tbl_name:
                tables.append(tbl_name)
    return tables

def extract_group_by(ast):
    group_cols = []
    groupby_node = ast.get("args", {}).get("group", {}).get("args", {})
    exprs = groupby_node.get("expressions")
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
                group_cols.append(col_name)
    elif "this" in groupby_node:
        col = groupby_node["this"]
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
            group_cols.append(col_name)
    return group_cols

def analyze_each_cte(ast):
    if not isinstance(ast, dict):
        return [lang.MSG_INVALID_AST]

    steps = []

    # FROM 해석
    try:
        from_tables = extract_from_tables(ast)
        if from_tables:
            steps.append(multiline_list(lang.MSG_FROM, from_tables, f" {lang.MSG_TABLE_SELECT}"))
    except Exception:
        steps.append(lang.MSG_ERROR_PARSE.format(target="FROM"))

    # JOIN 해석
    try:
        join_desc = analyze_cte_joins(ast)
        if join_desc:
            steps.append(join_desc)
    except Exception:
        steps.append(lang.MSG_ERROR_PARSE.format(target="JOIN"))

    # WHERE/조건/함수 해석
    try:
        walker = CTEConditionWalker()
        cond_func_descs = walker.analyze(ast)
        steps.extend(cond_func_descs)
    except Exception:
        steps.append(lang.MSG_ERROR_PARSE.format(target="조건/함수"))

    # GROUP BY 해석
    try:
        group_cols = extract_group_by(ast)
        if group_cols:
            group_by_str = lang.MSG_GROUP_BY_FULL_FORMAT.format(col=", ".join(group_cols), alias="")
            steps.append(group_by_str)
    except Exception:
        steps.append(lang.MSG_ERROR_PARSE.format(target="GROUP BY"))

    # SELECT 해석
    try:
        select_fields = analyze_cte_select_fields(ast)
        if select_fields:
            steps.append(multiline_list(lang.MSG_FROM.replace("FROM", "SELECT"), select_fields, f" {lang.MSG_COLUMN_SELECT}"))
    except Exception:
        steps.append(lang.MSG_ERROR_PARSE.format(target="SELECT"))

    return steps if steps else [lang.MSG_NONE]
