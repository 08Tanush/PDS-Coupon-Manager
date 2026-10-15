import os
from pathlib import Path
STORE='doorstep-pharmacy-a19a.myshopify.com'
API_VERSION='2026-10'
ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

def load_env(path=Path('.env')):
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                key,value=line.split('=',1)
                os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
