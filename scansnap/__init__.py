import datetime
import logging
import yaml # package: pyyaml
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
log_filename = f'scansnap_{datetime.date.today().isoformat()}.log'
logging.basicConfig(filename=log_filename, level=logging.DEBUG, format=log_format)

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


# Load settings for utils
try:
    with open('utils.yml') as f:
        settings = yaml.safe_load(f)
        logging.info(f'Loading configuration: {str(settings)}')
        # True/False in yaml file is recognized as boolean values in Python,
        # i.e. (settings['test_mode'] == 'True') will return False if lhs is
        # True as it would be comparing a boolean value and a string
        scansnap.utils.Settings.test_mode = settings['test_mode']
        logging.info(settings['test_mode'])
        logging.info(f'scansnap.utils.Settings.test_mode: {str(scansnap.utils.Settings.test_mode)}')
        scansnap.utils.Settings.sudo_scanimage = settings['sudo_scanimage']
except:
    logging.info('Either utils.yml was not found or something else went wrong.')

scansnap.utils.set_event_listener(scansnap.ScanEventListener.ScanEventListener())

from scansnap import routes