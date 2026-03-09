"""Модуль, отвечающий за работу сервера."""
import os, random, new_broker, json, qrcode
from flask import Flask
from flask import render_template, request, session, redirect, send_from_directory, abort, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from requests import post, get
from alf import alf
from my_lib.Python.new import file_to_list as ftl

slicer = r'\|/'
name = 'Alexis'
start = -100

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["EXPLAIN_TEMPLATE_LOADING"] = True
app.register_blueprint(new_broker.app)

open('Alexis.log', 'a', encoding='utf-8').write(
		f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  "Server restarted."\n')

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
			  text=f'Добро пожаловать в Почту, {k.get('f', '')}. Почта - мой новый проект.',
			  date=datetime.today())
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

app.secret_key = 'YOU-NOT-KNOW-THIS-I-SURE'#os.urandom(24)
open('Site/log', 'a').write(f'\nStart at {datetime.now().strftime("%d.%m.%Y %H:%M")}.')
admins = ['s762672@ya.ru', 'test@test']
authorized = json.load(open('auth.json'))
white = False
last: dict[str, list[str]] = json.load(open('last.json'))

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
	return render_template('main.html', name=name, prompt=prompt, session=session)


@app.route('/lk', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		if 'user' in session:
			if session['email'] in admins:
							return render_template('LK.html', name=name, session=session, add={'/adm/see': 'Административная панель'})
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
				if session['email'] not in authorized: authorized[session['email']] = 1
				else: authorized[session['email']] += 1
				return redirect('lk')
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
	authorized[session['email']] -= 1
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
			session['email'], request.form['s'], request.form['f'], \
			request.form['t'], request.form['tel'], request.form['b_day']
		with app.app_context():
			u = UserInfo.query.filter_by(email=session['email'])
			u.email = email
			u.s = sn
			u.f = fn
			u.t = tn
			u.tel = tel
			u.b_day = b_day
			db.session.commit()

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


@app.route('/rss.xml')
def rss():
	global start
	'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
	<channel>
        <title>Alexis Log</title>
        <link>https://s762672.cloudpub.ru/adm/log</link>
        <description>RSS logging of my site</description>
        <language>ru-ru</language></channel></rss>'''
	items = ''
	for i in ftl('Alexis.log', sort=False)[start:][::-1]:
		s = i.split('  ')
		if len(s) > 2:
			try:
				title = s[2].replace('"', '').replace('GET ', 'GET "')
				description = f"""
Code: {s[3]},\tPerson: {s[4].split(' | ')[0]},\tIP: {s[1]},\tWeight: {s[4].split(' | ')[1]}
			"""
				pubDate = datetime.strptime(s[0], '[%d.%m.%Y %H:%M:%S]')
				items += f'''
		<item>
			<title>{title}"</title>
			<description>{description}</description>
			<pubDate>{pubDate}</pubDate>
		</item>'''
			except:
				pass
	down = '</channel></rss>'
	a = open('rss.xml', 'r', encoding='utf-8').read()[:-16]
	open('rss.xml', 'w', encoding='utf-8').write(a+items+down)
	start += (ftl('Alexis.log', sort=False).index(i)+1 -start)
	# return send_from_directory('', 'rss.xml')

@app.route('/adm/<comm>', methods=['GET', 'POST'])
def admin(comm):
	if 'user' in session:
		if session['email'] in admins:
			if comm == 'see':
				return render_template(name=name, template_name_or_list='AdmSee.html',
				                       u=AuthUser.query.all(),
				                       d=UserInfo.query.all(),
									   c=authorized,
									   l=last,
				                       a=Applications.query.all())
			elif comm == 'del':
				with app.app_context():
					email = request.form['way']
					user = AuthUser.query.filter_by(email=email).first()
					data = UserInfo.query.filter_by(email=email).first()
					db.session.delete(user)
					db.session.delete(data)
				return redirect('/lk')
			elif comm == 'update':
				email = request.form['way']
				return redirect(f'/get_acc?code=0{email}0')
			elif comm == 'log':
				date = request.args.get('date')
				if not date: date = datetime.today().strftime("%d.%m.%Y")
				dt_0 = (datetime.strptime(date, '%d.%m.%Y')-timedelta(1)).strftime('%d.%m.%Y') \
					if datetime.strptime(date, '%d.%m.%Y') >= datetime(2025, 10, 22) else None
				dt_1 = (datetime.strptime(date, '%d.%m.%Y')+timedelta(1)).strftime('%d.%m.%Y') \
					if datetime.strptime(date, '%d.%m.%Y') < datetime.today()-timedelta(1) else None
				date1 = '['+(datetime.strptime(date, '%d.%m.%Y')+timedelta(1)).strftime('%d.%m.%Y')
				f = open('Alexis.log', encoding='utf-8').read()
				return render_template('log.html', name=name, session=session, f=f[f.find(date)-1:f.find(date1)], dt_0=dt_0, dt_1=dt_1)
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


try:
	from alice import bp, fly
	app.register_blueprint(bp)
	@app.route('/flight', methods=['GET', 'POST'])
	def Flight ():
		if request.method == 'POST':
			print('Fl',request.form['flight'])
			return fly(request.form['flight'])
		else:
			return render_template(name=name, template_name_or_list='Fly.html')
except: print('INF')

@app.route('/down', methods=['GET', 'POST'])
def Down ():
	return render_template(name=name, template_name_or_list='down.html')

@app.route('/down/<file>', methods=['GET', 'POST'])
def Download (file):
	name = os.listdir('down')[[name[:name.rfind('.')] for name in os.listdir('down')].index(file)]
	if file == 'Alex':
		if request.method == 'POST':
			with app.app_context():
				if AUsers.query.filter_by(Username=request.form['name']).first() is None:
					au = AUsers(Username=request.form['name'], Password=request.form['pass'], Rating=0)
					db.session.add(au)
					db.session.commit()
			return send_from_directory('down', 'Alex.exe')
		else: return render_template(name=name, template_name_or_list='ADown.html')
	elif file in [name[:name.rfind('.')] for name in os.listdir('down')]:
		return send_from_directory('down', name)
	else:
		return 'Файл не найден.'

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
		response = post('https://www.rzd.ru/tt/train/schedule', json=data, headers=headers, timeout=10)
		with open('output.json', 'w') as f: json.dump(response.json(), f)
		return render_template(name=name, template_name_or_list='TSee.html', trains=response.json()['trains'])

@app.before_request
def limit_remote_addr():
	e: str = session.get('email')
	if e and not last.get(e): last[e] = []
	if e and '.' not in request.path:
		while len(last[e]) > 10-1:
			le = last[e]
			le.pop(0)
			last[e] = le
		last[e] += [request.path]
		json.dump(last, open('last.json', 'w'))
	if e and e not in authorized: authorized[session['email']] = 1
	if authorized != json.load(open('auth.json')):
		json.dump(authorized, open('auth.json', 'w'))
	if not os.path.isfile('static/not_blocked_ips'): open('static/not_blocked_ips', 'w').write('')
	not_blocked_ips = open('static/not_blocked_ips', 'r').read().split('\n')
	if white and request.headers.get('x-real-ip') not in not_blocked_ips:
		abort(403)  # Forbiden

@app.after_request
def after_request(response: Response):
	e: str = session.get('email')
	if e and not request.cookies.get('Name'):
		n: str = session['user'].upper()
		ltrs = {ltr for ltr in n}
		alf[' '] = ' '
		for ltr in ltrs:
			n.replace(ltr, alf[ltr])
		n = n.lower().title()
		response.set_cookie('Name', n)
	if response.calculate_content_length(): fsb: int = response.calculate_content_length()
	else:
		try:
			if not 'manifest.json' in request.path:
				if 'down/' not in request.path:
					fsb = os.path.getsize(request.path[1:])
				else: fsb = os.path.getsize(request.path[1:]+'.exe')
			else: fsb = 0
		except: fsb = 0
	fsk = fsb // 1024
	fsb = fsb % 1024
	fsm = fsk // 1024
	fsk = fsk % 1024
	open(f'Alexis.log', 'a', encoding='utf-8').write(
		f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  {request.headers.get('x-real-ip')}  "{\
			request.method} {request.path}"  {response.status[:3]}  {request.cookies.get('Name')} | {\
				fsm}MB {fsk}KB {fsb}B\n')
	return response

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

@app.route('/lets/<letter>')
def let(letter: str):
	if 'user' in session:
		prompt = session.get('user')
	else:
		prompt = 'Вход/Регистрация'
	try:
		names = json.load(open('lets.json', encoding='utf-8'))
		let = [p.split('&') for p in open('lets/'+letter, encoding='utf-8').read().replace('\n', '').split('%')]
		if let[0][0][0] == '?':
			name = let[0][0][let[0][0].find('?')+1:let[0][0].find('?', let[0][0].find('?')+1)]
			let[0].pop(0)
		else:
			name = letter
		return render_template('lets.html', name=names[name], let=let, prompt=prompt)
	except:
		if session.get('email') in admins:
			prompt = session.get('user')
			let = [p.split('&') for p in open('lets/'+letter, encoding='utf-8').read().replace('\n', '').split('%')]
			if let[0][0][0] == '?':
				name = let[0][0][let[0][0].find('?')+1:let[0][0].find('?', let[0][0].find('?')+1)]
				let[0].pop(0)
			else:
				name = letter
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
	sovrers = open('static/sovr/sovr.txt', encoding='utf-8').read().split('\n')
	if not sovrers[-1]: sovrers = sovrers[:-1]
	List = open('static/sovr/List.txt', encoding='utf-8').read().split('\n')
	if not List[-1]: List = List[:-1]
	meetings = open('static/sovr/meetings.txt', encoding='utf-8').read().split('\n')
	if not meetings[-1]: meetings = meetings[:-1]
	if 'user' in session:
		if session['email'] in sovrers+admins+['sovr@sovr']:
			nsovrers = []
			with app.app_context():
				for sovrer in sovrers:
					ui = UserInfo.query.filter_by(email=sovrer).first()
					nsovrers.append(f'{ui.s} {ui.f} {ui.t}')
			nsovrers.sort()
			return render_template('sovt.html', prompt=session.get('user'), sovr=nsovrers, list=List, meetings=meetings)
	return abort(403)

@app.route('/get_acc')
def wear():
	if request.args.get('code'):
		email = request.args.get('code')[1:-1]
		ui = UserInfo.query.filter_by(email=email).first()
		if ui:
			if session.get('email'): authorized[session['email']] -= 1
			session['user'] = f'{ui.s} {ui.f} {ui.t}'
			session['telephone'] = ui.tel
			session['birthday'] = ui.b_day
			session['email'] = ui.email
			if session['email'] not in authorized: authorized[session['email']] = 1
			else: authorized[session['email']] += 1
	return redirect('lk')

@app.route('/get_qr')
def qrcoder():
	if session.get('email'):
		response = get(
		'https://clck.ru/--',
		{'url': f'https://s762672.cloudpub.ru/get_acc?code={random.randint(0, 9)} \
			{session.get('email')}{random.randint(0, 9)}'}, timeout=10)
		img = qrcode.make(response.text)
		img.save("static/qr.png")
		return send_from_directory(app.static_folder, 'qr.png')

@app.route('/test', methods=['GET', 'POST'])
def test():
	if request.method == 'GET':
		if session.get('user'):
			return render_template('test.html', session=session)
		else: return redirect('lk')
	if request.method == 'POST':
		open('test.txt', 'a', encoding='utf-8').write(str(request.form)+'\n')
		return redirect('lk')

@app.route('/test/result')
def test_result():
	f = open('test.txt', encoding='utf-8').read().replace('ImmutableMultiDict([', '').replace('])', '') \
		.replace('), ', '|').replace('(', '').replace(')', '').replace("'", '').replace('attitude', '') \
		.replace('advice', '').replace('mood', '').replace('verb', '').replace('adjective', '') \
		.replace('verdict', '').replace('name', '').replace(', ', '').replace(',', '')
	return render_template('log.html', name=name, session=session, f=f)

@app.route('/class')
def clas(): return render_template('class.html')

@app.route('/favicon.ico')
def favicon(): return send_from_directory('static/img', 'f.ico')

if os.path.isdir('C:'):
	"""Функция, запускающая работу сервера."""
	import webbrowser

	date = '9999' #datetime.now().strftime("%H%M")
	#webbrowser.open_new_tab('http://127.0.0.1:{}/'.format(date))
	app.run(port=int(date))
