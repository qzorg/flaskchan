Imageboard Software written in Flask. Designed to have very little JS, and should be able to operate with none at all. GPL-3.0+

## Creating a Dev Environment


1. Install the dependancies for your distro
- sudo apt-get install libjpeg-dev zlib1g-dev python python-dev python-pip libtiff5-dev libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk

- sudo yum install python python-devel python-pip libtiff-devel libjpeg-devel libzip-devel freetype-devel lcms2-devel libwebp-devel tcl-devel tk-devel
2. pip install -r requirements.txt
3. python app.py
4. Default mod: (user / test)
5. Use the mod panel to change the default user (user) password. This is your root "recovery" user and it should have a strong and memorable password.

## Deploying on Apache wsgi

1. apt-get install git apache2 libapache2-mod-wsgi libjpeg-dev zlib1g-dev python python-dev python-pip libffi-dev
2. cd /var/www/ && git clone https://github.com/qzorg/flaskchan.git
3. Modify the Deploy/app.wsgi file to fit your needs, then copy it to your $SITEROOT/flaskchan/.
4. Edit the Deploy/devchan.conf and replace all lines that start with $ with your own information. Copy the devchan.conf file to your /etc/apache2/sites-enabled/.
5. pip install -r requirements.txt.
6. Edit config.py to include direct paths to directories such as static/images/, static/thumbs, and the sqlite database.
6. service apache2 reload.
