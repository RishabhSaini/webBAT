from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.dialects.sqlite
import os

app = Flask(__name__)

#app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://aaron:Onmyrds1!@bat-targeted-db.cr8rg6sr5pl3.us-east-2.rds.amazonaws.com:1723/bat-targeted-db'
db = SQLAlchemy(app)


from .models import trigger
from app import routes
