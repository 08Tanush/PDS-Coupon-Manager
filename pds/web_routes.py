import sqlite3
from flask import abort, flash, redirect, render_template, request, send_file, session, url_for
from .auth import login_required, csrf_token, require_csrf, password_matches
from .dashboard_service import create_batch, list_batches, get_batch_path, batch_details, dashboard_stats
from .grouped_batch import resume
from .grouped_export import export
from .hospitals import abbreviation

def register_routes(app):
    app.jinja_env.globals['csrf_token']=csrf_token

    @app.after_request
    def headers(resp):
        resp.headers['Cache-Control']='no-store'
        resp.headers['X-Content-Type-Options']='nosniff'
        resp.headers['X-Frame-Options']='DENY'
        resp.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'none'; form-action 'self'; frame-ancestors 'none'"
        return resp

    @app.get('/login')
    def login():
        return render_template('login.html')

    @app.post('/login')
    def login_post():
        require_csrf()
        if not password_matches(request.form.get('password','')):
            flash('Invalid password','error')
            return redirect(url_for('login'))
        session.clear()
        session['admin']=True
        flash('Signed in','success')
        return redirect(url_for('dashboard'))

    @app.post('/logout')
    @login_required
    def logout():
        require_csrf()
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    @login_required
    def dashboard():
        all_batches=list_batches(app.config['PDS_OUTPUT_DIR'])
        return render_template('dashboard.html',batches=all_batches[:6],stats=dashboard_stats(all_batches),selected=all_batches[0] if all_batches else None)

    @app.post('/generate')
    @login_required
    def generate():
        require_csrf()
        if request.form.get('confirm')!='yes':
            abort(400,'Explicit confirmation required')
        try:
            hospital=request.form.get('hospital','').strip()
            count=int(request.form.get('count','100'))
            short=request.form.get('short','')
            doctor=request.form.get('doctor','')
            path,result=create_batch(app.config['PDS_OUTPUT_DIR'],hospital,count,short,doctor,confirm=True)
            if result==0: flash('Batch completed. Review the statuses before distribution.','success')
            else: flash('Batch needs review or resume. Do not distribute pending codes.','error')
            return redirect(url_for('batch_detail',batch_id=path.stem))
        except (ValueError,RuntimeError,sqlite3.Error,OSError,KeyError) as exc:
            flash('Generation stopped: '+str(exc)[:300],'error')
            return redirect(url_for('dashboard'))

    @app.get('/batches')
    @login_required
    def batches():
        return render_template('batches.html',batches=list_batches(app.config['PDS_OUTPUT_DIR']))

    @app.get('/batches/<batch_id>')
    @login_required
    def batch_detail(batch_id):
        try: details=batch_details(get_batch_path(app.config['PDS_OUTPUT_DIR'],batch_id))
        except (ValueError,FileNotFoundError): abort(404)
        return render_template('batch_detail.html',batch=details)

    @app.post('/batches/<batch_id>/resume')
    @login_required
    def resume_batch(batch_id):
        require_csrf()
        try:
            path=get_batch_path(app.config['PDS_OUTPUT_DIR'],batch_id)
            result=resume(path,True)
            flash('Resume completed.' if result==0 else 'Some codes still need review.','success' if result==0 else 'error')
        except (ValueError,RuntimeError,sqlite3.Error,OSError,KeyError) as exc:
            flash('Resume stopped: '+str(exc)[:300],'error')
        return redirect(url_for('batch_detail',batch_id=batch_id))

    @app.get('/batches/<batch_id>/export/<kind>')
    @login_required
    def download(batch_id,kind):
        if kind not in ('verified','audit'): abort(404)
        try:
            path=get_batch_path(app.config['PDS_OUTPUT_DIR'],batch_id)
            with sqlite3.connect(path) as db:
                files=export(db,path)
            target=files[0] if kind=='verified' else files[1]
            return send_file(target,as_attachment=True,download_name=target.name,mimetype='text/csv')
        except (ValueError,FileNotFoundError): abort(404)
