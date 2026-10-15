"""Local password login only; not Shopify embedded-session authentication."""
import hmac
import secrets
from functools import wraps
from flask import current_app, redirect, request, session, abort, url_for

def password_matches(candidate):
    return hmac.compare_digest(candidate.encode(),current_app.config['PDS_ADMIN_PASSWORD'].encode())

def login_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return fn(*args,**kwargs)
    return wrapper

def csrf_token():
    if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']

def require_csrf():
    if not hmac.compare_digest(str(request.form.get('csrf','')),str(session.get('csrf',''))):
        abort(400,'Invalid form token')
