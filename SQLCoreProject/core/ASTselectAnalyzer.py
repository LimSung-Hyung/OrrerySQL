from language.lang import lang

def extract_select_fields(ast):
    """
    SELECT 절 내 표현식들을 해석하여 사람이 읽을 수 있는 형태로 반환
    ex: ["name", "salary * 2 AS double_salary", "COUNT(*) AS cnt"]
    """
    if not isinstance(ast, dict):
        return []

    results = []
    expressions = ast.get("args", {}).get("expressions", [])

    for expr in expressions:
        if not isinstance(expr, dict):
            continue

        cls = expr.get("class", "")
        args = expr.get("args", {})

        # SELECT name AS alias
        if cls == "Alias":
            alias_val = args.get("alias", {})
            if isinstance(alias_val, dict):
                alias = alias_val.get("args", {}).get("this", "alias")
            else:
                alias = str(alias_val)
            inner = args.get("this", {})
            inner_str = _describe_expression(inner)
            results.append(f"{inner_str} AS {alias}")

        # SELECT name
        else:
            expr_str = _describe_expression(expr)
            results.append(expr_str)

    return results


def _describe_expression(expr):
    """
    표현식 객체 하나를 문자열로 설명
    ex: Column(name), Function(SUM), Binary(MUL), Literal 등
    """
    if not isinstance(expr, dict):
        # dict가 아니면(str 등) 바로 반환
        return str(expr)
    cls = expr.get("class", "")
    args = expr.get("args", {})

    if cls == "Column":
        # 여기서 table까지 추적!
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
    elif cls in {"Literal", "Identifier"}:
        # args가 dict가 아닐 수 있으니 방어
        if isinstance(args, dict):
            this_val = args.get("this", {})
            if isinstance(this_val, dict):
                inner_args = this_val.get("args", {})
                if isinstance(inner_args, dict):
                    return inner_args.get("this", lang.MSG_VAL)
                else:
                    return str(inner_args)
            else:
                return str(this_val)
        else:
            return str(args)
    elif cls in {"Add", "Sub", "Mul", "Div"}:
        left = _describe_expression(args.get("this", {}) if isinstance(args, dict) else {})
        right = _describe_expression(args.get("expression", {}) if isinstance(args, dict) else {})
        op = {"Add": "+", "Sub": "-", "Mul": "*", "Div": "/"}.get(cls, "?")
        return f"({left} {op} {right})"
    elif cls in {"Count", "Sum", "Avg", "Max", "Min"}:
        inner = _describe_expression(args.get("this", {}) if isinstance(args, dict) else {})
        return f"{cls.upper()}({inner})"
    elif cls == "Star":
        return "*"
    else:
        return lang.MSG_CALC
