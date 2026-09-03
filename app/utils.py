import json
import hashlib
from typing import List, Dict, Optional

DATABASE_FILE = 'app/database.json'

def get_db() -> List[Dict]:
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_db(data: List[Dict]):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_md5(password: str) -> str:
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def find_user(login: str) -> Optional[Dict]:
    users = get_db()
    return next((user for user in users if user['login'] == login), None)

def update_user_profile(login: str, message: str = None, photo: str = None):
    users = get_db()
    for user in users:
        if user['login'] == login:
            if message is not None:
                user['message'] = message
            if photo is not None:
                user['photo'] = photo
            save_db(users)
            return

def delete_user(login: str) -> Optional[Dict]:
    users = get_db()
    user_to_delete = next((u for u in users if u['login'] == login), None)
    if user_to_delete:
        new_users = [u for u in users if u['login'] != login]
        save_db(new_users)
    return user_to_delete