import json
from sqlglot import parse_one
from SQLCoreProject.core.ASTselectAnalyzer import extract_select_fields
from SQLCoreProject.core.ASTjoinAnalyzer import extract_join_detail
from SQLCoreProject.core.ASTKeywordsAnalyzer import extract_clause_description
from SQLCoreProject.core.ASTtcAnalyzer import SQLTCAnalyzer
from SQLCoreProject.core.ASTwithAnalyzer import extract_with_blocks
from SQLCoreProject.core.ASTaggregation import parse_aggregation
from SQLCoreProject.core.CTEjoin import _extract_joins
from language.lang import lang

class SQLQueryInterpreter:
    IGNORE_CLASSES = {
        "COLUMN", "IDENTIFIER", "TABLE", "LITERAL", "PAREN",
        "ALIAS", "ASC", "ORDER", "TABLEALIAS"
    }

    CLAUSE_ORDER = [
        "FROM", "JOIN", "ON", "WHERE", "GROUP", "HAVING",
        "SELECT", "DISTINCT", "ORDERED", "LIMIT"
    ]

    def __init__(self, query):
        self.query = query
        try:
            self.tree = parse_one(query)
            dumped = self.tree.dump()
            self.ast = json.loads(dumped) if isinstance(dumped, str) else dumped
            self.classifier = SQLTCAnalyzer(self.ast)
            self.error = None
        except Exception as e:
            self.tree = None
            self.ast = {"error": str(e)}
            self.classifier = None
            self.error = str(e)

    def get_structured_steps(self):
        if self.error:
            return [f"[ERROR] {self.error}"]

        summary = self.get_summary()
        used_keywords = []
        self._extract_keywords_in_order(self.ast, used_keywords)

        # GROUP 방어 - main SELECT에 group by 없으면 강제 필터
        if not self._has_main_group_by():
            # main SELECT GROUP BY 노드를 used_keywords에서 강제 제거
            def is_main_group(kw, node):
                # WITH 블록 아래가 아니고, root level에 붙은 GROUP만 제거
                if kw != "GROUP":
                    return True
                parent = node.get("_parent", None)
                # parent 없이 root node거나, parent가 select라면 main SELECT임
                return False
            used_keywords = [pair for pair in used_keywords if is_main_group(*pair)]

        steps = []
        step_num = 1

        def step(text):
            steps.append(f"{step_num}. {text}")

        def substep(text):
            steps.append(f"↳ {text}")

        cte_conditions = set()
        step_num = self._process_with_blocks(steps, step_num, step, substep, cte_conditions)
        step_num = self._process_from(summary, steps, step_num, step, substep)
        step_num = self._process_joins(used_keywords, steps, step_num, step)
        step_num = self._process_where(summary, cte_conditions, steps, step_num, step, substep)
        step_num = self._process_group(used_keywords, steps, step_num, step)
        step_num = self._process_having(used_keywords, steps, step_num, step)
        step_num = self._process_select(summary, used_keywords, steps, step_num, step)
        step_num = self._process_distinct(used_keywords, steps, step_num, step)
        step_num = self._process_ordered(used_keywords, steps, step_num, step)
        step_num = self._process_limit(used_keywords, steps, step_num, step)

        return steps

    def _process_with_blocks(self, steps, step_num, step, substep, cte_conditions):
        try:
            cte_info = extract_with_blocks(self.ast)
            for cte_name, analysis in cte_info.items():
                if isinstance(analysis, list):
                    steps.append(f"{step_num}. {analysis[0]}")  # 헤더
                    for line in analysis[1:]:
                        steps.append(line)  # 내부는 이미 번호 붙음
                    step_num += 1
                else:
                    steps.append(f"{step_num}. {lang.MSG_ERROR_PARSE.format(target=cte_name)}: {analysis}")
                    step_num += 1
        except Exception as e:
            step(lang.MSG_ERROR_PARSE.format(target="WITH") + f": {str(e)}")
            step_num += 1
        return step_num

    def _process_from(self, summary, steps, step_num, step, substep):
        tables = summary.get("tables")
        if tables:
            if len(tables) <= 2:
                step(f"{lang.MSG_FROM} [{', '.join(tables)}] {lang.MSG_TABLE_SELECT}")
            else:
                step(lang.MSG_FROM + " [")
                for t in tables:
                    steps.append(f"    {t}")
                steps.append("] " + lang.MSG_TABLE_SELECT)
            step_num += 1
        aliases = summary.get("aliases")
        if aliases:
            for table, alias in aliases.items():
                substep(lang.MSG_ALIAS_USED.format(table=table, alias=alias))
        return step_num

    def _process_joins(self, used_keywords, steps, step_num, step):
        join_nodes = [n for kw, n in used_keywords if kw == "JOIN"]
        for node in join_nodes:
            desc = extract_join_detail(node)
            steps.append(f"{step_num}. {desc}")
            step_num += 1
        return step_num

    def _process_where(self, summary, cte_conditions, steps, step_num, step, substep):
        conditions = summary.get("conditions")
        if conditions:
            filtered_conds = [cond for cond in conditions if cond not in cte_conditions]
            if filtered_conds:
                step("WHERE " + lang.MSG_CONDITION_USE + " ↓")
                step_num += 1
                for cond in filtered_conds:
                    if isinstance(cond, str) and "\n" in cond:
                        for line in cond.splitlines():
                            if line.strip():
                                substep(line)
                    elif isinstance(cond, list):
                        for line in cond:
                            substep(line)
                    else:
                        if cond in {"AND", "OR"}:
                            substep(f"{cond} {lang.MSG_CONDITION_USE} {lang.MSG_CONDITION_LINK}")
                        else:
                            substep(f"{cond}")
        return step_num

    def _process_group(self, used_keywords, steps, step_num, step):
        node = self._find_first_clause(used_keywords, "GROUP")
        if node:
            group_args = node.get("args", {})
            group_exprs = group_args.get("expressions")
            if isinstance(group_exprs, list) and any(self._valid_group_col(e) for e in group_exprs):
                desc = extract_clause_description("GROUP", node)
                if desc:  # 빈문자열이면 추가하지 마라
                    step(desc)
                    step_num += 1
            elif "this" in group_args:
                this = group_args["this"]
                if self._valid_group_col(this):
                    desc = extract_clause_description("GROUP", node)
                    if desc:
                        step(desc)
                        step_num += 1
        return step_num

    def _valid_group_col(self, col_node):
        if not col_node or (isinstance(col_node, dict) and not col_node):
            return False
        if isinstance(col_node, dict):
            if col_node.get("class") in {"Identifier", "Column"}:
                col_name = col_node.get("args", {}).get("this")
                return bool(col_name)
            for v in col_node.values():
                if self._valid_group_col(v):
                    return True
        return False

    def _process_having(self, used_keywords, steps, step_num, step):
        node = self._find_first_clause(used_keywords, "HAVING")
        if node:
            desc = extract_clause_description("HAVING", node)
            step(desc)
            step_num += 1
        return step_num

    def _process_select(self, summary, used_keywords, steps, step_num, step):
        node = self._find_first_clause(used_keywords, "SELECT")
        if node:
            select_fields = extract_select_fields(node)
            if select_fields:
                label = lang.MSG_FROM.replace("FROM", "SELECT")
                if len(select_fields) > 3:
                    item_lines = ",\n    ".join(str(i) for i in select_fields)
                    step(f"SELECT using [\n    {item_lines}\n] {lang.MSG_COLUMN_SELECT}")
                else:
                    step(f"SELECT using [{', '.join(str(i) for i in select_fields)}] {lang.MSG_COLUMN_SELECT}")
                step_num += 1
        return step_num

    def _process_distinct(self, used_keywords, steps, step_num, step):
        node = self._find_first_clause(used_keywords, "DISTINCT")
        if node:
            desc = extract_clause_description("DISTINCT", node)
            step(desc)
            step_num += 1
        return step_num

    def _process_ordered(self, used_keywords, steps, step_num, step):
        node = self._find_first_clause(used_keywords, "ORDERED")
        if node:
            desc = extract_clause_description("ORDERED", node)
            step(desc)
            step_num += 1
        return step_num

    def _process_limit(self, used_keywords, steps, step_num, step):
        node = self._find_first_clause(used_keywords, "LIMIT")
        if node:
            desc = extract_clause_description("LIMIT", node)
            step(desc)
            step_num += 1
        return step_num

    def _find_first_clause(self, used_keywords, clause):
        for kw, node in used_keywords:
            if kw == clause:
                return node
        return None

    def _extract_keywords_in_order(self, node, used_keywords):
        if isinstance(node, dict):
            cls = node.get("class")
            # GROUP이면 group 컬럼이 진짜 있을 때만 추가 (main/CTE 공통)
            if cls and cls.upper() == "GROUP":
                group_args = node.get("args", {})
                exprs = group_args.get("expressions")
                has_valid = False
                if isinstance(exprs, list) and any(self._valid_group_col(e) for e in exprs):
                    has_valid = True
                elif "this" in group_args and self._valid_group_col(group_args["this"]):
                    has_valid = True
                # step_num/used_keywords 추가는 컬럼 있을 때만
                if has_valid:
                    used_keywords.append((cls.upper(), node))
            elif cls and cls.upper() not in self.IGNORE_CLASSES:
                used_keywords.append((cls.upper(), node))
            for val in node.values():
                self._extract_keywords_in_order(val, used_keywords)
        elif isinstance(node, list):
            for item in node:
                self._extract_keywords_in_order(item, used_keywords)

    def _has_main_group_by(self):
        """
        쿼리 원본에서 main SELECT(가장 마지막) ~ LIMIT 사이에 group by가 실제로 있는지 검사
        """
        q = self.query.lower()
        select_idx = q.rfind("select")
        group_by_idx = q.rfind("group by")
        limit_idx = q.rfind("limit")
        # group by가 select~limit 사이에 있어야 main SELECT의 group by임
        if group_by_idx == -1 or select_idx == -1:
            return False
        if limit_idx == -1:
            return group_by_idx > select_idx
        return select_idx < group_by_idx < limit_idx

    def get_ast(self):
        ast = self.ast if isinstance(self.ast, dict) else {"error": "AST is not dict"}
        def check_empty_not(node):
            if not isinstance(node, dict):
                return False
            if node.get("class", "").upper() == "NOT":
                right = node.get("args", {}).get("this", {})
                if isinstance(right, dict) and not right.get("class"):
                    print(lang.MSG_WARNING + ": AST 내 NOT 우항이 비어 있음: 파서/라이브러리 문제 가능성 99%")
            for v in node.values():
                if isinstance(v, dict):
                    check_empty_not(v)
                if isinstance(v, list):
                    for i in v:
                        check_empty_not(i)
        check_empty_not(ast)
        return ast

    def get_summary(self):
        return self.classifier.summary() if self.classifier else {}

    def get_logical_flow(self):
        return "\n".join(self.get_structured_steps()) if not self.error else f"[ERROR] {self.error}"

    def get_natural_description(self):
        if self.error:
            return lang.MSG_QUERY_FAIL.format(error=self.error)
        summary = self.get_summary()
        if summary.get("functions"):
            return f"{', '.join(summary['functions'])} {lang.MSG_FUNC_USED}"
        return lang.MSG_SIMPLE_SELECT
