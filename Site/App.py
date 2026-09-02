import json
import new_broker
import max_client
import urllib.parse
from my_lib import Log
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, Response, session
from wsgidav.wsgidav_app import WsgiDAVApp


app = Flask(__name__)
app.config["EXPLAIN_TEMPLATE_LOADING"] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Site.db'
app.config['SQLALCHEMY_BINDS'] = {
    'mail':  'sqlite:///Mail.db',
    'AM':    'sqlite:///AlexMess.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = open('secret.helpfile', 'r').read()
app.register_blueprint(new_broker.app)
app.register_blueprint(max_client.app)


slicer = r'\|/'
name = 'Alexis'
white = False
admins = ['s762672@ya.ru', 'test@test']

logging = Log('Alexis.log')
llogging = Log('Load.log')
wlogging = Log('WebDav.log')

start = int(open('start.helpfile', 'r').read())
not_blocked_ips = open('static/not_blocked_ips', 'r').read().split('\n')
blocked_ips = open('static/blocked_ips', 'r').read().split('\n')
authorized = json.load(open('auth.json'))
last: dict[str, list[str]] = json.load(open('last.json'))


class WsgiDAVMiddleware:
    def __init__(self, flask_app: Flask, dav_app: WsgiDAVApp,
                 dav_path: tuple[str, ...] = ("/webdav", "/:dir_browser")):
        self.decode = urllib.parse.unquote
        self.flask_app = flask_app
        self.dav_app = dav_app
        self.dav_path = dav_path

    @staticmethod
    def forbidden_response(start_response: Response):
        status = "403 Forbidden"
        response_headers = [("Content-Type", "text/plain; charset=utf-8")]
        start_response(status, response_headers)
        return [b"Forbidden"]

    def __call__(self, 
                 environ: dict[str, str], # WSGIEnvironment
                 start_response: Response):
        # Если путь начинается с /webdav, передаём запрос в WsgiDAV
        # open('env', 'w', encoding='utf-8').write(str(environ))
        if environ.get("PATH_INFO", "").startswith(self.dav_path):
            if white and environ.get("HTTP_X_REAL_IP") not in not_blocked_ips:
                self.forbidden_response(start_response)
            if environ.get("HTTP_X_REAL_IP") in blocked_ips:
                self.forbidden_response(start_response)
            wlogging.log(f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  {environ.get("HTTP_X_REAL_IP")}'
                         f'"{environ["REQUEST_METHOD"]} {self.decode(environ["REQUEST_URI"])}"')
            return self.dav_app(environ, start_response)
        # Иначе — в Flask
        return self.flask_app(environ, start_response)

# -------------------------------------------------------------------------------------------------------------

db = SQLAlchemy(app)


class AuthUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f'{self.email} | {self.password}'


class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey(
        'auth_user.email'), unique=True, nullable=False)
    s = db.Column(db.String(50))  # Фамилия
    f = db.Column(db.String(50))  # Имя
    t = db.Column(db.String(50))  # Отчество
    tel = db.Column(db.String(20))  # Телефон
    b_day = db.Column(db.String(10))  # Дата рождения
    MBTI = db.Column(db.String(5))  # Дата рождения

    def __repr__(self):
        return f'{self.email} | {self.s} | {self.f} | {self.t} | {self.tel} | {self.b_day} | {self.MBTI}'


class Applications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey(
        'auth_user.email'), nullable=False)
    lines = db.Column(db.Integer)
    way = db.Column(db.String(120))
    number = db.Column(db.Integer)
    date = db.Column(db.Date)

    def __repr__(self):
        return f'<Applications {self.email}>'


class MUsers(db.Model):
    __bind_key__ = 'mail'
    id = db.Column(db.Integer, unique=True, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'{self.id} | {self.email} | {self.date.strftime("%d.%m.%Y %H:%M")}'


class MMess(db.Model):
    __bind_key__ = 'mail'
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.Integer, nullable=False)
    sender = db.Column(db.Integer)
    topic = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'{self.sender}'


class AUsers(db.Model):
    __bind_key__ = 'AM'
    id = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(50), nullable=False, unique=True)
    Password = db.Column(db.String(50), nullable=False)
    Rating = db.Column(db.Integer, nullable=False)


class AMesses(db.Model):
    __bind_key__ = 'AM'
    id = db.Column(db.Integer, primary_key=True)
    Sender = db.Column(db.String(50), nullable=False)
    Recipient = db.Column(db.String(50), nullable=False)
    Text = db.Column(db.String(250), nullable=False)
    Type = db.Column(db.String(10), nullable=False)
    Context = db.Column(db.String(10000))

    def __repr__(self):
        return f'{self.id}%$%{self.Sender}%$%{self.Text}'


# Создание таблиц в базе данных
with app.app_context():
    db.create_all()


def new_user(**k):
    with app.app_context():
        if AuthUser.query.filter_by(email=k.get('email', '')).first() is None:
            a = AuthUser(email=k.get('email', ''),
                         password=k.get('password', ''))
            i = UserInfo(email=k.get('email', ''), s=k.get('s', ''),
                         f=k.get('f', ''), t=k.get('t', ''), tel=k.get('tel', ''),
                         b_day=k.get('b_day', ''))
            db.session.add(a)
            db.session.add(i)
            db.session.commit()
        if MUsers.query.filter_by(email=k.get('email', '')).first() is None:
            mu = MUsers(email=k.get('email', ''), date=datetime.today())
            db.session.add(mu)
            db.session.commit()
            rec = MUsers.query.filter_by(email=k.get('email', '')).first()
            mm = MMess(recipient=rec.id, topic='Добро пожаловать в Почту.',
                       text=f'Добро пожаловать в Почту, {
                           k.get(
                               'f', '')}. Почта - мой новый проект.',
                       date=datetime.today())
            db.session.add(mm)
            db.session.commit()


def new_application(**k):
    with app.app_context():
        ap = Applications(email=k.get('email', ''), lines=k.get('line', ''), way=k.get('way', ''),
                          number=k.get('num', ''), date=k.get('date', ''))
        db.session.add(ap)
        db.session.commit()


def get_messages(t=True):
    with app.app_context():
        mu = MUsers.query.filter_by(email=session['email']).first()
        mms = MMess.query.filter_by(recipient=mu.id).all()
        mm = []
        for m in mms:
            text = ''
            mus = MUsers.query.filter_by(id=m.sender).first()
            mue = str(mus).split(' | ')[1] if mus else 'System'
            mu = UserInfo.query.filter_by(
                email=mue).first() if mus else 'System'
            mu = mu.f if mus else 'System'
            if t:
                for i in range(len(m.text)):
                    if i < 20:
                        text += m.text[i]
                text += '...'
            else:
                text = m.text
            mm.append((m.id, mu, m.topic, text,
                       m.date.strftime('%d.%m.%Y %H:%M')))
        return mm


def get_out_messages(t=True):
    with app.app_context():
        mu = MUsers.query.filter_by(email=session['email']).first()
        mms = MMess.query.filter_by(sender=mu.id).all()
        mm = []
        for m in mms:
            text = ''
            mus = MUsers.query.filter_by(id=m.recipient).first()
            mue = str(mus).split(' | ')[
                1] if mus else 'Неизвестный пользователь'
            mu = UserInfo.query.filter_by(email=mue).first(
            ) if mus else 'Неизвестный пользователь'
            mu = mu.f if mus else 'Неизвестный пользователь'
            if t:
                for i in range(len(m.text)):
                    if i < 20:
                        text += m.text[i]
                text += '...'
            else:
                text = m.text
            mm.append((m.id, mu, m.topic, text,
                       m.date.strftime('%d.%m.%Y %H:%M')))
        return mm


new_user(email='example@mail.ru', password='', s='', f='System', t='',
         tel='+0 (000) 00-00-00', b_day='00-00-00', id=-1)

# -------------------------------------------------------------------------------------------------------------