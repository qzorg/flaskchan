from flask import Flask, request, redirect, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from flask.ext.misaka import Misaka
from functools import wraps
from flask import request, Response
from flask.ext.bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for, escape, request
from werkzeug.utils import secure_filename
import os, json



app = Flask(__name__)
Misaka(app=app, escape    = True,
                no_images = True,
                wrap      = True,
                autolink  = True,
                no_intra_emphasis = True,
                space_headers     = True,
								fenced_code				= True)

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

from config import *
from util import *

db.create_all()
db.session.commit()

@app.route('/')
def show_frontpage():
    css = getcss()
    total_posts = sql_get_one(db.engine.execute("SELECT COUNT(*) FROM " + Posts.__tablename__))
    total_ops = sql_get_one(db.engine.execute("SELECT COUNT(*) FROM " + Posts.__tablename__ + " WHERE op_id = 0"))
    images = sql_get_one(db.engine.execute("SELECT COUNT(*) FROM " + Posts.__tablename__ + " WHERE fname IS NOT NULL AND fname != ''"))
    boards = db.engine.execute("SELECT name, long_name FROM " + Boards.__tablename__)
    recent_posts = Posts.query.order_by(Posts.date.desc()).limit(3).all()
    popular_threads = get_popular_threads()
    # Can't get unique posters, we don't record IP addresses
    return render_template('home.html', css=css, total_posts = total_posts, total_ops = total_ops, images = images, boards = boards, recent_posts = recent_posts, render_template = render_template, json = json, popular_threads = popular_threads)

@app.route('/all/')
def show_all():
    OPs = get_OPs_all()
    rules = getrules()
    css = getcss()
    list = []
    for OP in OPs:
        replies = get_last_replies(OP.id)
        list.append(OP)
        list += replies[::-1]

    return render_template('show_all.html', entries=list, board='all', rules=rules, css = css)

@app.route('/<board>/')
def show_board(board):
    if board_inexistent(board):
        return redirect('/')
    OPs = get_OPs(board)
    list = []
    css = getcss()
    for OP in OPs:
        replies = get_last_replies(OP.id)
        list.append(OP)
        list += replies[::-1]

    sidebar = get_sidebar(board)

    return render_template('show_board.html', entries=list, board=board, sidebar=sidebar, id=0, css=css)

@app.route('/<board>/catalog')
def show_catalog(board):
    OPs = get_OPs_catalog(board)
    sidebar = get_sidebar(board)
    css=getcss()
    return render_template('show_catalog.html', entries=OPs, board=board, sidebar=sidebar, css=css)

@app.route('/<board>/<id>/')
def show_thread(board, id):
    OP      = get_thread_OP(id)
    replies = get_replies(id)
    sidebar = get_sidebar(board)
    css = getcss()

    return render_template('show_thread.html', entries=OP+replies, board=board, id=id, sidebar=sidebar, css=css, render_template = render_template, json = json)

@app.route('/add', methods=['POST'])
def new_thread():
    board = request.form['board']
    if no_image():
        return redirect('/' + board + '/')

    newPost = new_post(board)
    newPost.last_bump = datetime.now()
    db.session.add(newPost)
    db.session.commit()
    return redirect('/' + board + '/')

@app.route('/add_reply', methods=['POST'])
def add_reply():
    board  = request.form['board']
    thread = request.form['op_id']
    if no_content_or_image():
        return redirect('/' + board + '/')

    newPost = new_post(board, thread)
    db.session.add(newPost)
    if 'sage' not in request.form['email'] and reply_count(thread) < BUMP_LIMIT:
        bump_thread(thread)
    db.session.commit()
    return redirect('/' + board + '/' + thread)

@app.route('/del')
def delete():
    post_id = request.args.get('id')
    delete_post(post_id)
    board   = request.args.get('board')
    thread  = request.args.get('thread')
    return redirect('/' + board + '/' + thread + '/admin')
@app.route('/login', methods=['GET', 'POST'])

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/<board>/<id>/admin')
@requires_auth
def show_thread_admin(board, id):
    OP      = get_thread_OP(id)
    replies = get_replies(id)
    sidebar = get_sidebar(board)
    css = getcss()

    return render_template('show_thread_admin.html', entries=OP+replies, board=board, id=id, sidebar=sidebar, css=css)


@app.route('/report')
def report():
	post_id = request.args.get('id')
	report_post(post_id)
	board   = request.args.get('board')
	thread  = request.args.get('thread')
	flash('reported')
	return redirect(request.referrer)
	

@app.route('/reports')
@requires_auth
def showreports():
	reports = get_reports()
	reports = reversed(reports)
	#reports = reports.tolist()
	return render_template('reports.html', reports = reports)
@app.route('/mod')
@requires_auth
def showmod():
	css = getcss()
	return render_template('mod.html', css=css)

@app.route('/modadd', methods = ['GET', 'POST'])
@requires_auth
def addusers():
    css=getcss()
    if request.method == 'POST':
        if not request.form['name'] or not request.form['password1'] or not request.form['password2']:
            flash('Please enter all the fields', 'error')
        else:
            name = request.form['name']
            password1 = request.form['password1']
            password2 = request.form['password2']
            if (password1 == password2):
                password = password1
                usercreate(name, password)
                flash('Record was successfully added')


            else:
                flash('Passwords must match')
    return render_template('adduser.html', css=css)



@app.route('/edrules', methods = ['GET', 'POST'])
@requires_auth
def edrules():
    css = getcss()
    if request.method == 'POST':
        if not request.form['rules']:
            flash('Please enter all the fields', 'error')
        else:
            rules = request.form['rules']
            setrules(rules)
            flash('Rules where successfully updated')

    rules = getrules()
    return render_template('ruleset.html', rules = rules, css=css)

@app.route('/settings', methods = ['GET', 'POST'])
def settings():
    css = getcss()
    csslist = getcsslist()
    lastpage = request.referrer
    if request.method == 'POST':
            session['css'] = request.form['css']
            return redirect(lastpage)
    return render_template('settings.html', css=css, csslist = csslist)


@app.route('/uploadcss', methods = ['GET', 'POST'])
@requires_auth
def uploadcss():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            css = secure_filename(file.filename)
            setcss(css)
            file.save(os.path.join("static/", css))
            return redirect(redirect_url())
    return render_template('uploadcss.html', css=getcss())
@app.route('/deluser', methods = ['GET', 'POST'])
@requires_auth
def delusers():
    if request.method == 'POST':
            killuser = request.form['user']
            delete_user(killuser)
            return redirect(request.referrer)
    users = get_users()
    return render_template('deluser.html', users = users, css = getcss())


@app.route('/changepassword', methods = ['GET', 'POST'])
@requires_auth
def changepassword():
    css=getcss()
    if request.method == 'POST':
        if not request.form['name'] or not request.form['password1'] or not request.form['password2'] or not request.form['oldpassword']:
            flash('Please enter all the fields', 'error')
        else:
            oldpassword = request.form['oldpassword']
            username = request.form['name']
            password1 = request.form['password1']
            password2 = request.form['password2']
            if (password1 == password2):
                password = password1

                if check_auth(username, oldpassword):
                    change_password(username, password)
                    flash("Record successfully updated!")
                else:
                    flash("wrong username or password")
            else:
                flash('Passwords must match')
    return render_template('changepassword.html', css=css)


if __name__ == '__main__':
    print(' * Running on http://localhost:5000/ (Press Ctrl-C to quit)')
    print(' * Database is', SQLALCHEMY_DATABASE_URI)
    app.run(host='0.0.0.0')
