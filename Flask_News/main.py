import os
import sqlite3

from flask import Flask, render_template, g, request, flash, redirect, url_for, session, abort, make_response
from flask_login import login_required, LoginManager, current_user, login_user, logout_user
import newsapi
from werkzeug.security import generate_password_hash, check_password_hash

from UseFul.FDataBse import FDataBase
from UseFul.UserLogin import UserLogin

app = Flask(__name__)
app.config["SECRET_KEY"] = "wewrtrtey1223345dfgdf"

dbase = None

login_manager = LoginManager(app)
login_manager.login_view = 'no_authorized'
login_manager.login_message = 'Авторизируетесь для доступа к закрытым страницам'
login_manager.login_message_category = 'success'


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


def connect_db():
    conn = sqlite3.connect('my_db.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if not hasattr(g, "link_db"):
        g.link_db = connect_db()
    return g.link_db


def create_db():
    db = connect_db()
    with app.open_resource("db.sql", mode="r") as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, dbase)


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    if request.method == "POST":
        user = dbase.getUserByEmail(request.form['email'])
        if user and check_password_hash(user['psw'], request.form['psw']):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get("remainme") else False
            login_user(userlogin, remember=rm)
            return redirect(request.cookies.get("next") or url_for('profile'))
        flash("Неверные данные  - логин")

    return render_template("index.html", menu=dbase.getMenu(),
                           title="Авторизация")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        session.pop('_flashes', None)
        if (len(request.form['name']) > 4 and
                len(request.form['email']) > 4 and
                len(request.form['psw']) > 4 and
                request.form['psw'] == request.form['psw2']):
            hash = generate_password_hash(request.form['psw'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            print(res)
            if res:
                flash("Вы успешно зарегистрированы", category="success")
                return redirect(url_for('index'))
            else:
                flash("Ошибка при добавлении в БД", category="error")
        else:
            flash("Неверно заполнены поля", category="error")

    return render_template("index.html", menu=dbase.getMenu(),
                           title="Регистрация")


@app.route('/profile')
@login_required
def profile():
    name = current_user.getName()
    return render_template("profile.html", menu=dbase.getMenu(), name=name,
                           title="Профиль пользователя")


@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""
    answer = make_response(img)
    answer.headers["Content-Type"] = "image/png"
    return answer


@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files['file']
        if file:
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                    return redirect(url_for("profile"))
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка чтения файлабновления аватара", "error")
    return redirect(url_for("profile"))


@app.route('/logout')
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    resp = make_response(redirect(url_for("no_authorized")))
    resp.delete_cookie('next')
    return resp


@app.route("/")
def index():
    if not os.path.exists("lesson2_DB.db"):
        create_db()
    # get_news("cat")
    return render_template("index.html", menu=dbase.getMenu(),
                           title="Index page", posts=dbase.getPostAnonce())


@app.route("/add_post", methods=["GET", "POST"])
@login_required
def addPost():
    if request.method == "POST":
        if (len(request.form['name']) > 4 and
                len(request.form['author']) > 4 and
                len(request.form['title']) > 4 and
                len(request.form['description']) > 4 and
                len(request.form['urlToImage']) > 4 and
                len(request.form['url']) > 4 and
                len(request.form['post']) > 10):
            res = dbase.addPost(request.form['name'], request.form['author'], request.form['title'],
                                request.form['description'], request.form['urlToImage'], request.form['url'],
                                request.form['post'])
            if not res:
                flash("Ошибка добавления", category="error")
            else:
                flash("Успешно добавлено", category="success")
        else:
            flash("Ошибка добавления, проверьте ваши данные", category="error")
    return render_template("add_post.html", menu=dbase.getMenu(),
                           title="Добавление статьи")


@app.route("/post/<alias>", methods=["GET", "POST"])
@login_required
def showpost(alias):
    title, post, post_time, author = dbase.getPost(alias)
    if not title:
        abort(404)
    return render_template("showpost.html", menu=dbase.getMenu(), title=title, post=post,
                           post_time=post_time, author=author)


@app.errorhandler(404)
def pageNotFounded(error):
    return render_template("page404.html", title="Страница не найдена")


@app.route('/noauthorized')
def no_authorized():
    resp = make_response(render_template("no_authorized.html", menu=dbase.getMenu(),
                                         title="Авторизуйтесь"))
    if request.args.get('next'):
        resp.set_cookie('next', request.args.get('next'))
    return resp


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "link_db"):
        g.link_db.close()


def get_news(keyword):
    apiKey = "9b48fe6447fe4d0383f50e30af3198b9"
    text = ""
    try:
        newsapi = NewsApiClient(apiKey)
        news = newsapi.get_everything(q=keyword, language='ru', page_size=15)
    except Exception as e:
        news = {}
        print(f'Ошибка запроса новостей. {e}')
    news_articles = news['articles']
    print(news_articles[0])
    try:
        for i, value in enumerate(news_articles):
            res = dbase.addPost(value['source']['name'], value['author'], value['title'], value['description'],
                                value['url'],
                                value['urlToImage'], text)
    except Exception as e:
        print(f'Ошибка записи новости в БД. {e}')
    return "done"


if __name__ == "__main__":
    app.run(debug=True)