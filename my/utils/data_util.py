import os
from pathlib import Path

current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
cookies_dir = current_dir.parent.parent / 'cookies'
douyin_cookies_dir = cookies_dir / 'douyin_uploader'
def get_douyin_cookie_path(account_name):
    return douyin_cookies_dir / f"{account_name}.json"