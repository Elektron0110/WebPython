"""Модуль, отвечающий за работу сервера."""
from flask import render_template, request, session, redirect, send_from_directory, abort, Response
from wsgidav.wsgidav_app import WsgiDAVApp
from datetime import datetime, timedelta
from my_lib import file_to_list as ftl
from IPs import IP_Seeker as IP
from requests import post, get
from functools import wraps
from cheroot import wsgi
import import_threading
from alf import alf
import urllib.parse
from App import *
import random
import qrcode
import json
import os


if not os.path.isdir('Site'):                     os.mkdir('Site')
if not os.path.isdir('Site/applications'):        os.mkdir('Site/applications')
if not os.path.isfile('static/not_blocked_ips'):  open('static/not_blocked_ips', 'w').write('')
if not os.path.isfile('static/blocked_ips'):      open('static/blocked_ips', 'w').write('')

if not os.path.isfile('auth.json'):               open('auth.json', 'w').write('')
if not os.path.isfile('last.json'):               open('last.json', 'w').write('')

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
    news = json.load(open('news.json', 'rb'))
    return render_template('main.html', name=name, news=news,
                           prompt=prompt, session=session)


@app.route('/lk', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user' in session:
            if session['email'] in app.config["admins"]:
                return render_template('LK.html', name=name, session=session, add={
                                       '/adm/see': 'Административная панель'})
            return render_template('LK.html', name=name, session=session)
        else:
            return render_template(
                name=name, template_name_or_list='login.html',
                prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')
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
            new_user(email=email, password=password, s=sn,
                     f=fn, t=tn, tel=tel, b_day=b_day)
        ui = UserInfo.query.filter_by(email=email).first()
        u = AuthUser.query.filter_by(email=email).first()
        if u:
            if password == u.password:
                session['user'] = f'{ui.s} {ui.f} {ui.t}'
                session['telephone'] = ui.tel
                session['birthday'] = ui.b_day
                session['email'] = ui.email
                if session['email'] not in authorized:
                    authorized[session['email']] = 1
                else:
                    authorized[session['email']] += 1
                return redirect('lk')
            else:
                print(password, u.password)
                return 'Password in invalid.'
        else:
            return render_template(name=name, template_name_or_list='register.html',
                                   email=email,
                                   password=password,
                                   date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'),
                                   prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.route('/logout')
@check_auth()
def logout():
    authorized[session['email']] -= 1
    session.pop('user')
    session.pop('telephone')
    session.pop('birthday')
    session.pop('email')
    return redirect('/')


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
        session['user'] = f"{
            request.form['s']} {
            request.form['f']} {
            request.form['t']}"
        session['telephone'] = request.form['tel']
        session['birthday'] = request.form['b_day']
        email, sn, fn, tn, tel, b_day = \
            session['email'], request.form['s'], request.form['f'], \
            request.form['t'], request.form['tel'], request.form['b_day']
        with app.app_context():
            UserInfo.query.filter(UserInfo.email == email).update({
                UserInfo.email: email, UserInfo.s: sn, UserInfo.f: fn, UserInfo.t: tn,
                UserInfo.tel: tel, UserInfo.b_day: b_day})
            db.session.commit()

        return redirect('/')


@app.route('/new', methods=['GET', 'POST'])
@check_auth()
def new():
    if request.method == 'GET':
        return render_template(name=name, template_name_or_list='xxx.html',
                               session=session,
                               date=(datetime.today() - timedelta(days=365) * 18).strftime('%Y-%m-%d'))
    elif request.method == 'POST':
        if request.form['type'] == 'check':
            session['user'] = f"{
                request.form['s']} {
                request.form['f']} {
                request.form['t']}"
            session['telephone'] = request.form['tel']
            session['birthday'] = request.form['b_day']
            sn, fn, tn, tel, b_day = \
                request.form['s'], request.form['f'], \
                request.form['t'], request.form['tel'], request.form['b_day']
            u = UserInfo.query.filter_by(email=session['email']).first()
            u.s, u.f, u.t, u.tel, u.b_day = sn, fn, tn, tel, b_day
            return render_template(
                name=name, template_name_or_list='yyy.html', session=session)
        elif request.form['type'] == 'input':
            lines = request.form['lines']
            way = request.form['way']
            text = request.form['text']
            print(request.files['fileInput'])
            number = random.randint(1000, 9999)
            today = datetime.today()
            # open(f'Site/applications/new={number}', 'w').write(text)
            request.files['fileInput'].save(f'Site/applications/new={number}')
            new_application(
                email=session['email'], line=lines, way=way, num=number, date=today)
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
    for i in ftl('Alexis.log', sort=False)[start:]:
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
            except BaseException:
                pass
    down = '</channel></rss>'
    a = open('rss.xml', 'r', encoding='utf-8').read()[:-16]
    open('rss.xml', 'w', encoding='utf-8').write(a + items + down)
    start += (ftl('Alexis.log', sort=False).index(i) + 1 - start)
    open('start.helpfile', 'w').write(str(start))
    return send_from_directory('', 'rss.xml')


@app.route('/adm/log/<comm>', methods=['GET', 'POST'])
@check_auth(True)
def adminlog(comm):
    if f'{comm}.log' in os.listdir():
        date = request.args.get('date')
        if not date:
            date = datetime.today().strftime("%d.%m.%Y")
        dt_0 = (datetime.strptime(date, '%d.%m.%Y') - timedelta(1)).strftime('%d.%m.%Y') \
            if datetime.strptime(date, '%d.%m.%Y') >= datetime(2025, 10, 22) else None
        dt_1 = (datetime.strptime(date, '%d.%m.%Y') + timedelta(1)).strftime('%d.%m.%Y') \
            if datetime.strptime(date, '%d.%m.%Y') < datetime.today() - timedelta(1) else None
        date1 = '[' + (datetime.strptime(date, '%d.%m.%Y') +
                        timedelta(1)).strftime('%d.%m.%Y')
        f = open(f'{comm}.log', encoding='utf-8').read()
        return render_template('log.html', name=name, session=session, f=f[f.find(
            date) - 1:f.find(date1)], dt_0=dt_0, dt_1=dt_1)
    else:
        abort(404)


@app.route('/adm/IP/<ip>', methods=['GET'])
@check_auth(True)
def adminip(ip):
    return open(f'IPs/{ip}', 'r').read() if os.isfile(f'IPs/{ip}') else abort(404)


@app.route('/adm/<comm>', methods=['GET', 'POST'])
@check_auth(True)
def admin(comm):
    if comm == 'see':
        return render_template(name=name, template_name_or_list='AdmSee.html',
                               session=session,
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
        if not date:
            date = datetime.today().strftime("%d.%m.%Y")
        dt_0 = (datetime.strptime(date, '%d.%m.%Y') - timedelta(1)).strftime('%d.%m.%Y') \
            if datetime.strptime(date, '%d.%m.%Y') >= datetime(2025, 10, 22) else None
        dt_1 = (datetime.strptime(date, '%d.%m.%Y') + timedelta(1)).strftime('%d.%m.%Y') \
            if datetime.strptime(date, '%d.%m.%Y') < datetime.today() - timedelta(1) else None
        date1 = '[' + (datetime.strptime(date, '%d.%m.%Y') +
                        timedelta(1)).strftime('%d.%m.%Y')
        f = open('Alexis.log', encoding='utf-8').read()
        return render_template('log.html', name=name, session=session, f=f[f.find(
            date) - 1:f.find(date1)], dt_0=dt_0, dt_1=dt_1)
    elif comm == 'IP':
        r = ''
        for f in os.listdir('IPs'):
            r += f'<a href="IP/{f}">{f}</a><br>'
        return r
    else:
        return abort(404)


mname = 'Почта'


@app.route('/mail', methods=['GET', 'POST'])
def mmain():
    if request.method == 'GET':
        if 'user' in session:
            return render_template(
                'MLK.html', name=mname, session=session, messes=get_messages())
        else:
            return render_template(
                name=mname, template_name_or_list='Mlogin.html')
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
                new_user(email=email, password=password, s=sn,
                         f=fn, t=tn, tel=tel, b_day=b_day)
            ui = UserInfo.query.filter_by(email=email).first()
            u = AuthUser.query.filter_by(email=email).first()
            if u:
                if password == u.password:
                    session['user'] = f'{ui.s} {ui.f} {ui.t}'
                    session['telephone'] = ui.tel
                    session['birthday'] = ui.b_day
                    session['email'] = ui.email
                    return render_template(
                        'MLK.html', name=mname, session=session, messes=get_messages())
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
                return render_template(
                    'MLK.html', name=mname, session=session, messes=get_messages())
            else:
                return render_template(
                    name=mname, template_name_or_list='Mlogin.html')


@app.route('/mail/mess/<id>')
@check_auth(link='/mail')
def see(id):
    mms = get_messages(False) + get_out_messages(False)
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
        return abort(404)


@app.route('/mail/new/', methods=['GET', 'POST'])
def mnewmess():
    if request.method == 'GET':
        if 'user' in session:
            return render_template(
                name=mname, template_name_or_list='Mwriter.html')
        else:
            return render_template(
                name=mname, template_name_or_list='Mlogin.html')
    if request.method == 'POST':
        recipient = request.form['recipient'] if request.form['recipient'] else 's762672@ya.ru'
        topic = request.form['topic'] if request.form['topic'] else 'Без темы'
        text = request.form['text']
        with app.app_context():
            rec = MUsers.query.filter_by(email=recipient).first()
            sen = MUsers.query.filter_by(email=session['email']).first()
            mm = MMess(recipient=rec.id if rec else 0, topic=topic,
                       text=text, date=datetime.today(), sender=sen.id)
            db.session.add(mm)
            db.session.commit()
        return redirect('/mail')


@app.route('/mail/out')
@check_auth(link='/mail')
def moutmess():
    return render_template('MLK.html', name=mname, session=session, messes=get_out_messages())


@app.route('/mail/answer/<id>')
@check_auth(link='/mail')
def answer(id):
    id = int(id)
    mms = get_messages(False) + get_out_messages(False)
    ids = [mm[0] for mm in mms]
    if int(id) in ids:
        mess = MMess.query.filter_by(id=id).first()
        rid = mess.sender
        topic = mess.topic
        mus = MUsers.query.filter_by(id=int(rid)).first()
        email = mus.email  # str(mus).split(' | ')[1]
        return render_template(
            name=mname, template_name_or_list='Mwriter.html', rec=email, top=topic)
    else:
        return abort(404)


@app.route('/mail/del/<id>')
@check_auth(link='/mail')
def dmail(id):
    print(id)
    id = int(id)
    print(True)
    mms = get_messages(False) + get_out_messages(False)
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
        return abort(404)


try:
    from alice import bp, fly
    app.register_blueprint(bp)

    @app.route('/flight', methods=['GET', 'POST'])
    def Flight():
        if request.method == 'POST':
            print('Fl', request.form['flight'])
            return fly(request.form['flight'])
        else:
            return render_template(name=name, template_name_or_list='Fly.html',
                                   prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')
except Exception as e:
    print('INF')


@app.route('/down', methods=['GET', 'POST'])
def Down():
    return render_template(name=name, template_name_or_list='down.html',
                           prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.route('/down/<file>', methods=['GET', 'POST'])
def Download(file):
    if True in [file in f for f in os.listdir('down')]:
        name = os.listdir('down')[[name[:name.rfind('.')]
                                for name in os.listdir('down')].index(file)]
        if file == 'Alex':
            if request.method == 'POST':
                with app.app_context():
                    if AUsers.query.filter_by(
                            Username=request.form['name']).first() is None:
                        au = AUsers(
                            Username=request.form['name'], Password=request.form['pass'], Rating=0)
                        db.session.add(au)
                        db.session.commit()
                return send_from_directory('down', 'Alex.exe')
            else:
                return render_template(
                    name=name, template_name_or_list='ADown.html',
                    prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')
        else:
            return send_from_directory('down', name)
    else:
        return ('Файл не найден.', 404)


@app.route('/train', methods=['GET', 'POST'])
def trains():
    stations = {}
    file = open('static/stations', 'r', encoding='utf-8').read()
    for line in file.split('\n'):
        if line:
            stations[line.split('\t')[0]] = line.split('\t')[-1]
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
        return render_template(
            name=name, template_name_or_list='TChoice.html', stations=stations,
            min=(datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d"),
            today=datetime.now().strftime("%Y-%m-%d"),
            max=(datetime.now()+timedelta(days=6)).strftime("%Y-%m-%d"),
            prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')
    else:
        data = {'stationDepartureId': stations[request.form['stationDepartureId']],
                'stationArrivalId': stations[request.form['stationArrivalId']],
                'departure': True, # bool(request.form.get('departure', False)),
                'date': datetime.strptime(request.form.get('date'), "%Y-%m-%d").strftime("%d.%m.%Y")}
        response = post('https://www.rzd.ru/tt/train/schedule',
                        json=data, headers=headers, timeout=10)
        with open('output.json', 'w') as f:
            json.dump(response.json(), f, ensure_ascii=False)
        return render_template(
            name=name, template_name_or_list='TSee.html', trains=response.json()['trains'],
            prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.before_request
def limit_remote_addr():
    e: str = session.get('email')
    if e and not last.get(e):
        last[e] = []
    if e and '.' not in request.path:
        while len(last[e]) > 10 - 1:
            le = last[e]
            le.pop(0)
            last[e] = le
        last[e] += [request.path]
        json.dump(last, open('last.json', 'w'))
    if e and e not in authorized:
        authorized[session['email']] = 1
    if authorized != json.load(open('auth.json')):
        json.dump(authorized, open('auth.json', 'w'))
    if white and request.headers.get('x-real-ip') not in not_blocked_ips:
        abort(403)  # Forbiden
    if request.headers.get('x-real-ip') in blocked_ips:
        abort(403, 'You can not open this website.')


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
    if response.calculate_content_length():
        fsb: int = response.calculate_content_length()
    else:
        try:
            if not 'manifest.json' in request.path:
                if 'down/' not in request.path:
                    fsb = os.path.getsize(request.path[1:])
                else:
                    fsb = os.path.getsize(request.path[1:] + '.exe')
            else:
                fsb = 0
        except BaseException:
            fsb = 0
    fsk = fsb // 1024
    fsb = fsb % 1024
    fsm = fsk // 1024
    fsk = fsk % 1024
    ip = request.headers.get('x-real-ip')
    if f'{ip}.IP' not in os.listdir('IPs'):
        IP(ip).Seek()
    if f'{ip}.HEAD' not in os.listdir('HEADs') and request.path == '/':
        open(f'HEADs/{ip}.HEAD', 'w').write(str(request.headers))
    if request.path.startswith(('/loader', '/video', '/films')):
        llogging.log(f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  {ip}  "{
            request.method} {request.full_path}"  {response.status[:3]}  {request.cookies.get('Name')}'
        )
    elif request.path.startswith(('/max', '/static/max')):
        mlogging.log(f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  {ip}  "{
            request.method} {request.full_path}"  {response.status[:3]}  {request.cookies.get('Name')}',
            slice=' | ', fw=f'{fsm}MB {fsk}KB {fsb}B')
    else:
        logging.log(f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  {ip}  "{
            request.method} {request.full_path}"  {response.status[:3]}  {request.cookies.get('Name')}',
            slice=' | ', fw=f'{fsm}MB {fsk}KB {fsb}B')
    return response


@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/lets')
def lets():
    names = json.load(open('lets.json', encoding='utf-8'))
    let = {names[file] if file in names.keys(
    ) else file: file for file in os.listdir('lets')}
    return render_template('all_lets.html', let=let,
                           prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.route('/lets/<letter>')
def let(letter: str):
    prompt = session.get('user') if 'user' in session else 'Вход/Регистрация'
    if letter not in os.listdir('lets'): return abort(404)
    try:
        names = json.load(open('lets.json', encoding='utf-8'))
        let = [p.split('&') for p in open(
            'lets/' + letter, encoding='utf-8').read().replace('\n', '').split('%')]
        if let[0][0][0] == '?':
            name = let[0][0][let[0][0].find(
                '?') + 1:let[0][0].find('?', let[0][0].find('?') + 1)]
            let[0].pop(0)
        else:
            name = letter
        return render_template(
            'lets.html', name=names[name], let=let, prompt=prompt)
    except BaseException:
        if session.get('email') in app.config["admins"]:
            prompt = session.get('user')
            let = [p.split('&') for p in open(
                'lets/' + letter, encoding='utf-8').read().replace('\n', '').split('%')]
            if let[0][0][0] == '?':
                name = let[0][0][let[0][0].find(
                    '?') + 1:let[0][0].find('?', let[0][0].find('?') + 1)]
                let[0].pop(0)
            else:
                name = letter
            return render_template(
                'lets.html', name=name, let=let, prompt=prompt)
        else:
            return abort(403, 'This page only for administrators.')


@app.route('/mess/<q>', methods=['GET', 'POST'])
def am_checker(q):
    if q == 'check':
        with app.app_context():
            return '{' + f'"check": "{
                (AUsers.query.filter_by(Username=request.form["name"]).first(
                ).Password == request.form["pass"])
                if AUsers.query.filter_by(Username=request.form["name"]).first() else False}"' + '}'
    elif q == 'get':
        if request.method == 'POST':
            with app.app_context():
                if AUsers.query.filter_by(Username=request.form["name"]).first(
                ).Password == request.form["pass"]:
                    mm = []
                    for m in AMesses.query.filter_by(
                            Recipient=request.form['name']).all():
                        sender = AUsers.query.filter_by(
                            Username=request.form["name"]).first()
                        mm.append((m.id, m.Sender, m.Text, m.Type,
                                   m.Context, sender.Rating))
                    return json.dumps(mm)
                else:
                    return json.dumps('???')
        else:
            return json.dumps('???')
    elif q == 'send':
        if request.method == 'GET':
            return json.dumps('???')
        else:
            with app.app_context():
                if AUsers.query.filter_by(Username=request.form["name"]).first(
                ).Password == request.form["pass"]:
                    am = AMesses(Sender=request.form['name'], Recipient=request.form['reci'], Text=request.form['text'],
                                 Type=request.form['type'], Context=request.form['cont'])
                    db.session.add(am)
                    db.session.commit()
                    return 'OK'
                else:
                    return json.dumps('???')
    elif q == 'bad':
        if request.method == 'GET':
            return json.dumps('???')
        else:
            with app.app_context():
                AUsers.query.filter_by(Username=request.form["name"]).first(
                ).Rating -= int(request.form["count"])
                # db.session.add(am)
                db.session.commit()
                return 'OK'
    else:
        return json.dumps('???')


@app.route('/about')
def about():
    m = urllib.parse.quote
    email = 's762672@ya.ru'
    topic = m(f'Предоложение по сайту {name}.')
    lbody = m('Опишите своё предложение и подпишитесь.')
    href=f"mailto:{email}?subject={topic}&body={lbody}"
    return render_template('about.html', email=href,
                           prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.route('/SOVR')
def sovt():
    sovrers = open('static/sovr/sovr.txt', encoding='utf-8').read().split('\n')
    if not sovrers[-1]:
        sovrers = sovrers[:-1]
    List = open('static/sovr/List.txt', encoding='utf-8').read().split('\n')
    if not List[-1]:
        List = List[:-1]
    meetings = open('static/sovr/meetings.txt',
                    encoding='utf-8').read().split('\n')
    if not meetings[-1]:
        meetings = meetings[:-1]
    if 'user' in session:
        if session['email'] in sovrers + app.config["admins"] + ['sovr@sovr']:
            nsovrers = []
            with app.app_context():
                for sovrer in sovrers:
                    ui = UserInfo.query.filter_by(email=sovrer).first()
                    nsovrers.append(f'{ui.s} {ui.f} {ui.t}')
            nsovrers.sort()
            return render_template('sovt.html', prompt=session.get(
                'user'), sovr=nsovrers, list=List, meetings=meetings)
    return abort(403)


@app.route('/get_acc')
def wear():
    if request.args.get('code'):
        email = request.args.get('code')[1:-1]
        ui = UserInfo.query.filter_by(email=email).first()
        if ui:
            if session.get('email'):
                authorized[session['email']] -= 1
            session['user'] = f'{ui.s} {ui.f} {ui.t}'
            session['telephone'] = ui.tel
            session['birthday'] = ui.b_day
            session['email'] = ui.email
            if session['email'] not in authorized:
                authorized[session['email']] = 1
            else:
                authorized[session['email']] += 1
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


@app.route('/tests')
@check_auth()
def tests():
    return render_template('all_tests.html', tests={'MBTI-тест': 'mbti', 'Про меня': 'meaning'},
                           prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.route('/test/<test>', methods=['GET', 'POST'])
@check_auth()
def test(test: str):
    if request.method == 'GET':
        return render_template(f'test_{test}.html', session=session, prompt=session.get('user'))
    else:
        res: list[dict[str, str]] = json.load(open(f'tests/{test}.txt', 'rb'))
        res.append({key: request.form['key'] for key in request.form})
        
        json.dump(res, open(f'tests/{test}.txt', 'a', encoding='utf-8'), ensure_ascii=False)

        if test == 'mbti':
            with app.app_context():
                print(request.form['result'])
                UserInfo.query.filter(UserInfo.email == session['email']).update({
                    UserInfo.MBTI: request.form['result']})
                db.session.commit()
        return redirect('lk')


@app.route('/test/<test>/result')
@check_auth()
def test_result(test: str):
    f = open(f'tests/{test}.txt', encoding='utf-8').read().replace('ImmutableMultiDict([', '').replace('])', '') \
        .replace('), ', '|').replace('(', '').replace(')', '').replace("'", '').replace('attitude', '') \
        .replace('advice', '').replace('mood', '').replace('verb', '').replace('adjective', '') \
        .replace('verdict', '').replace('name', '').replace(', ', '').replace(',', '')
    return render_template('log.html', name=name, session=session, f=f)


@app.route('/class')
def clas():
    return render_template('class.html',
                           prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.route('/favicon.ico')
def favicon(): return send_from_directory('static/img', 'f.ico')


@app.route('/loader/twitch/<chanel>/<t>/<id>')
def twitchloader(id: int, chanel: str, t: str):
    vurl = f'https://twitch.tv/{chanel}/{t}/{id}'
    import_threading.load(vurl)
    return redirect('/video')


@app.route('/loader/twitch/<chanel>')
def twitch(chanel: str):
    vurl = f'https://twitch.tv/{chanel}'
    import_threading.load(vurl)
    return redirect('/video')


@app.route('/loader/<chanel>/<smth>')
def loader(smth: str, chanel: str):
    if chanel == 'vk':
        vurl = f'https://vkvideo.ru/video-{smth}'
    else:
        vurl = f'https://rutube.ru/video/{smth}'
    import_threading.load(vurl)
    return redirect('/video')


h = ftl('links.helpfile', sort=False)[0]


@app.route('/video')
def video():
    r = ''
    for f in os.listdir(h):
        if os.path.isdir(f'{h}/{f}'):
            r += f'<a href="video/{f}"><b>{f}</b></a><br>'
        else:
            r += f'<a href="video/{f}">{f}</a>    <a href="video/{f}" download>Скачать</a><br>'
    return r


@app.route('/video/<fod>')
def videofod(fod):
    if os.path.isfile(f'{h}/{fod}'):
        return send_from_directory(h, fod)
    else:
        r = ''
        for f in os.listdir(f'{h}/{fod}'):
            if os.path.isdir(f'{h}/{fod}/{f}'):
                r += f'<a href="{fod}/{f}"><b>{f}</b></a><br>'
            else:
                r += f'<a href="{fod}/{f}">{f}</a>    <a href="video/{f}" download>Скачать</a><br>'
        return r


@app.route('/video/<directory>/<file>')
def videodirectoryfile(directory, file):
    return send_from_directory(f'{h}/{directory}', file)


j = ftl('links.helpfile', sort=False)[2]


@app.route('/films')
def films():
    r = ''
    for f in os.listdir(j):
        if os.path.isdir(f'{j}/{f}'):
            r += f'<a href="films/{f}"><b>{f}</b></a><br>'
        else:
            r += f'<a href="films/{f}">{f}</a>    <a href="video/{f}" download>Скачать</a><br>'
    return r


@app.route('/films/<fod>')
def filmsfod(fod):
    if os.path.isfile(f'{j}/{fod}'):
        return send_from_directory(j, fod)
    else:
        r = ''
        for f in os.listdir(f'{j}/{fod}'):
            if os.path.isdir(f'{j}/{fod}/{f}'):
                r += f'<a href="{fod}/{f}"><b>{f}</b></a><br>'
            else:
                r += f'<a href="{fod}/{f}">{f}</a>    <a href="video/{f}" download>Скачать</a><br>'
        return r


@app.route('/films/<directory>/<file>')
def filmsdirectoryfile(directory, file):
    return send_from_directory(f'{j}/{directory}', file)


@app.route('/ping')
def ping():
    return str(datetime.now())


@app.route('/VertDider')
@app.route('/VertDider/<url>')
def Vert_Dider(url=''):
    urls = {'IQ': 'Что измеряют IQ тесты [Veritasium].mp4',
            'PI': 'Как считали число пи [Veritasium].mp4',
            'Imaginary': 'Мнимые числа реальны 1-13 [Welch Labs].mp4',
            'AE': 'AE.png',
            'GG': 'GG.png'}
    if '.' in url: return send_from_directory(ftl('links.helpfile', sort=False)[0]+'/Vert Dider/PNG', url)
    if url: return send_from_directory(ftl('links.helpfile', sort=False)[0]+'/Vert Dider', urls[url])
    return render_template('VD.html', urls=urls, title='VertDider',
                           prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')


@app.route('/E-Code')
@app.route('/E-Code/<url>')
def E_Code(url=''):
    urls = {'DNA': 'Что показывают генетические тесты.mp4',
            'Life': 'Поиски жизни и разума во вселенной.m3u8',
            'Phusic': 'Математика физика и музыка.mp4',
            'BH': 'Чёрные дыры кротовые норы и путешествия во времени.mp4'}
    years = {'DNA': 2025,
            'Life': 2024,
            'Phusic': 2024,
            'BH': 2025}

    if '.' in url: return send_from_directory(app.static_folder, f'E-Code/PNG/{url}')
    if url: return send_from_directory(app.static_folder, f'E-Code/{urls[url]}')
    return render_template('VD.html', urls=urls, title='E-Code', years=years,
                            prompt=session.get('user') if 'user' in session else 'Вход/Регистрация')

if os.path.isdir('C:'):
    # """Функция, запускающая работу сервера."""
    # import webbrowser

    host = '0.0.0.0'
    date = 9999  # datetime.now().strftime("%H%M")
    # #webbrowser.open_new_tab('http://127.0.0.1:{}/'.format(date))
    # app.run(host=host, port=date)

    dir = ftl('links.helpfile', sort=False)[1]

    dav_config = {
        "host": host,
        "port": date,
        "provider_mapping": {
                "/webdav": dir,
        },
        "http_authenticator": {
            "domain_controller": None,
            "accept_basic": True,
            "accept_digest": False,
            "default_to_digest": False
        },
        "simple_dc": {
            "user_mapping": {
                "/webdav": True
            }
        },
        "verbose": 2,
    }

    # Создаём экземпляр WsgiDAV
    dav_app = WsgiDAVApp(dav_config)
    app.wsgi_app = WsgiDAVMiddleware(app.wsgi_app, dav_app)

    # Запускаем сервер Cheroot, который обслуживает и Flask, и WsgiDAV
    server = wsgi.Server(
        bind_addr=(host, date),
        wsgi_app=app.wsgi_app
    )
    print(f"Flask + WsgiDAV запущен: http://127.0.0.1:{date}/")
    print(f"WebDAV: http://127.0.0.1:{date}/webdav")

    print('\n\n')
    logging.log(
        f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  "Server restarted."')
    wlogging.log(
        f'[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]  "WebDav restarted."')

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nСервер остановлен.\n\n")
        server.stop()
