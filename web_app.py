"""Local-only PDS dashboard. Not an authenticated Shopify embedded application."""
import os
from pathlib import Path
from flask import Flask
from pds.config import load_env
from pds.web_routes import register_routes

def create_app(test_config=None):
    load_env()
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('PDS_SESSION_SECRET', ''),
                      PDS_ADMIN_PASSWORD=os.getenv('PDS_ADMIN_PASSWORD', ''),
                      PDS_OUTPUT_DIR=str(Path(__file__).resolve().parent / 'output'))
    if test_config:
        app.config.update(test_config)
    if not app.config['SECRET_KEY'] or not app.config['PDS_ADMIN_PASSWORD']:
        raise RuntimeError('Set PDS_SESSION_SECRET and PDS_ADMIN_PASSWORD in .env (use long random values).')
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      MAX_CONTENT_LENGTH=128*1024)
    register_routes(app)
    return app

if __name__ == '__main__':
    app = create_app()
    print('LOCAL ONLY: http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
