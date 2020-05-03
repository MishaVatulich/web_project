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


@app.route('/order/<int:book_id>', methods=['POST', 'GET'])
@login_required
def order(book_id):
    session = db_session.create_session()
    if request.method == 'GET':
        if book_id != 0:
            if session.query(Books).filter(Books.id == book_id).first().amount == 0:
                return redirect('/')
            else:
                books = [session.query(Books).filter(Books.id == book_id).first()]
        else:
            books = []
            for ids in current_user.basket.split():
                book = session.query(Books).filter(Books.id == int(ids)).first()
                if book.amount != 0:
                    books.append(book)
            if len(books) == 0:
                return redirect('/')
        return render_template('order.html', title='Заполнение данных', ord=url_for('static',
                                                                                    filename='css/forbasket.css'),
                               books=books)
    elif request.method == 'POST':
        try:
            if request.form['acception'] == 'on':
                server = smtplib.SMTP('smtp.mail.ru', 25)
                server.connect("smtp.mail.ru", 587)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(LOGIN, PASSWORD)
                mails = {}
                if book_id != 0:
                    book = session.query(Books).filter(Books.id == book_id).first()
                    book.amount -= int(request.form[str(book.id)])
                    mails[book.user.email] = [book.title + '(x' + request.form[str(book.id)] + ')']
                else:
                    for ids in current_user.basket.split():
                        book = session.query(Books).filter(Books.id == int(ids)).first()
                        if book.amount != 0:
                            book.amount -= int(request.form[str(book.id)])
                            trader = book.user.email
                            if trader in mails:
                                mails[trader].append(book.title + '(x' + request.form[str(book.id)] + ')')
                            else:
                                mails[trader] = [book.title + '(x' + request.form[str(book.id)] + ')']
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
                    msg['to'] = i
                    server.sendmail(msg['from'], msg['to'], msg.as_string())
                server.quit()
                return redirect('/')
        except Exception:
            return redirect('/order/{}'.format(book_id))


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


@app.route('/', methods=['GET', 'POST'])
def main_window():
    session = db_session.create_session()
    if request.method == 'GET':
        return render_template('mainpage.html', title='Главная',
                               books=session.query(Books).filter(Books.amount != 0).all(),
                               fun=url_for('static', filename='css/style2.css'))
    elif request.method == 'POST':
        min_cost = request.form['min_cost']
        max_cost = request.form['max_cost']
        if request.form['min_cost'] == '':
            min_cost = 0
        if request.form['max_cost'] == '':
            max_cost = 10 ** 10
        if request.form['filt_genre'] == 'Все':
            books = session.query(Books).filter(Books.cost >= int(min_cost), Books.cost <= int(max_cost),
                                                Books.amount != 0).all()
        else:
            books = session.query(Books).filter(Books.genre == request.form['filt_genre'],
                                                Books.cost >= int(min_cost), Books.cost <= int(max_cost),
                                                Books.amount != 0).all()
        find_books = []
        for i in books:
            if request.form['search_title'].lower() in i.title.lower() and \
               request.form['search_name'].lower() in i.user.name.lower():
                find_books.append(i)
        return render_template('mainpage.html', title='Главная', books=find_books, len_books=len(books),
                               fun=url_for('static', filename='css/style2.css'))


@app.route('/profile/<int:profile_id>')
def profile(profile_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == profile_id).first()
    return render_template('profile.html', title='Профиль',
                           user=user, len_books=len(user.books),
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
                book.cost = request.form['cost']
                book.amount = request.form['amount']
                book.genre = request.form['genre']
                book.user_id = current_user.id

                session = db_session.create_session()
                session.add(book)
                session.commit()

                book.image = str(book.user_id) + '_' + book.created_date

                img = request.files['photo'].read()
                out = open("static/img/" + book.image + ".jpg", "wb")
                out.write(img)
                out.close
                session.commit()
                return redirect('/')
        except Exception:
            return redirect('/sell')


@app.route('/add/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_to_basket(book_id):
    if current_user.basket is not None:
        if str(book_id) not in current_user.basket.split():
            session = db_session.create_session()
            user = session.query(User).filter(User.id == current_user.id).first()
            user.basket = user.basket + ' ' + str(book_id)
            session.commit()
    else:
        session = db_session.create_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        user.basket = str(book_id)
        session.commit()
    return redirect('/')


@app.route('/delete/<int:book_id>', methods=['GET', 'POST'])
@login_required
def books_delete(book_id):
    session = db_session.create_session()
    book = session.query(Books).filter(Books.id == book_id, Books.user == current_user).first()
    if book:
        os.remove("static/img/" + book.image + '.jpg')
        for user in session.query(User).all():
            if str(book_id) in user.basket.split():
                user_basket = user.basket.split()
                user_basket.remove(str(book_id))
                user.basket = ' '.join(user_basket)
        session.delete(book)
        session.commit()
    else:
        abort(404)
    return redirect('/profile/{}'.format(current_user.id))


@app.route('/basket_delete/<int:book_id>', methods=['GET', 'POST'])
@login_required
def basket_delete(book_id):
    session = db_session.create_session()
    user = session.query(User).filter(User.id == current_user.id).first()
    user_basket = user.basket.split()
    user_basket.remove(str(book_id))
    user.basket = ' '.join(user_basket)
    session.commit()
    return redirect('/basket')


@app.route('/change/<int:book_id>', methods=['GET', 'POST'])
@login_required
def books_change(book_id):
    session = db_session.create_session()
    book = session.query(Books).filter(Books.id == book_id, Books.user == current_user).first()
    if request.method == 'GET':
        return render_template('change.html', title='Изменение книги', fun=url_for('static', filename='css/style.css'),
                               book=book)
    elif request.method == 'POST':
        book.amount = request.form['amount']
        book.cost = request.form['cost']
        session.commit()
        return redirect('/profile/{}'.format(current_user.id))


def main():
    db_session.global_init("db/database.sqlite")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    

if __name__ == '__main__':
    main()
