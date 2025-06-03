import os
import random
from flask import Flask
from flask import render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

slicer = r'\|/'
name = 'Программа'

app = Flask(__name__)
app.config["DEBUG"] = True

if not os.path.isdir('Site'):
	os.mkdir('Site')
	open('Site/log', 'w').write('Start.')
if not os.path.isdir('Site/applications'):
	os.mkdir('Site/applications')

# -------------------------------------------------------------

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class AuthUser(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(80), nullable=False)
	
	def __repr__(self):
		return f'{self.email} | {self.password}'


class UserInfo(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), db.ForeignKey('auth_user.email'), unique=True, nullable=False)
	s = db.Column(db.String(50))  # Фамилия
	f = db.Column(db.String(50))  # Имя
	t = db.Column(db.String(50))  # Отчество
	tel = db.Column(db.String(20))  # Телефон
	b_day = db.Column(db.String(10))  # Дата рождения
	
	def __repr__(self):
		return f'{self.email} | {self.s} | {self.f} | {self.t} | {self.tel} | {self.b_day}'


class Applications(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), db.ForeignKey('auth_user.email'), nullable=False)
	lines = db.Column(db.Integer)
	way = db.Column(db.String(120))
	number = db.Column(db.Integer)
	date = db.Column(db.Date)
	
	def __repr__(self):
		return f'<Applications {self.email}>'


# Создание таблиц в базе данных
with app.app_context():
	db.create_all()


def new_user(**k):
	with app.app_context():
		if AuthUser.query.filter_by(email=k.get('email', '')).first() is None:
			a = AuthUser(email=k.get('email', ''), password=k.get('password', ''))
			i = UserInfo(email=k.get('email', ''), s=k.get('s', ''),
			             f=k.get('f', ''), t=k.get('t', ''), tel=k.get('tel', ''),
			             b_day=k.get('b_day', ''))
			db.session.add(a)
			db.session.add(i)
			db.session.commit()


def new_application(**k):
	with app.app_context():
		ap = Applications(email=k.get('email', ''), lines=k.get('line', ''), way=k.get('way', ''),
		                  number=k.get('num', ''), date=k.get('date', ''))
		db.session.add(ap)
		db.session.commit()


new_user(email='s762672@ya.ru', password='Alex', s='Шульган', f='Алексей', t='Владимирович',
         tel='+7 (904) 333-55-37', b_day='2011-10-01')
new_user(email='test@test', password='Bug', s='Тестов', f='Тест', t='Тестович',
         tel='+0 (123) 456-78-90', b_day='0000-00-00')

# -------------------------------------------------------------

app.secret_key = os.urandom(24)
open('Site/log', 'a').write(f'\nStart at {datetime.now().strftime("%d.%m.%Y %H:%M")}.')


# @app.errorhandler(404)
# @app.route('/')
# def to():
# 	return 'Сайт на тех.обслуживании.'

@app.route('/')
def main():
	if 'user' in session:
		prompt = session.get('user')
	else:
		prompt = 'Вход/Регистрация'
	return render_template('main.html', name=name, prompt=prompt)


@app.route('/lk', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		if 'user' in session:
			return render_template('LK.html', name=name, session=session)
		else:
			return render_template('login.html')
	if request.method == 'POST':
		thing = request.form['thing']
		email = request.form['email']
		password = request.form['password']
		if thing == 'register':
			fn = request.form['f_name']
			sn = request.form['s_name']
			tn = request.form['t_name']
			tel = request.form['tel']
			b_day = request.form['b_day']
			new_user(email=email, password=password, s=sn, f=fn, t=tn, tel=tel, b_day=b_day)
		ui = UserInfo.query.filter_by(email=email).first()
		u = AuthUser.query.filter_by(email=email).first()
		if u:
			if password == u.password:
				session['user'] = f'{ui.s} {ui.f} {ui.t}'
				session['telephone'] = ui.tel
				session['birthday'] = ui.b_day
				session['email'] = ui.email
				return render_template('LK.html', name=name, session=session)
			else:
				print(password, u.password)
				return 'Password in invalid.'
		else:
			return render_template('register.html',
			                       email=email,
			                       password=password,
			                       date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'))


@app.route('/logout')
def logout():
	session.pop('user')
	session.pop('telephone')
	session.pop('birthday')
	session.pop('email')
	return redirect('/')


@app.route('/hidden/<thing>')
def session_data(thing):
	things = {'session': str(session).replace('<', '').replace('>', ''),
	          'user': session['user'],
	          'telephone': session['telephone'],
	          'birthday': session['birthday']}
	return f"{things[thing]}"


@app.route('/update', methods=['GET', 'POST'])
def update():
	if request.method == 'GET':
		return render_template('all.html',
		                       session=session,
		                       name=name,
		                       tel=session['telephone'],
		                       birthday=session['birthday'],
		                       date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'))
	elif request.method == 'POST':
		session['user'] = f"{request.form['s']} {request.form['f']} {request.form['t']}"
		session['telephone'] = request.form['tel']
		session['birthday'] = request.form['b_day']
		email, sn, fn, tn, tel, b_day = \
			session['email'], request.form['slicer'], request.form['f'], \
			request.form['t'], request.form['tel'], request.form['b_day']
		u = AuthUser.query.filter_by(email=session['email'])
		u.info.email = email
		u.info.sn = sn
		u.info.fn = fn
		u.info.tn = tn
		u.info.tel = tel
		u.info.b_day = b_day
		return redirect('/')


@app.route('/new', methods=['GET', 'POST'])
def new():
	if request.method == 'GET':
		return render_template('xxx.html',
		                       session=session,
		                       date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'))
	elif request.method == 'POST':
		if request.form['type'] == 'check':
			session['user'] = f"{request.form['s']} {request.form['f']} {request.form['t']}"
			session['telephone'] = request.form['tel']
			session['birthday'] = request.form['b_day']
			sn, fn, tn, tel, b_day = \
				request.form['s'], request.form['f'], \
				request.form['t'], request.form['tel'], request.form['b_day']
			u = UserInfo.query.filter_by(email=session['email']).first()
			u.s, u.f, u.t, u.tel, u.b_day = sn, fn, tn, tel, b_day
			return render_template('yyy.html', session=session)
		elif request.form['type'] == 'input':
			question = {'Имя': 3, 'Инн': 2, 'Нквд': 2}
			lines = request.form['lines']
			way = request.form['way']
			text = request.form['text']
			number = random.randint(1000, 9999)
			today = datetime.today().strftime('%Y-%m-%d')
			open(f'Site/applications/new={number}', 'w').write(text)
			new_application(email=session['email'], line=lines, way=way, num=number, date=today)
			return f'''Заявка отправлена.
Ориентировочная стоимость выполнения задачи: {5 * int(lines) * int(question[way])}₽.'''


@app.route('/adm/<comm>', methods=['GET', 'POST'])
def admin(comm):
	admins = ['s762672@ya.ru', 'test@test']
	if 'user' in session:
		if session['email'] in admins:
			if comm == 'see':
				return render_template('AdmSee.html',
				                       u=AuthUser.query.all(),
				                       d=UserInfo.query.all(),
				                       a=Applications.query.all())
			elif comm == 'del':
				with app.app_context():
					email = request.form['way']
					user = AuthUser.query.filter_by(email=email).first()
					data = UserInfo.query.filter_by(email=email).first()
					db.session.delete(user)
					db.session.delete(data)
				return redirect('/lk')
			else:
				return redirect('/lk')
		else:
			return redirect('/lk')
	else:
		return redirect('/lk')


@app.route('/new')
def sr():
	return 'Раздел на стадии разработки.'


@app.route('/Ums')
def printer():
	weather = open('data', 'r').read().replace('{', '').replace('}', '')
	weather = weather.replace(', ', '\n').replace("'", '')
	return weather


if __name__ == '__main__':
	import webbrowser
	
	date = datetime.now().strftime("%H%M")
	webbrowser.open_new_tab('http://127.0.0.1:{}/'.format(date))
	app.run(port=int(date))
