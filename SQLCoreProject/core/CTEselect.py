# CTEselect.py

from language.lang import lang

def analyze_cte_select_fields(ast):
    """
    CTE 내부 SELECT 절의 필드 해석: alias, 계산식, 컬럼명
    ex: ["name", "salary * 2 AS double_salary"]
    """
    if not isinstance(ast, dict):
        return lang.MSG_CALC

    results = []
    expressions = ast.get("args", {}).get("expressions", [])

    for expr in expressions:
        if not isinstance(expr, dict):
            continue

        cls = expr.get("class", "")
        args = expr.get("args", {})

        if cls == "Alias":
            alias = args.get("alias", {}).get("args", {}).get("this", "alias")
            inner = args.get("this", {})
            inner_str = _describe_expression(inner)
            results.append(f"{inner_str} AS {alias}")
        else:
            expr_str = _describe_expression(expr)
            results.append(expr_str)

    return results


def _describe_expression(expr):
    cls = expr.get("class", "")
    args = expr.get("args", {})

    if cls == "Column":
        return args.get("this", {}).get("args", {}).get("this", lang.MSG_COL)
    elif cls in {"Literal", "Identifier"}:
        return args.get("this", {}).get("args", {}).get("this", lang.MSG_VAL)
    elif cls in {"Add", "Sub", "Mul", "Div"}:
        left = _describe_expression(args.get("this", {}))
        right = _describe_expression(args.get("expression", {}))
        op = {"Add": "+", "Sub": "-", "Mul": "*", "Div": "/"}.get(cls, "?")
        return f"({left} {op} {right})"
    elif cls in {"Count", "Sum", "Avg", "Max", "Min"}:
        inner = _describe_expression(args.get("this", {}))
        return f"{cls.upper()}({inner})"
    elif cls == "Star":
        return "*"
    else:
        return lang.MSG_CALC

def _describe_value(args):
    if isinstance(args, dict):
        return args.get("this", {}).get("args", {}).get("this", lang.MSG_NONE)
    return lang.MSG_NONE
