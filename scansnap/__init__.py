import datetime
import logging
from flask import Flask, current_app
#from flask_sqlalchemy import SQLAlchemy
#from flask_bcrypt import Bcrypt
#from flask_login import LoginManager
#from flask_mail import Mail
from scansnap.config import Config

import scansnap.ScanEventListener
import scansnap.websocketserver
import scansnap.utils

# __init__.py is executed multiple time. Why?
# TODO: this stupid guard should not be necessary
#is_initialized = False
#if is_initialized:
#    exit()
#is_initialized = True


log_format = '%(asctime)-15s %(thread)d %(message)s'
logging.basicConfig(filename='scansnap_{}.log'.format(datetime.date.today().isoformat()), level=logging.DEBUG, format=log_format)

logging.info('🐱🐱🐱🐱🐱🐱 Logger configured. Initializing the app.')

app = Flask(__name__)
app.config.from_object(Config)

# This causes RuntimeError: Working outside of application context.
#logging.info('App root path: {}'.format(current_app.root_path))

#db = SQLAlchemy()
#bcrypt = Bcrypt()
#login_manager = LoginManager()

# Set the name of the login view (a function name of a route),
# This is the view which the flask_login will redirect the user
# to when the user attempts to access a view annotated with
# login_required
#login_manager.login_view = 'login'

#login_manager.login_message_category = 'info'

# Note that you might have to turn on less secure app access to send emails
# using your Gmail account:
# https://myaccount.google.com/lesssecureapps
#mail = Mail()

# Initialize extensions
#db.init_app(app)
#bcrypt.init_app(app)
#login_manager.init_app(app)
#mail.init_app(app)

ws_port = 2479
scansnap.websocketserver.start_web_socket_server(ws_port)

scansnap.utils.set_event_listener(scansnap.ScanEventListener.ScanEventListener())

from scansnap import routes