import re
import secrets
from .config import ALPHABET

PERCENTAGES = (6, 7, 8)

def abbreviation(name):
    words = re.findall(r'[A-Za-z0-9]+', name)
    if not words or len(name) > 120:
        raise ValueError('Hospital name must contain letters or digits and be at most 120 characters')
    short = ''.join(word[0] for word in words).upper()[:10]
    return short if len(short) > 1 else words[0][:10].upper()

def plan(name, count, short=None):
    if not 1 <= count <= 5000:
        raise ValueError('Count must be between 1 and 5000')
    prefix = (short or abbreviation(name)).upper()
    if not re.fullmatch(r'[A-Z0-9]{2,10}', prefix):
        raise ValueError('Hospital abbreviation must be 2-10 uppercase letters or digits')
    codes = set()
    while len(codes) < count:
        codes.add(prefix + '-' + ''.join(secrets.choice(ALPHABET) for _ in range(16)))
    return [(code, secrets.choice(PERCENTAGES)) for code in sorted(codes)]
