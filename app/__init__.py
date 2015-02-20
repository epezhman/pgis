from flask import Flask
from flask.ext.assets import Environment, Bundle
from flask.ext.sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

# Create app
app = Flask(__name__)
Bootstrap(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# Assets
assets = Environment(app)
js = Bundle('javascripts/leaflet-src.js', 'javascripts/jquery-2.1.3.min.js', 'javascripts/main.js',
            filters='jsmin', output='gen/packed.js')
assets.register('application_js', js)

less = Bundle('stylesheets/leaflet.css', 'stylesheets/main.less.css',
              filters='less,cssmin', output='gen/packed.css')

assets.register('application_css', less)

# Load Routes
from app import routes



