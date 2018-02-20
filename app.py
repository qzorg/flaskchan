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
import os, json, re, random




app = Flask(__name__)
Misaka(app=app, escape    = True,
                no_images = True,
                wrap      = True,
                autolink  = True,
                no_intra_emphasis = True,
                space_headers     = True,
                                fenced_code                = True)

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

from config import *
from util import *

db.create_all()
db.session.commit()

@app.route('/')
def show_frontpage():
    if not first_run_check():
        site_name = SITE_NAME
        css = getcss()
        total_posts = sql_get_one(db.engine.execute("SELECT COUNT(*) FROM " + Posts.__tablename__ + " WHERE NOT deleted"))
        total_ops = sql_get_one(db.engine.execute("SELECT COUNT(*) FROM " + Posts.__tablename__ + " WHERE op_id = 0 AND NOT deleted"))
        images = sql_get_one(db.engine.execute("SELECT COUNT(*) FROM " + Posts.__tablename__ + " WHERE fname IS NOT NULL AND fname != '' AND NOT deleted"))
        boards = db.engine.execute("SELECT name, long_name FROM " + Boards.__tablename__)
        recent_posts = Posts.query.order_by(Posts.date.desc()).filter(Posts.board != 'lewd').filter(Posts.deleted != 1).limit(3).all()
        popular_threads = get_popular_threads()
        tn_all(recent_posts)
        truncate = lambda x: x[:100] + "..." if len(x) > 100 else x
        # Can't get unique posters, we don't record IP addresses
        return render_template('home.html', css=css, total_posts = total_posts, total_ops = total_ops, images = images, boards = boards, recent_posts = recent_posts, render_template = render_template, json = json, popular_threads = popular_threads, truncate = truncate, re = re, site_name = site_name)
    else:
        return redirect(url_for("setup"))
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


@app.route('/all/')
def show_all():
    return show_board("all",0)
@app.route('/<board>/')
@app.route('/<board>')
def show_board_default(board):
    return redirect('/'+board+'/0/') 
@app.route('/<board>/<page>/')
def show_board(board,page):
    if not page:
        page = 0
    if board_inexistent(board) and board != "all":
        return redirect('/')
    if board == "all":
        OPs = get_OPs_all()
    else:
        OPs = get_OPs_page(board,page)
    list = []
    css = getcss()
    for OP in OPs:
        replies = get_last_replies(OP.id)
        list.append(OP)
        list += replies[::-1]

    sidebar = get_sidebar(board)
    coalesce = lambda x: x.id if x.op_id == 0 else x.op_id
    try:
        if list[0]:
            list[0].new_thread = False
    except:
        pass
    for i in range(len(list) - 1):
        if coalesce(list[i]) != coalesce(list[i + 1]):
            list[i + 1].new_thread = True
        else:
            list[i + 1].new_thread = False
    tn_all(list)
    user = "user"
    return render_template('show_board.html', entries=list, board=board, sidebar=sidebar, id=0, css=css, json = json, user=user)



@app.route('/mod/<board>/<page>/')
@requires_auth
def show_board_for_admin(board):
    if board_inexistent(board) and board != "all":
        return redirect('/')
    if board == "all":
        OPs = get_OPs_all()
    else:
        OPs = get_OPs_page(board,page)
    list = []
    css = getcss()
    for OP in OPs:
        replies = get_last_replies(OP.id)
        list.append(OP)
        list += replies[::-1]

    sidebar = get_sidebar(board)
    coalesce = lambda x: x.id if x.op_id == 0 else x.op_id
    try:
        if list[0]:
            list[0].new_thread = False
    except:
        pass
    for i in range(len(list) - 1):
        if coalesce(list[i]) != coalesce(list[i + 1]):
            list[i + 1].new_thread = True
        else:
            list[i + 1].new_thread = False
    tn_all(list)
    user = "mod"
    return render_template('show_board.html', entries=list, board=board, sidebar=sidebar, id=0, css=css, json = json, user=user)



@app.route('/imagedump/')
def show_imagedump():
    image_data = db.engine.execute("SELECT fname FROM " + Posts.__tablename__ + " WHERE fname IS NOT NULL AND fname != '' AND NOT deleted").fetchall()
    images = []
    for image in image_data:
        images.append(image[0])
    image_count = len(images)
    css = getcss()
    return render_template('imagedump.html', css=css, image_count=image_count, images=images)

@app.route('/random/')
def random_thread():
    #OPs = db.session.query(Posts).filter_by(op_id = '0', deleted = 0).filter(Posts.board != "lewd").offset(int(rowCount*random.random())).first()
    OPs_data = db.engine.execute("SELECT id, board FROM " + Posts.__tablename__ + " WHERE board IS NOT 'lewd' AND NOT deleted").fetchall()
    OP_ids = []
    OP_boards = []
    for OP in OPs_data:
        OP_ids.append(OP[0])
        OP_boards.append(OP[1])
    
    random_int = random.randint(0, len(OP_ids)-1)

    return redirect('/' + OP_boards[random_int] + '/' + str(OP_ids[random_int]))

@app.route('/random_image/')
def random_image():
    image_data = db.engine.execute("SELECT fname FROM " + Posts.__tablename__ + " WHERE fname IS NOT NULL AND fname != '' AND NOT deleted").fetchall()
    images = []
    for image in image_data:
        images.append(image[0])
    image_count = len(images)
    image = random.choice(images)
    return redirect('/static/images/' + image)

@app.route('/random_image_sfw/')
def random_image_sfw():
    image_data = db.engine.execute("SELECT fname FROM " + Posts.__tablename__ + " WHERE fname IS NOT NULL AND fname != '' AND NOT deleted AND board IS NOT 'lewd'").fetchall()
    images = []
    for image in image_data:
        images.append(image[0])
    image_count = len(images)
    image = random.choice(images)
    return redirect('/static/images/' + image)

@app.route('/<board>/catalog')
def show_catalog(board):
    OPs = get_OPs_catalog(board)
    sidebar = get_sidebar(board)
    css=getcss()
    user = "user"
    return render_template('show_catalog.html', entries=OPs, board=board, sidebar=sidebar, css=css, user=user)

@app.route('/<board>/thread/<id>/')
def show_thread(board, id):
    OP      = get_thread_OP(id)
    print(OP)
    if OP == []:
        return redirect('/' + board + '/')
    replies = get_replies(id)
    sidebar = get_sidebar(board)
    css = getcss()
    entries = OP + replies
    tn_all(entries)
    user = "user"
    return render_template('show_thread.html', entries=entries, board=board, id=id, sidebar=sidebar, css=css, render_template = render_template, json = json, user=user)




@app.route('/mod/<board>/catalog')
@requires_auth
def show_catalog_for_admin(board):
    OPs = get_OPs_catalog(board)
    sidebar = get_sidebar(board)
    css=getcss()
    user = "mod"
    return render_template('show_catalog.html', entries=OPs, board=board, sidebar=sidebar, css=css, user=user)

@app.route('/mod/<board>/thread/<id>/')
@requires_auth
def show_thread_for_admin(board, id):
    OP      = get_thread_OP(id)
    print(OP)
    if OP == []:
        return redirect('/' + board + '/')
    replies = get_replies(id)
    sidebar = get_sidebar(board)
    css = getcss()
    entries = OP + replies
    tn_all(entries)
    user = "mod"
    return render_template('show_thread.html', entries=entries, board=board, id=id, sidebar=sidebar, css=css, render_template = render_template, json = json, user=user)





@app.route('/add', methods=['POST'])
def new_thread():
    ipaddr = request.environ['REMOTE_ADDR']
    board = request.form['board']
    if board_inexistent(board):
        flash('no such board')
        return redirect('/' + board + '/')

 
    if no_image():
        return redirect('/' + board + '/')
    if check_banned(ipaddr):
               flash('You are banned, fuck off')
               return redirect('/' + board + '/')
    
    newPost = new_post(board, ipaddr)
    newPost.last_bump = datetime.now()
    db.session.add(newPost)
    db.session.commit()
    bump_off_last(board)
    return redirect('/' + board + '/' + "thread/" + str(newPost.id))

@app.route('/add_reply', methods=['POST'])
def add_reply():
    ipaddr = request.environ['REMOTE_ADDR']
    board  = request.form['board']
    thread = request.form['op_id']
    if no_content_or_image():
        return redirect('/' + board + '/')

    newPost = new_post(board, ipaddr, thread)
    db.session.add(newPost)
    if 'sage' not in request.form['email'] and reply_count(thread) < BUMP_LIMIT:
        bump_thread(thread)
    if check_banned(ipaddr):
               flash('You are banned, fuck off')
               return redirect('/' + board + '/')
    db.session.commit()
    return redirect('/' + board + '/thread/' + thread)

@app.route('/del')
def delete():
    post_id = request.args.get('id')
    delete_post(post_id)
    board   = request.args.get('board')
    thread  = request.args.get('thread')
    return redirect('/' + board + '/' + thread + '/admin')
@app.route('/<board>/thread/<id>/admin')
@requires_auth
def show_thread_admin(board, id):
    OP      = get_thread_OP(id)
    replies = get_replies(id)
    sidebar = get_sidebar(board)
    css = getcss()

    return render_template('show_thread_admin.html', entries=OP+replies, board=board, id=id, sidebar=sidebar, css=css)

@app.route('/<board>/admin')
@requires_auth
def show_board_admin(board, id):
    OP      = get_thread_OP(id)
    replies = get_replies(id)
    sidebar = get_sidebar(board)
    css = getcss()

    return render_template('show_board_admin.html', entries=OP+replies, board=board, id=id, sidebar=sidebar, css=css)


@app.route('/report')
def report():
    post_id = request.args.get('id')
    report_post(post_id)
    board   = request.args.get('board')
    thread  = request.args.get('thread')
    flash('reported')
    return redirect(request.referrer)
    

@app.route('/mod/reports')
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

@app.route('/mod/modadd', methods = ['GET', 'POST'])
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



@app.route('/mod/edrules', methods = ['GET', 'POST'])
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


@app.route('/mod/uploadcss', methods = ['GET', 'POST'])
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
@app.route('/mod/deluser', methods = ['GET', 'POST'])
@requires_auth
def delusers():
    if request.method == 'POST':
            killuser = request.form['user']
            delete_user(killuser)
            return redirect(request.referrer)
    users = get_users()
    return render_template('deluser.html', users = users, css = getcss())


@app.route('/mod/changepassword', methods = ['GET', 'POST'])
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

@app.route('/mod/dismiss/<report>', methods = ['GET', 'POST'])
@requires_auth
def dismiss(report):
    report_id = report
    dismiss_report(report_id)
    flash('Dismissed')
    return redirect(request.referrer)


@app.route('/mod/bans', methods=['GET','POST'])
@requires_auth
def showbans():
   bans = get_bans()
   bans = reversed(bans)

   return render_template('bans.html', bans = bans)


@app.route('/ban/<variable>', methods=['GET'])
@requires_auth
def banip(variable):
   date=datetime.now()
   ip=get_ip(variable)
   ban(date, ip)
   return redirect(request.referrer)

@app.route('/mod/unban/<variable>', methods=['GET', 'POST'])
@requires_auth
def unban(variable):
   ip=str(variable)
   unban_ip(ip)
   return redirect("/mod/bans")
@app.route('/setup', methods=['GET','POST'])
def setup():
    if first_run_check():
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
                        return redirect("/")


                    else:
                        flash('Passwords must match')

        return render_template("adduser.html", css=getcss())
    else: return("site already configured")

if __name__ == '__main__':
    print(' * Running on http://localhost:5000/ (Press Ctrl-C to quit)')
    print(' * Database is', SQLALCHEMY_DATABASE_URI)
    app.run(host='0.0.0.0')

