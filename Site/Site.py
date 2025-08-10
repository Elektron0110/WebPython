"""Модуль, отвечающий за работу сервера."""
import os
import random
from flask import Flask
from flask import render_template, request, session, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from searcher import fly
from alice import bp, json
from requests import post

slicer = r'\|/'
name = 'Программа'

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["EXPLAIN_TEMPLATE_LOADING"] = True
app.register_blueprint(bp)

if not os.path.isdir('Site'):
	os.mkdir('Site')
	open('Site/log', 'w').write('Start.')
if not os.path.isdir('Site/applications'):
	os.mkdir('Site/applications')

# -------------------------------------------------------------

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Site.db'
app.config['SQLALCHEMY_BINDS'] = {
	'mail':        'sqlite:///Mail.db'
}
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
		if MUsers.query.filter_by(email=k.get('email', '')).first() is None:
			mu = MUsers(email=k.get('email', ''), date=datetime.today())
			db.session.add(mu)
			db.session.commit()
			rec = MUsers.query.filter_by(email=k.get('email', '')).first()
			mm = MMess(recipient=rec.id, topic='Добро пожаловать в Почту.',
			  text='Добро пожаловать в Почту. Почта - мой новый проект.', date=datetime.today())
			db.session.add(mm)
			db.session.commit()


def new_application(**k):
	with app.app_context():
		ap = Applications(email=k.get('email', ''), lines=k.get('line', ''), way=k.get('way', ''),
		                  number=k.get('num', ''), date=k.get('date', ''))
		db.session.add(ap)
		db.session.commit()


new_user(email='example@mail.ru', password='', s='', f='System', t='',
         tel='+0 (000) 00-00-00', b_day='00-00-00', id=-1)
new_user(email='s762672@ya.ru', password='Alex', s='Шульган', f='Алексей', t='Владимирович',
         tel='+7 (904) 333-55-37', b_day='2011-10-01')
new_user(email='test@test', password='Bug', s='Тестов', f='Тест', t='Тестович',
         tel='+0 (123) 456-78-90', b_day='0000-00-00')

# -------------------------------------------------------------

app.secret_key = os.urandom(24)
open('Site/log', 'a').write(f'\nStart at {datetime.now().strftime("%d.%m.%Y %H:%M")}.')
admins = ['s762672@ya.ru', 'test@test']


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


@app.route('/Ums')
def sr():
	if os.path.isfile('data'):
		import json
		text = ''
		data: dict[str, dict[str, str]] = json.loads(open('data', 'r').read())
		for um in data:
			text += um+': '
			for k in data[um]:
				text += f'{k}: {data[um][k]}, '
			text = text[:-2]+'.\n'
		return '<meta http-equiv="refresh" content="60">'+text.replace('\n', '<br>')
	else: return 'Запустите "Брокер" для работы данной вкладки.'

mname = 'Почта'

def get_messages(t = True):
	with app.app_context():
		mu = MUsers.query.filter_by(email=session['email']).first()
		mms = MMess.query.filter_by(recipient=mu.id).all()
		mm = []
		for m in mms:
			text = ''
			mus = MUsers.query.filter_by(id=m.sender).first()
			mue = str(mus).split(' | ')[1] if mus else 'System'
			mu = UserInfo.query.filter_by(email=mue).first() if mus else 'System'
			mu = mu.f if mus else 'System'
			if t:
				for i in range(len(m.text)):
					if i < 20:
						text += m.text[i]
				text += '...'
			else:
				text = m.text
			mm.append((m.id, mu, m.topic, text, m.date.strftime('%d.%m.%Y %H:%M')))
		return mm

def get_out_messages(t = True):
	with app.app_context():
		mu = MUsers.query.filter_by(email=session['email']).first()
		mms = MMess.query.filter_by(sender=mu.id).all()
		mm = []
		for m in mms:
			text = ''
			mus = MUsers.query.filter_by(id=m.recipient).first()
			mue = str(mus).split(' | ')[1] if mus else 'Неизвестный пользователь'
			mu = UserInfo.query.filter_by(email=mue).first() if mus else 'Неизвестный пользователь'
			mu = mu.f if mus else 'Неизвестный пользователь'
			if t:
				for i in range(len(m.text)):
					if i < 20:
						text += m.text[i]
				text += '...'
			else:
				text = m.text
			mm.append((m.id, mu, m.topic, text, m.date.strftime('%d.%m.%Y %H:%M')))
		return mm

@app.route('/mail', methods=['GET', 'POST'])
def mmain():
	if request.method == 'GET':
		if 'user' in session:
			return render_template('MLK.html', name=mname, session=session, messes=get_messages())
		else:
			return render_template('Mlogin.html')
	if request.method == 'POST':
		thing = request.form['thing']
		if thing in ['login', 'register']:
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
					return render_template('MLK.html', name=mname, session=session, messes=get_messages())
				else:
					print(password, u.password)
					return 'Password in invalid.'
			else:
				return render_template('Mregister.html',
									email=email,
									password=password,
									date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'))
		else:
			if 'user' in session:
				return render_template('MLK.html', name=mname, session=session, messes=get_messages())
			else:
				return render_template('Mlogin.html')

@app.route('/mail/mess/<id>')
def see(id):
	if 'user' in session:
		mms = get_messages(False)+get_out_messages(False)
		ids = [mm[0] for mm in mms]
		if int(id) in ids:
			mm = mms[ids.index(int(id))]
			mess = f'''<title>{mm[2]}</title>
От: {mm[1]}<br>
Тема: {mm[2]}<br>
Текст письма: {mm[3]}<br>
Время: {mm[4]}<br>
<a href="../del/{id}" title="Сообщение удалится у всех связанных с ним пользователей.">Удалить сообщение</a>'''
			return str(mess)
		else:
			return redirect('/mail')
	else:
		return redirect('/mail')

@app.route('/mail/new/', methods=['GET', 'POST'])
def mnewmess():
	if request.method == 'GET':
		if 'user' in session:
			return render_template('Mwriter.html')
		else:
			return render_template('Mlogin.html')
	if request.method == 'POST':
		recipient = request.form['recipient'] if request.form['recipient'] else 's762672@ya.ru'
		topic = request.form['topic'] if request.form['topic'] else 'Без темы'
		text = request.form['text']
		with app.app_context():
			rec = MUsers.query.filter_by(email=recipient).first()
			sen = MUsers.query.filter_by(email=session['email']).first()
			mm = MMess(recipient=rec.id if rec else 0, topic=topic, text=text, date=datetime.today(), sender=sen.id)
			db.session.add(mm)
			db.session.commit()
		return redirect('/mail')

@app.route('/mail/out')
def moutmess():
	if 'user' in session:
		return render_template('MLK.html', name=mname, session=session, messes=get_out_messages())
	else:
		return render_template('Mlogin.html')

@app.route('/mail/answer/<id>')
def answer(id):
	id = int(id)
	if 'user' in session:
		mms = get_messages(False)+get_out_messages(False)
		ids = [mm[0] for mm in mms]
		if int(id) in ids:
			mess = MMess.query.filter_by(id=id).first()
			rid = mess.sender
			topic = mess.topic
			mus = MUsers.query.filter_by(id=int(rid)).first()
			email = mus.email #str(mus).split(' | ')[1]
			return render_template('Mwriter.html', rec=email, top=topic)
		else:
			return redirect('/mail')
	else:
		return redirect('/mail')

@app.route('/mail/del/<id>')
def dmail(id):
	print(id)
	id = int(id)
	if 'user' in session:
		print(True)
		mms = get_messages(False)+get_out_messages(False)
		ids = [mm[0] for mm in mms]
		if int(id) in ids:
			print(True)
			with app.app_context():
				letter = MMess.query.filter_by(id=int(id)).first()
				print(letter, type(letter))
				db.session.delete(letter)
				db.session.commit()
			return redirect('/mail')
		else:
			return redirect('/mail')
	else:
		return redirect('/mail')

@app.route('/flight', methods=['GET', 'POST'])
def Flight ():
	if request.method == 'POST':
		print('Fl',request.form['flight'])
		return fly(request.form['flight'])
	else:
		return render_template('Fly.html')

@app.route('/down', methods=['GET', 'POST'])
def Down ():
	return render_template('down.html')

@app.route('/down/<file>', methods=['GET', 'POST'])
def Download (file):
	return send_from_directory('down', file+'.exe')

@app.route('/train', methods=['GET', 'POST'])
def trains():
	stations = {
		2004001: 'СПб (Московский)',
		2006004: 'Мск (Ленинградский)'
	}
	headers = {"Accept": "application/json, text/javascript, */*; q=0.01",
			   "Accept-Encoding": "gzip, deflate, br",
			   "Accept-Language": "ru",
			   "Connection": "keep-alive",
			   "Content-Length": "94",
			   "Content-Type": "application/json; charset=UTF-8",
			   "Host": "www.rzd.ru",
			   "Origin": "https://www.rzd.ru",
			   "Referer": "https://www.rzd.ru/ru/9278",
			   "sec-ch-ua": "'Not_A Brand';v='99', 'Microsoft Edge';v='109', 'Chromium';v='109'",
			   "sec-ch-ua-mobile": "?0",
			   "sec-ch-ua-platform": "'Windows'",
			   "Sec-Fetch-Dest": "empty",
			   "Sec-Fetch-Mode": "cors",
			   "Sec-Fetch-Site": "same-origin",
			   "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.140",
			   "X-KL-saas-Ajax-Request": "Ajax_Request",
			   "X-KL-safekids-Ajax-Request": "Ajax_Request",
			   "X-Requested-With": "XMLHttpRequest"}
	if request.method != 'POST':
		return render_template('TChoice.html', stations=stations)
	else:
		data = {'stationDepartureId'	: int(request.form['stationDepartureId']),
				'stationArrivalId'		: int(request.form['stationArrivalId']),
				'departure'				: request.form.get('departure', True),
				'date'					: datetime.today().strftime("%d.%m.%Y")}
		response = post('https://www.rzd.ru/tt/train/schedule', json=data, headers=headers)
		with open('output.json', 'w') as f: json.dump(response.json(), f)
		return render_template('TSee.html', trains=response.json()['trains'])

if os.path.isdir('C:'):
	"""Функция, запускающая работу сервера."""
	import webbrowser

	date = '9999' #datetime.now().strftime("%H%M")
	#webbrowser.open_new_tab('http://127.0.0.1:{}/'.format(date))
	app.run(port=int(date))
