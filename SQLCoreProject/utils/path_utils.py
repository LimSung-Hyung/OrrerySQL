import os
import sys

def get_user_data_dir(app_name='OrrerySQL'):
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
    elif sys.platform == 'darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    data_dir = os.path.join(base, app_name)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_logs_dir():
    base = get_user_data_dir()
    logs = os.path.join(base, 'logs')
    os.makedirs(logs, exist_ok=True)
    return logs

def get_cache_dir():
    base = get_user_data_dir()
    cache = os.path.join(base, 'cache')
    os.makedirs(cache, exist_ok=True)
    return cache

def get_company_data_dir():
    base = get_user_data_dir()
    company = os.path.join(base, 'company')
    os.makedirs(company, exist_ok=True)
    return company

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path) 