import os
import json
import pandas as pd
from SQLCoreProject.utils.path_utils import get_user_data_dir, get_logs_dir, get_cache_dir
from SQLCoreProject.plugin.Key_loader import load_key
from Crypto.Cipher import AES
import base64

KEY = load_key()

def decrypt_json(data, key=KEY):
    nonce = base64.b64decode(data['nonce'])
    ciphertext = base64.b64decode(data['ciphertext'])
    tag = base64.b64decode(data['tag'])
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    decrypted = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(decrypted.decode('utf-8'))

def merge_encrypted(base_dir, key, extension, label):
    data = []
    ext = f'.{extension.lower()}'
    for file in os.listdir(base_dir):
        if file.lower().endswith(ext):
            try:
                with open(os.path.join(base_dir, file), 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    if isinstance(raw, dict) and 'nonce' in raw:
                        decrypted = decrypt_json(raw, key=key)
                    elif isinstance(raw, dict):
                        decrypted = raw
                    else:
                        continue
                    if extension in ["ted", "tmd", "tlc", "acc"]:
                        file_id = os.path.splitext(file)[0]
                        decrypted["id"] = file_id
                    data.append(decrypted)
            except Exception as e:
                continue
    if not data:
        return None
    if extension.lower() in ["tns_rca", "rca_tns"]:
        rca_entries = []
        for d in data:
            if "RCA" in d and isinstance(d["RCA"], list):
                rca_entries.extend(d["RCA"])
        if not rca_entries:
            return None
        def flatten_rca(entry):
            rows = []
            case_id = entry.get("case_id")
            acc_id = entry.get("acc_id")
            def recurse(children, level=1, parent=None):
                for node in children:
                    cur_node = node.get("node")
                    if not cur_node:
                        continue
                    action = node.get("action_item", "")
                    weight = node.get("weight", 0)
                    rows.append({
                        "case_id": case_id,
                        "acc_id": acc_id,
                        "level": level,
                        "parent": parent,
                        "node": cur_node,
                        "action_item": action,
                        "weight": weight
                    })
                    recurse(node.get("children", []), level + 1, cur_node)
            if isinstance(entry.get("tree"), list):
                recurse(entry.get("tree", []))
            return rows
        flattened = []
        for entry in rca_entries:
            if isinstance(entry, dict):
                flattened.extend(flatten_rca(entry))
        df = pd.DataFrame(flattened)
        if df.empty or df.shape[1] == 0:
            return None
        return df
    df = pd.DataFrame(data)
    if df.empty or df.shape[1] == 0:
        return None
    if extension.lower() == "tlc" and "licenses" in df.columns:
        df = df.explode("licenses", ignore_index=True)
        licenses_df = pd.json_normalize(df["licenses"])
        df = pd.concat([df.drop(columns=["licenses"]), licenses_df], axis=1)
    if extension == "ted" and "education" in df.columns:
        df = df.explode("education", ignore_index=True)
        df = pd.concat(
            [df.drop(columns=["education"]), pd.json_normalize(df["education"])],
            axis=1
        )
    elif extension == "tmd" and "medical" in df.columns:
        df = df.explode("medical", ignore_index=True)
        df = pd.concat(
            [df.drop(columns=["medical"]), pd.json_normalize(df["medical"])],
            axis=1
        )
    elif extension == "acc":
        data = []
        for file in os.listdir(base_dir):
            if file.lower().endswith(".acc"):
                try:
                    with open(os.path.join(base_dir, file), "r", encoding="utf-8") as f:
                        raw = json.load(f)
                        dec = decrypt_json(raw, key=key) if isinstance(raw, dict) and 'nonce' in raw else raw
                        emp_id = os.path.splitext(file)[0]
                        rows = []
                        if isinstance(dec, dict) and "accident" in dec:
                            rows = dec["accident"]
                        elif isinstance(dec, list):
                            rows = dec
                        for row in rows:
                            if isinstance(row, dict):
                                row["id"] = emp_id
                                data.append(row)
                except Exception as e:
                    continue
        df = pd.DataFrame(data)
        if not df.empty:
            return df
        return None
    return df

def load_company_data_files(base_dir, key):
    """
    회사 전용 이력/로그/데이터 파일(.tns, .ted, .tmd, .tlc, .acc 등) 읽기/병합/해석/정규화/DF 반환
    반환: { 'people': df, 'education': df, ... }
    """
    result = {}
    for ext, label, name in [
        ('tns', 'PEOPLE', 'people'),
        ('ted', 'EDUCATION', 'education'),
        ('tmd', 'MEDICAL', 'medical'),
        ('TNS_RCA', 'RCA', 'rca'),
        ('tlc', 'LICENSE', 'license'),
        ('acc', 'ACPLG', 'acplg')
    ]:
        df = merge_encrypted(base_dir, key, ext, label)
        if df is not None:
            result[name] = df
    # accident 별도 처리
    accident_path = os.path.join(base_dir, '_accidents.json')
    if os.path.exists(accident_path):
        try:
            with open(accident_path, 'r', encoding='utf-8') as f:
                accident_data = json.load(f)
            accident_df = pd.json_normalize(accident_data)
            result["accident"] = accident_df
        except Exception as e:
            pass
    return result

class CompanyDataPlugin:
    def __init__(self):
        self.data = None
    def load(self, folder_path):
        # 예시: 폴더 내 파일을 읽어 pandas DataFrame 등으로 메모리 DB 구성
        self.data = {}
        for file in os.listdir(folder_path):
            if file.endswith('.tns'):
                with open(os.path.join(folder_path, file), 'r', encoding='utf-8') as f:
                    try:
                        self.data[file] = json.load(f)
                    except Exception as e:
                        print(f"[ERROR] {file} → {e}")
        # 실제 구현에서는 기존 병합/복호화 로직을 여기에 추가 