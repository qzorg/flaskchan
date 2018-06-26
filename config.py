DEBUG = True
SECRET_KEY = 'secret'
SQLALCHEMY_DATABASE_URI = 'sqlite:///posts.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

BUMP_LIMIT         = 100
BOARDS             = ['all', 'diy', 'lam', 'r', 'meta', 'cult', 'create','learn','media','meta', 'programming', 'tech', 'lewd']
UPLOAD_FOLDER      = 'static/images/'
THUMBS_FOLDER      = 'static/thumbs/'
ALLOWED_EXTENSIONS =  set(['png','jpg','jpeg','gif', 'css', 'webm'])
SITE_NAME = 'whatever'
MAX_POSTS          = 100
MAX_FILE           = 5000000 #max file size in bytes
