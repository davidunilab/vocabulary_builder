import os 
from flask import Flask, url_for, render_template, redirect, request
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, current_user, login_required
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField
from flask_script import Manager, Command


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
manager = Manager(app)
admin = Admin(app, "Vocabulary Builder admin")

roles_users = db.Table('roles_users',
                       db.Column("user_id", db.Integer(), db.ForeignKey("users.id")),
                       db.Column("role_id", db.Integer(), db.ForeignKey("roles.id"))
                       )


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)
    description = db.Column(db.String())

    def __repr__(self):
        return f"<Role {self.name}>"


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
    words = db.relationship('Words', backref='users', lazy='dynamic')
    # https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/

    def __repr__(self):
        return f'<User {self.email} >'


class Words(db.Model):
    __tablename__ = 'words'
    id = db.Column(db.Integer(), primary_key=True)
    word = db.Column(db.String())
    assoc = db.Column(db.String())
    hint = db.Column(db.String())
    translation = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<Word {self.word}>'


class UserView(ModelView):
    # column_exclude_list = ["password"]
    can_delete = True
    can_create = True
    can_edit = True


class WordsView(ModelView):
    # column_exclude_list = ["password"]
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True


class WordsForm(FlaskForm):
    word = StringField("Word")
    assoc = StringField("Association")
    hint = StringField("Hint")
    translation = StringField("Translation")


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@app.route('/words-add', methods=["GET", "POST"])
@login_required
def add_words():
    form = WordsForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            word = Words()
            word.word = request.form.get('word')
            word.assoc = request.form.get('assoc')
            word.hint = request.form.get('hint')
            word.translation = request.form.get('translation')
            word.user_id = current_user.id
            db.session.add(word)
            db.session.commit()

            form.word.data = ''
            form.assoc.data = ''
            form.hint.data = ''
            form.translation.data = ''

    return render_template("add_words.html", title="Add word", form=form)


@app.route('/words-rm', methods=["GET", "POST"])
@login_required
def rm_words():
    words = Words.query.filter(Words.user_id == current_user.id).all()
    if request.method == 'POST':
        if request.form.get("word_id"):
            words = Words.query.filter(Words.user_id == current_user.id).filter(Words.id == request.form.get("word_id")).first()
            db.session.delete(words)
            db.session.commit()
        return redirect(url_for("rm_words"))
    return render_template("rm-words.html", title='Remove Words', words=words)


@app.route('/')
def test():
    return render_template("main.html")


@app.route('/profile')
@login_required
def profile():
    role_names = list((role.name for role in current_user.roles))
    return render_template('profile.html', title="Profile", roles=role_names)


@app.route('/words-list')
@login_required
def words():
    role_names = list((role.name for role in current_user.roles))
    if "admin" in role_names:
        words = Words.query.all()
        return render_template('words_list.html', title="Words", words=words)
    words = Words.query.filter(Words.user_id == current_user.id).all()
    return render_template('words_list.html', title="Words", words=words)


@app.route('/about')
def about():
    return render_template('about.html', title="About")


admin.add_view(UserView(User, db.session))
admin.add_view(ModelView(Role, db.session))
admin.add_view(WordsView(Words, db.session))

@app.before_first_request
def before_first_request_func():
    db.create_all()
    # user_datastore.create_role(name='admin')
    # user_datastore.create_user(username='David', email='davidchincharashvili@gmail.com',
    #                            password='david123', roles=['admin'])



if __name__ == "__main__":
    app.run()
