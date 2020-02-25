import os
from flask import (Flask, current_app, flash, json, redirect, render_template,
                   request, send_from_directory, url_for, g, session)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from werkzeug.utils import secure_filename
from flask_security import (RoleMixin, Security,
                            SQLAlchemySessionUserDatastore, UserMixin,
                            current_user, login_required)  
from flask import Flask                                            
import datetime
import re

import mysql.connector

app = Flask(__name__)
application = app

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://std_866:qwertyuio@std-mysql:3306/std_866'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_PASSWORD_SALT'] = 'salt'
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
db = SQLAlchemy(app)
app.secret_key = "super secret key"

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    fullname = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(255))

db.create_all()
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)

@app.route('/')
def main():
    cnx = mysql.connector.connect(user='std_866', password='qwertyuio',host='std-mysql.ist.mospolytech.ru', database='std_866')
    cursor = cnx.cursor() 
    cursor.execute("SELECT `id`,`title`,`author`,`release`,`quantity` FROM `books` ORDER BY `books`.`author` DESC")
    _All_Book = cursor.fetchall()
    cursor.execute("SELECT `journal`.`id`,`journal`.`date`, `books`.`title`,`books`.`author`,`journal`.`status` FROM `books` JOIN `journal`  ON (`books`.`id` = `journal`.`book`)")
    _Issued_books = cursor.fetchall()
    cursor.execute("SELECT `user`.`fullname` FROM `journal` JOIN `user`  ON (`journal`.`user_id` = `user`.`id`)")
    _Book_user = cursor.fetchall()
    cursor.execute("SELECT `user`.`id`,`user`.`fullname` FROM `user`")
    _All_user = cursor.fetchall()
    cursor.close()
    return render_template('index.html', All_Book = _All_Book, Issued_books = _Issued_books, Book_user = _Book_user, All_user = _All_user)

@app.route('/showSignUp', methods=["GET", "POST"])
def showSignUp():
    if current_user.is_authenticated:
        return render_template('index.html')
    elif request.method == 'POST':
        _nickname = request.form['inputNickName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']
        _fullname = request.form['inputLastname'] + ' ' + request.form['inputFirstname'] + ' ' + request.form['inputpatronymic']
        email_user = User.query.filter(User.email == _email).first()
        if email_user:
            flash('Пользователь с таким e-mail уже существует!')
            return render_template('signup.html',nickname=_nickname, password=_password)
        nickname_user = User.query.filter(User.nickname == _nickname).first()
        if nickname_user:
            flash('Пользователь с таким никнеймом уже существует!')
            return render_template('signup.html', email=_email, password=_password)
        Us = user_datastore.create_user(nickname=_nickname, email=_email, password=_password, fullname = _fullname)

        # Rol = user_datastore.create_role(name='specialist', description='specialist')
        # Rol = user_datastore.create_role(name='admin', description='administrator')
        # user_datastore.add_role_to_user(Us, Rol)
        # user_datastore.add_role_to_user(Us, "admin")

        user_datastore.add_role_to_user(Us, "user")
        # user user@user.user User11
        # admin admin@admin.admin Admin1
        # specialist  specialist@specialist.specialist Specialist1
        db.session.commit()
        return redirect('/login')
    return render_template('signup.html')


@app.route('/newbook', methods=["GET", "POST"])
@login_required
def newbook():
    if request.method == 'POST':
            _Title = request.form['inputTitle']
            _Author = request.form['inputAuthor']
            _Release = request.form['inputRelease']
            _Quantity = request.form['inputQuantity']
            cnx = mysql.connector.connect(user='std_866', password='qwertyuio',host='std-mysql.ist.mospolytech.ru', database='std_866')
            cursor = cnx.cursor() 
            cursor.execute("INSERT INTO `books` (`id`, `title`, `author`, `release`, `quantity`) VALUES (NULL, '" + str(_Title) + "', '" + str(_Author) + "', '" + str(_Release) + "', '" + _Quantity + "');")
            cnx.commit()
            cursor.close()
    return render_template('newbook.html')

@app.route('/take_book/<int:id>', methods=["GET", "POST"])
@login_required
def take_book(id):
    return redirect('/')

@app.route('/del/<int:id>')
@login_required
def dellappeal(id):
    if current_user.has_role('admin'):
        cnx = mysql.connector.connect(user='std_866', password='qwertyuio',host='std-mysql.ist.mospolytech.ru', database='std_866')
        cursor = cnx.cursor() 
        cursor.execute("DELETE FROM `journal` WHERE `journal`.`id` = "+ str(id) +"")
        cnx.commit()
        cursor.close()
    return redirect('/')

if __name__ == "__main__":
    app.debug = True
    app.run()
