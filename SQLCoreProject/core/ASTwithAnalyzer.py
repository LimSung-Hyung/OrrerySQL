from SQLCoreProject.utils.sql_constants import SQL_FUNCTIONS
from SQLCoreProject.utils.walker_core import ConditionFormatter
from SQLCoreProject.core.AST_each_CTE import analyze_each_cte
from language.lang import lang

def extract_with_blocks(ast):
    if not isinstance(ast, dict):
        return {}

    with_section = ast.get("args", {}).get("with", {}).get("args", {})
    expressions = with_section.get("expressions", [])

    result = {}
    for expr in expressions:
        try:
            alias = expr.get("args", {}).get("alias", {}).get("args", {}).get("this", {}).get("args", {}).get("this", lang.MSG_CTE)
            cte_select = expr.get("args", {}).get("this", {})

            lines = analyze_each_cte(cte_select)
            if not isinstance(lines, list):
                raise ValueError(lang.MSG_ERROR_NOT_LIST)

            # 헤더(CTE 정의)에 step_num, 내부에 1,2,3... 숫자
            pretty = [f"[WITH {alias} {lang.MSG_DEF}]"]
            for idx, line in enumerate(lines, 1):
                pretty.append(f"   {idx}. {line}")
            result[alias] = pretty
        except Exception as e:
            result[alias] = [lang.MSG_ERROR_PARSE.format(target=alias) + f": {e}"]

    return result



