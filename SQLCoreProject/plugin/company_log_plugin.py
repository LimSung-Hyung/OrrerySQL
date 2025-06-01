import os
from SQLCoreProject.utils.path_utils import get_logs_dir

def log_company_history(msg, filename="company_history.log"):
    """
    회사 전용 이력/로그를 logs 폴더 하위에 기록하는 함수.
    """
    log_path = os.path.join(get_logs_dir(), filename)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n") 