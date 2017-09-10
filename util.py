from flask import request, flash, redirect, url_for
from time import time
from os.path import join
from PIL import Image
from models import Boards, Posts, Users, Reports, Rules, Css
from app import db
from datetime import datetime
from config import *
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc
from flask import session, redirect, url_for, escape, request
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

def board_inexistent(name):
    if name not in BOARDS:
        flash('board ' + name + ' does not exist')
        return True

def upload_file():
    file = request.files['file']
    fname = ''
    if file and allowed_file(file.filename):
        # Save file as <timestamp>.<extension>
        ext = file.filename.rsplit('.', 1)[1]
        fname = str(int(time() * 1000)) + '.' + ext
        file.save(join(UPLOAD_FOLDER, fname))

        # Pass to PIL to make a thumbnail
        if ext == "webm":
            pass
        else:
            file = Image.open(file)
            file.thumbnail((200,200), Image.ANTIALIAS)
            file.save(join(THUMBS_FOLDER, fname))
    return fname

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def no_image():
    if not request.files['file']:
        flash('Must include an image')
        return True
    return False

def no_content_or_image():
    if not request.files['file'] and request.form['post_content'] == '':
        flash('Must include a comment or image')
        return True
    return False

def get_replies(thread):
    return db.session.query(Posts).filter_by(op_id = thread, deleted = 0).all()

def get_last_replies(thread):
    return db.session.query(Posts).filter_by(op_id = thread, deleted = 0).order_by(db.text('id desc')).limit(5)

def get_OPs(board):
    return db.session.query(Posts).filter_by(op_id = '0', board = board, deleted = 0).order_by(db.text('last_bump desc')).limit(10)

def get_OPs_catalog(board):
    return db.session.query(Posts).filter_by(op_id = '0', board = board, deleted = 0).order_by(db.text('last_bump desc')).limit(100)

def get_OPs_all():
    return db.session.query(Posts).filter(Posts.board != "lewd").filter_by(op_id = '0'               , deleted = 0).order_by(db.text('last_bump desc')).limit(10)

def get_thread_OP(id):
    return db.session.query(Posts).filter_by(id = id).all()

def get_sidebar(board):
    return db.session.query(Boards).filter_by(name=board).first()

def new_post(board, op_id = 0):
    newPost = Posts(board   = board,
                    name    = request.form['name'],
                    subject = request.form['subject'],
                    email   = request.form['email'],
                    text    = request.form['post_content'],
                    date    = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    fname   = upload_file(),
                    op_id   = op_id, # Threads are normal posts with op_id set to 0
                    deleted = False)
    return newPost


#THIS SECTION IS THROWING ERRORS, LETS LOOK AT IT TOMMOROW~~~

def bump_thread(op_id):
#OP = db.session.query(Posts).filter_by(id=op_id).first()
#OP.last_bump = datetime.now()
#    db.session.add(OP) '''
 #   if op_id
    OP = db.session.query(Posts).filter_by(id = op_id).first()
    OP.last_bump = datetime.now()
    db.session.commit()

def reply_count(op_id):
    return db.session.query(Posts).filter_by(op_id = op_id).count()

def delete_post(id):
    post = db.session.query(Posts).filter_by(id=id).one()
    post.deleted = True
    db.session.add(post)
    db.session.commit()

def delete_image(id):
    post = db.session.query(Posts).filter_by(id=id).one()
    post.deleted_image = True
    db.session.add(post)
    db.session.commit()

def check_auth(username, password):
    if (db.session.query(Users).filter_by(username=username).all()):
        usersce = db.session.query(Users).filter_by(username=username).first()
        pw_hash = usersce.pw_hash
        if (check_password_hash(pw_hash, password)):
            return True
        else:
            return False
    else:
        return False
def report_post(op_id):
	post = db.session.query(Posts).filter_by(id = op_id).first()
	rboard = post.board
	rdate = datetime.now()
	if (post.deleted == True):
		rdeleted = 1
	else:
		rdeleted = 0
	rop  = post.id
	add_report(rboard, rdate, rdeleted, rop)

def add_report(rboard, rdate, rdeleted, rop):
	#newRep = db.session.query(Reports).filter_by(id=id).one()
	print(rboard)
	print(rdate)
	print(rdeleted)
	print(rop)
	newRep = Reports(board   = rboard,
		rdate    = rdate,
		deleted = rdeleted,
		op_id   = rop,
		)
	db.session.add(newRep)
	db.session.commit()

def get_reports():
    return db.session.query(Reports).all()

def usercreate(name, password):
	pw_hash = generate_password_hash(password)
	user = Users(username=name, pw_hash=pw_hash)
	db.session.add(user)
	db.session.commit()
def setrules(rules):

	db.session.query(Rules).delete()
	db.session.commit()

	for line in rules.splitlines():
		edited = datetime.now()
		newRules = Rules(rules=line, edited = edited)
		db.session.add(newRules)
		db.session.commit()

def getrules():
	return db.session.query(Rules).all()



def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

def getcss():
    if session.get('css') is not None:
		css = session['css']
		print css
    else:
        css = "style.css"
    return css

def setcss(css):
	edited = datetime.now()
	newCss = Css(css=css, edited = edited)
	db.session.add(newCss)
	db.session.commit()

def getcsslist():
	return db.session.query(Css).all()
def get_users():
	return db.session.query(Users).all()
def delete_user(killuser):
    if (killuser == "1"):
        flash('can\'t delete root user')
    else:
        db.session.query(Users).filter_by(id=killuser).delete()
        db.session.commit()
def change_password(username, password):
    name=username
    db.session.query(Users).filter_by(username=username).delete()
    db.session.commit()
    usercreate(name, password)

def sql_get_one(x):
    for r in x: return r[0]

def get_popular_threads():
    results = db.engine.execute("SELECT CASE WHEN op_id = 0 THEN id ELSE op_id END AS normalized_id, COUNT(*) AS count FROM " + Posts.__tablename__ + " WHERE date > (DATETIME('now') - 604800) AND NOT deleted GROUP BY normalized_id ORDER BY count DESC LIMIT 5")
    l = [x[0] for x in results]
    return [Posts.query.filter_by(id = x).first() for x in l]

def dismiss_report(report_id):
    report_id = report_id
    db.session.query(Reports).filter_by(id=report_id).delete()
    db.session.commit()

def thumbnail(fname):
    if fname is None: return None
    ext = fname.split(".")[-1]
    if ext == "webm": return "/static/video.png"
    if ext == "pdf": return "/static/doc.png"
    return "/static/thumbs/" + fname
def tn_all(l):
    for x in l:
	x.thumbnail = thumbnail(x.fname)

# Run at app start
for board in BOARDS:
    if Boards.query.filter_by(name = board).first() is None:
	b = Boards()
	b.name = board
	b.long_name = board
	b.description = board
	b.hidden = False
	db.session.add(b)
db.session.commit()
