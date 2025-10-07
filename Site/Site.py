"""Модуль, отвечающий за работу сервера."""
import os
import random
import new_broker
from flask import Flask
from flask import render_template, request, session, redirect, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from searcher import fly
from alice import bp, json
from requests import post

slicer = r'\|/'
name = 'Alexis'

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["EXPLAIN_TEMPLATE_LOADING"] = True
app.register_blueprint(bp)
app.register_blueprint(new_broker.app)

if not os.path.isdir('Site'):
	os.mkdir('Site')
	open('Site/log', 'w').write('Start.')
if not os.path.isdir('Site/applications'):
	os.mkdir('Site/applications')

# -------------------------------------------------------------------------------------------------------------

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Site.db'
app.config['SQLALCHEMY_BINDS'] = {
	'mail':			'sqlite:///Mail.db',
	'AM':			'sqlite:///AlexMess.db'
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

# -------------------------------------------------------------------------------------------------------------

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
			return render_template(name=name, template_name_or_list='login.html')
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
			return render_template(name=name, template_name_or_list='register.html',
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
		return render_template(name=name, template_name_or_list='xxx.html',
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
			return render_template(name=name, template_name_or_list='yyy.html', session=session)
		elif request.form['type'] == 'input':
			lines = request.form['lines']
			way = request.form['way']
			text = request.form['text']
			print(request.files['fileInput'])
			number = random.randint(1000, 9999)
			today = datetime.today()
			# open(f'Site/applications/new={number}', 'w').write(text)
			request.files['fileInput'].save(f'Site/applications/new={number}')
			new_application(email=session['email'], line=lines, way=way, num=number, date=today)
			return f'''Заявка отправлена.
Ориентировочная стоимость выполнения задачи: {50 * int(lines) * 2.25}₽.'''


@app.route('/adm/<comm>', methods=['GET', 'POST'])
def admin(comm):
	if 'user' in session:
		if session['email'] in admins:
			if comm == 'see':
				return render_template(name=name, template_name_or_list='AdmSee.html',
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
			return render_template(name=mname, template_name_or_list='Mlogin.html')
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
				return render_template(name=mname, template_name_or_list='Mregister.html',
									email=email,
									password=password,
									date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'))
		else:
			if 'user' in session:
				return render_template('MLK.html', name=mname, session=session, messes=get_messages())
			else:
				return render_template(name=mname, template_name_or_list='Mlogin.html')

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
<a href="../del/{id}" onclick="alert('Сообщение удалилось у всех связанных с ним пользователей.')">Удалить сообщение</a>'''
			return str(mess)
		else:
			return redirect('/mail')
	else:
		return redirect('/mail')

@app.route('/mail/new/', methods=['GET', 'POST'])
def mnewmess():
	if request.method == 'GET':
		if 'user' in session:
			return render_template(name=mname, template_name_or_list='Mwriter.html')
		else:
			return render_template(name=mname, template_name_or_list='Mlogin.html')
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
		return render_template(name=mname, template_name_or_list='Mlogin.html')

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
			return render_template(name=mname, template_name_or_list='Mwriter.html', rec=email, top=topic)
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
		return render_template(name=name, template_name_or_list='Fly.html')

@app.route('/down', methods=['GET', 'POST'])
def Down ():
	return render_template(name=name, template_name_or_list='down.html')

@app.route('/down/<file>', methods=['GET', 'POST'])
def Download (file):
	if file == 'Alex':
		if request.method == 'POST':
			with app.app_context():
				if AUsers.query.filter_by(Username=request.form['name']).first() is None:
					au = AUsers(Username=request.form['name'], Password=request.form['pass'], Rating=0)
					db.session.add(au)
					db.session.commit()
			return send_from_directory('down', 'Alex.exe')
		else: return render_template(name=name, template_name_or_list='ADown.html')
	else: 
		return send_from_directory('down', file+'.exe') if os.path.isfile(f'down/{file}.exe') else 'Файл не найден.'

@app.route('/train', methods=['GET', 'POST'])
def trains():
	stations = {}
	file = open('static/stations', 'r', encoding='utf-8').read()
	for line in file.split('\n'):
		if line: stations[line.split('\t')[0]] = line.split('\t')[-1]
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
		return render_template(name=name, template_name_or_list='TChoice.html', stations=stations)
	else:
		data = {'stationDepartureId'	: stations[request.form['stationDepartureId']],
				'stationArrivalId'		: stations[request.form['stationArrivalId']],
				'departure'				: request.form.get('departure', True),
				'date'					: datetime.today().strftime("%d.%m.%Y")}
		response = post('https://www.rzd.ru/tt/train/schedule', json=data, headers=headers)
		with open('output.json', 'w') as f: json.dump(response.json(), f)
		return render_template(name=name, template_name_or_list='TSee.html', trains=response.json()['trains'])

@app.before_request
def limit_remote_addr():
	if not os.path.isfile('static/blocked_ips'): open('static/blocked_ips', 'w').write('')
	blocked_ips = open('static/blocked_ips', 'r').read().split('\n')
	if request.remote_addr in blocked_ips:
		abort(403)  # Forbiden

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
	return send_from_directory(app.static_folder, request.path[1:])

@app.route('/Жизнь.mp4')
@app.route('/ДНК.mp4')
@app.route('/ЧД.mp4')
@app.route('/ФМ.mp4')
def e_code_from_root():
	return send_from_directory(app.static_folder, 'E-Code'+request.path)

@app.route('/lets')
def lets():
	names = json.load(open('lets.json', encoding='utf-8'))
	if 'user' in session:
		prompt = session.get('user')
	else:
		prompt = 'Вход/Регистрация'
	let = {names[file] if file in names.keys() else file: file for file in os.listdir('lets')}
	return render_template('all_lets.html', let=let, prompt=prompt)

@app.route('/lets/<name>')
def let(name):
	if 'user' in session:
		prompt = session.get('user')
	else:
		prompt = 'Вход/Регистрация'
	try:
		names = json.load(open('lets.json', encoding='utf-8'))
		let = [p.split('&') for p in open('lets/'+name, encoding='utf-8').read().replace('\n', '').split('%')]
		return render_template('lets.html', name=names[name], let=let, prompt=prompt)
	except:
		if 'user' in session:
			prompt = session.get('user')
			let = [p.split('&') for p in open('lets/'+name, encoding='utf-8').read().replace('\n', '').split('%')]
			return render_template('lets.html', name=name, let=let, prompt=prompt)
		else:
			return abort(403)

@app.route('/mess/<q>', methods=['GET', 'POST'])
def am_checker(q):
	if q == 'check':
		with app.app_context():
			return '{'+f'"check": "{
				(AUsers.query.filter_by(Username=request.form["name"]).first().Password == request.form["pass"])
				if AUsers.query.filter_by(Username=request.form["name"]).first() else False}"'+'}'
	elif q == 'get':
		if request.method == 'POST':
			with app.app_context():
				if AUsers.query.filter_by(Username=request.form["name"]).first().Password == request.form["pass"]:
					mm = []
					for m in AMesses.query.filter_by(Recipient=request.form['name']).all():
						sender = AUsers.query.filter_by(Username=request.form["name"]).first()
						mm.append((m.id, m.Sender, m.Text, m.Type, m.Context, sender.Rating))
					return json.dumps(mm)
				else: return json.dumps('???')
		else: return json.dumps('???')
	elif q == 'send':
		if request.method == 'GET': return json.dumps('???')
		else:
			with app.app_context():
				if AUsers.query.filter_by(Username=request.form["name"]).first().Password == request.form["pass"]:
					am = AMesses(Sender=request.form['name'], Recipient=request.form['reci'], Text=request.form['text'],
				  		Type=request.form['type'], Context=request.form['cont'])
					db.session.add(am)
					db.session.commit()
					return 'OK'
				else: return json.dumps('???')
	elif q == 'bad':
		if request.method == 'GET': return json.dumps('???')
		else:
			with app.app_context():
				AUsers.query.filter_by(Username=request.form["name"]).first().Rating -= int(request.form["count"])
				# db.session.add(am)
				db.session.commit()
				return 'OK'
	else: return json.dumps('???')

@app.route('/about')
def about():
	if 'user' in session:
		prompt = session.get('user')
	else:
		prompt = 'Вход/Регистрация'
	return render_template('about.html', prompt=prompt)

@app.route('/SOVR')
def sovt():
	sovrers = open('sovr.txt', encoding='utf-8').read().split('\n')
	if not sovrers[-1]: sovrers = sovrers[:-1]
	List = open('List.txt', encoding='utf-8').read().split('\n')
	if not List[-1]: List = List[:-1]
	meetings = open('meetings.txt', encoding='utf-8').read().split('\n')
	if not meetings[-1]: meetings = meetings[:-1]
	if 'user' in session:
		if session['email'] in sovrers:
			nsovrers = []
			with app.app_context():
				for sovrer in sovrers:
					ui = UserInfo.query.filter_by(email=sovrer).first()
					nsovrers.append(f'{ui.s} {ui.f} {ui.t}')
			nsovrers.sort()
			return render_template('sovt.html', prompt=session.get('user'), sovr=nsovrers, list=List, meetings=meetings)
	return abort(403)

if os.path.isdir('C:'):
	"""Функция, запускающая работу сервера."""
	import webbrowser

	date = '9999' #datetime.now().strftime("%H%M")
	#webbrowser.open_new_tab('http://127.0.0.1:{}/'.format(date))
	app.run(port=int(date))
