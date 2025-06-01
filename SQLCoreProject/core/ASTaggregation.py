# ASTaggregation.py

from SQLCoreProject.utils.sql_constants import SQL_FUNCTIONS
from language.lang import lang
SQL_AGG_FUNCTIONS = ["SUM", "COUNT", "MAX", "MIN", "AVG"]
CASE_KEYWORD = "CASE"

def parse_aggregation(node, depth=0):
    """
    node: dict, AST에서 함수/CASE 노드
    depth: int, 계층 깊이 (출력용)
    return: list of str (계층적 해석 결과)
    """
    if not isinstance(node, dict):
        return []

    cls = node.get("class", "").upper()
    lines = []

    indent = "    " * depth
    arrow = "↳ " * depth

    # 집계함수(SUM, COUNT, MAX, MIN, AVG)
    if cls in SQL_FUNCTIONS:
        # 함수명
        lines.append(f"{arrow}{cls} 함수 사용 ↓")
        args = node.get("args", {})
        # 대표적으로 "this"가 인자, 또는 "expressions"
        target = args.get("this") or args.get("expression") or args.get("expressions")
        if isinstance(target, list):
            # 여러 인자(예: COUNT(DISTINCT a, b))
            for t in target:
                lines.extend(parse_aggregation(t, depth + 1))
        elif isinstance(target, dict):
            # 인자가 CASE, 또 함수면 재귀 파싱
            lines.extend(parse_aggregation(target, depth + 1))
        else:
            # 리터럴, 컬럼명 등
            lines.append(f"{arrow}    인자: {target}")
        return lines

    # CASE 함수
    if cls == CASE_KEYWORD:
        lines.append(f"{arrow}CASE 함수 사용 ↓")
        args = node.get("args", {})
        whens = args.get("ifs", []) or args.get("when", [])  # sqlglot 버전에 따라 다름
        else_expr = args.get("default") or args.get("else")
        # WHEN ... THEN ...
        for w in whens:
            # w는 dict이며, condition/true
            cond = w.get("cond") or w.get("condition")
            res = w.get("result") or w.get("true")
            # WHEN 조건
            when_strs = parse_aggregation(cond, depth + 2) if isinstance(cond, dict) else [str(cond)]
            then_strs = parse_aggregation(res, depth + 2) if isinstance(res, dict) else [str(res)]
            lines.append(f"{arrow}    WHEN ↓")
            for ws in when_strs:
                lines.append(f"{arrow}        조건: {ws}")
            lines.append(f"{arrow}    THEN ↓")
            for ts in then_strs:
                lines.append(f"{arrow}        반환: {ts}")
        # ELSE ...
        if else_expr is not None:
            else_strs = parse_aggregation(else_expr, depth + 2) if isinstance(else_expr, dict) else [str(else_expr)]
            lines.append(f"{arrow}    ELSE ↓")
            for es in else_strs:
                lines.append(f"{arrow}        반환: {es}")
        return lines

    # 그 외, 함수 안에 또 함수가 들어가는 경우
    if cls:
        # 알 수 없는 함수이거나, 단일 값/컬럼명/리터럴
        if "this" in node.get("args", {}):
            sub = node["args"]["this"]
            if isinstance(sub, dict):
                lines.append(f"{arrow}{cls} 내부 ↓")
                lines.extend(parse_aggregation(sub, depth + 1))
            else:
                lines.append(f"{arrow}{cls}: {sub}")
            return lines

    # 기본 리터럴/컬럼명/식
    if "args" in node and "this" in node["args"]:
        val = node["args"]["this"]
        if isinstance(val, dict):
            lines.extend(parse_aggregation(val, depth + 1))
        else:
            lines.append(f"{arrow}{val}")
        return lines

    return lines

# ======= 사용 예시 =======
# from ASTaggregation import parse_aggregation
# lines = parse_aggregation(aggregation_ast_dict)
# for l in lines:
#     print(l)
