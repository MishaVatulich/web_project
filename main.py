from flask import Flask, url_for, request, redirect, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from data import db_session
from data.users import User
from data.books import Books
from wtforms.fields.html5 import EmailField
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from os import abort
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header


app = Flask(__name__)
app.config['SECRET_KEY'] = 'Misha&Yarik_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

LOGIN = 'mikhail.ktoto@mail.ru'
PASSWORD = "TPRrutao3Y8-"


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/basket')
@login_required
def basket():
    session = db_session.create_session()
    books = []
    for i in current_user.basket.split():
        books.append(session.query(Books).filter(Books.id == int(i)).first())
    return render_template('basket.html', title='Корзина', books=books, len_books=len(books),
                           fun=url_for('static', filename='css/style2.css'))


@app.route('/order/<int:id>', methods=['POST', 'GET'])
@login_required
def data(id):
    if request.method == 'GET':
        return render_template('order.html', title='Заполнение данных', ord=url_for('static',
                                                                                    filename='css/forbasket.css'))
    elif request.method == 'POST':
        try:
            if request.form['acception'] == 'on':
                session = db_session.create_session()

                server = smtplib.SMTP('smtp.mail.ru', 25)
                server.connect("smtp.mail.ru", 587)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(LOGIN, PASSWORD)
                mails = {}
                if id != 0:
                    book = session.query(Books).filter(Books.id == int(id)).first()
                    book.amount -= 1
                    mails[book.user.email] = [book.title]
                else:
                    for ids in current_user.basket.split():
                        book = session.query(Books).filter(Books.id == int(ids)).first()
                        book.amount -= 1
                        trader = book.user.email
                        if trader in mails:
                            mails[trader].append(book.title)
                        else:
                            mails[trader] = [book.title]
                session.commit()
                for i in mails:
                    msg = MIMEText('''Здравствуйте, вас приветствует магазин VIPBook.
На нашем сайте были заказаны ваши книги: {}
Информация о заказе:
e-mail покупателя: {}
Город: {}
Адрес: {}
Способ доставки: {}
Упаковка: {}
Способ оплаты: {}
Пожелания к заказу: {}
                    
C уважением,
Магазин VIPBook
                    '''.format(', '.join(mails[i]), current_user.email, request.form['city'], request.form['address'],
                               request.form['delivery'], request.form['package'], request.form['pay'],
                               request.form['inform']), 'plain', 'utf-8')
                    msg['subject'] = Header('Заказ в магазине VIPBook', 'utf-8')
                    msg['from'] = LOGIN
                    msg['to'] = 'vatulich@inbox.ru'
                    server.sendmail(msg['from'], msg['to'], msg.as_string())
                server.quit()
                return redirect('/')
        except Exception:
            return redirect('/order')


@app.route('/success', methods=['GET', 'POST'])
def success():
    return render_template('success.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с таким e-mail уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/')
def main_window():
    session = db_session.create_session()
    return render_template('mainpage.html', title='Главная', books=session.query(Books).all(),
                           fun=url_for('static', filename='css/style2.css'))


@app.route('/profile')
@login_required
def profile():
    session = db_session.create_session()
    return render_template('profile.html', title='Профиль',
                           books=session.query(Books).filter(Books.user_id == current_user.id).all(),
                           fun=url_for('static', filename='css/style2.css'))


@app.route('/sell', methods=['POST', 'GET'])
@login_required
def sell():
    if request.method == 'GET':
        return render_template('sell.html', title='Продажа книги', fun=url_for('static', filename='css/style.css'))
    elif request.method == 'POST':
        try:
            if request.form['accept'] == 'on':
                book = Books()
                book.title = request.form['title']
                book.description = request.form['description']
                book.contacts = request.form['contacts']
                book.cost = request.form['cost']
                book.amount = request.form['amount']
                book.genre = request.form['genre']
                book.user_id = current_user.id

                session = db_session.create_session()
                session.add(book)
                session.commit()

                book.image = book.id

                img = request.files['photo'].read()
                out = open("static/img/" + str(book.image) + ".jpg", "wb")
                out.write(img)
                out.close
                session.commit()
                return redirect('/')
        except Exception:
            return redirect('/sell')


@app.route('/add/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_basket(id):
    if str(id) not in current_user.basket.split():
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        user.basket = user.basket + ' ' + str(id)
        session.commit()
    return redirect('/')


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def books_delete(id):
    session = db_session.create_session()
    book = session.query(Books).filter(Books.id == id, Books.user == current_user).first()
    if book:
        session.delete(book)
        session.commit()
        os.remove("static/img/" + str(id) + '.jpg')
    else:
        abort(404)
    return redirect('/profile')


def main():
    db_session.global_init("db/database.sqlite")
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
