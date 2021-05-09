import os 
from flask import Flask

from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
base_dir = os.getcwd()
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{base_dir}/vocabulary.db"
app.config["DEBUG"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'This_is_very_secret_key'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_SALT'] = 'somesaltfortheforum'
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


roles_users = db.Table('roles_users',
                       db.Column("user_id", db.Integer(), db.ForeignKey("users.id")),
                       db.Column("role_id", db.Integer(), db.ForeignKey("roles.id"))
                       )


class Role (db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)
    description = db.Column(db.String())


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    name = db.Column(db.String(255))
    username = db.Column(db.String(255), unique=True)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    words = db.relationship('Word', backref='users', lazy='dynamic')
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/


    def __repr__(self):
        return '<User %r>' % self.username


class Words(db.Model):
    __tablename__ = 'words'
    id = db.Column(db.Integer(), primary_key=True)
    word = db.Column(db.String(), unique=True)
    assoc = db.Column(db.String())
    hint = db.Column(db.String())
    translation = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Word %r>' % self.word


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@app.route('/')
def index():
    return "Home"


@app.route('/profile')
def profile():
    return "Profile"

if __name__ == "__main__":
    app.run()