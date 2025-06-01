import re
from SQLCoreProject.core.ASTtcAnalyzer import SQLTCAnalyzer
from SQLCoreProject.core.ASTKeywordsAnalyzer import extract_clause_description
from SQLCoreProject.core.ASTaggregation import parse_aggregation
from SQLCoreProject.core.ASTselectAnalyzer import extract_select_fields
from SQLCoreProject.core.ASTjoinAnalyzer import extract_join_detail
from SQLCoreProject.core.CTEjoin import _extract_joins
from language.lang import lang

def ascii_box(title, items, box_width=None):
    if isinstance(items, str):
        items = items.splitlines()
    new_items = []
    for line in items:
        new_items.extend(line.splitlines())
    items = new_items
    all_lines = [title] + items
    if box_width is None:
        max_width = max(len(line.rstrip()) for line in all_lines)
        box_width = max_width + 2
    top =  f"┌{'─'*box_width}┐"
    bot =  f"└{'─'*box_width}┘"
    label = f"│ {title.ljust(box_width-1)}│"
    divider = f"├{'─'*box_width}┤"
    body = [f"│ {line.rstrip().ljust(box_width-1)}│" for line in items]
    return '\n'.join([top, label, divider] + body + [bot])

def build_ascii_pipeline(blocks):
    # 1. 전체 박스 최대 폭 미리 산출
    all_lines = []
    for block in blocks:
        title, *body = block.split('\n', 1)
        body_lines = body[0].split('\n') if body else []
        all_lines.extend([title] + body_lines)
    max_width = max(len(line.rstrip()) for line in all_lines) + 2
    # 2. 박스 만들 때 동일 폭 사용
    out_lines = []
    n = len(blocks)
    for idx, block in enumerate(blocks):
        title, *body = block.split('\n', 1)
        box = ascii_box(title, body[0].split('\n') if body else [], box_width=max_width)
        out_lines.append(box)
        if idx < n - 1:
            out_lines.append('   │')
    return '\n'.join(out_lines)

def group_by_step_numbers(lines):
    """
    "1. ...", "2. ..." 등 번호가 붙은 라인 기준으로 박스 텍스트 분할
    내부 필드/조건은 줄바꿈만 유지 (한 박스에 다 박기)
    """
    steps = []
    buf = []
    for line in lines:
        if re.match(r"^\d+\.\s", line):  # 1. 2. ...로 시작
            if buf:
                steps.append('\n'.join(buf))
                buf = []
        buf.append(line)
    if buf:
        steps.append('\n'.join(buf))
    return steps

class SQLFlowVisualizer:
    """
    논리 해석 결과(단계별 numbered line list)를 받아
    아스키아트 박스+파이프라인 구조로 출력 (PySide6 없는 순수 텍스트)
    """
    def __init__(self, flow_steps, parent=None):
        # flow_steps: str or list
        if isinstance(flow_steps, str):
            lines = flow_steps.splitlines()
        elif isinstance(flow_steps, list):
            lines = []
            for x in flow_steps:
                lines += (x.splitlines() if isinstance(x, str) else [])
        else:
            lines = []

        self.step_blocks = group_by_step_numbers(lines)

    def as_ascii_pipeline(self, max_global_width=80):
        # 전체 박스 최대 폭 미리 산출, 단 80자 넘으면 80에 고정
        all_lines = []
        for block in self.step_blocks:
            title, *body = block.split('\n', 1)
            body_lines = body[0].split('\n') if body else []
            all_lines.extend([title] + body_lines)
        max_width = min(max(len(line.rstrip()) for line in all_lines) + 2, max_global_width)
        out_lines = []
        n = len(self.step_blocks)
        for idx, block in enumerate(self.step_blocks):
            title, *body = block.split('\n', 1)
            lines = body[0].split('\n') if body else []
            # 너무 긴 줄은 wrap
            new_lines = []
            for l in lines:
                if len(l) > max_width-2:
                    for i in range(0, len(l), max_width-2):
                        new_lines.append(l[i:i+max_width-2])
                else:
                    new_lines.append(l)
            box = ascii_box(title, new_lines, box_width=max_width)
            out_lines.append(box)
            if idx < n - 1:
                out_lines.append('   │')
        return '\n'.join(out_lines)

    def show(self):
        # 터미널/리포트 출력
        pass

# ======= 사용 예시 =======
if __name__ == '__main__':
    # 예시 논리 해석 결과(번호 붙은 단계별 블록)
    example = [
        lang.EXAMPLE_FROM_PEOPLE,
        lang.EXAMPLE_SELECT_FIELDS,
        lang.EXAMPLE_WHERE,
        lang.EXAMPLE_GROUP_BY,
        lang.EXAMPLE_ORDER_BY
    ]
    viz = SQLFlowVisualizer(example)
    viz.show()
