from flask import Blueprint as Flask, render_template, session, jsonify, request, abort
from decorators import *
import requests
import json

TRANPORT_FILE = "max.helpfile"
DEFAULT = open('default.helpfile').readlines()[0][:-1]

app = Flask(__name__, 'new_broker')


@app.route('/max')
def max():
    if 'user' in session:
        prompt = session.get('user')
    else:
        prompt = 'Вход/Регистрация'
    return render_template("max.html", name=current_app.config['name'], prompt=prompt, session=session)


@app.route('/max/all')
@check_auth(True)
def maxall():
    chats: list[dict[str, str]] = json.load(
        open('max_chats.json', encoding='utf-8'))
    of = False
    try:
        requests.get('https://ya.ru')
    except:
        of = True
    fstring = f'<a href="/max{'/of' if of else ''}/{chats[0]["id"]}">{chats[0]["type"]} | {chats[0]["name"]}</a>\n<br>\n'
    return fstring+'</a>\n<br>\n'.join([f'<a href="/max{'/of' if of else ''}/{chat["id"]}">{chat["name"]}' for chat in chats[1:]])


@app.route('/max/<x>')
def maxx(x):
    if not (x+'0')[1:].isdigit():
        return abort(400)
    if 'user' in session:
        prompt = session.get('user')
    else:
        prompt = 'Вход/Регистрация'
    open(TRANPORT_FILE, 'w').write(x)
    while open(TRANPORT_FILE).read() != 'DONE':
        pass
    return render_template("max.html", name=current_app.config['name'], prompt=prompt, session=session)


@app.route('/max/of/<x>')
def maxxoof(x):
    if not (x+'0')[1:].isdigit():
        return abort(400)
    if 'user' in session:
        prompt = session.get('user')
    else:
        prompt = 'Вход/Регистрация'
    return render_template("max.html", name=current_app.config['name'], prompt=prompt, session=session)


@app.route('/max/data/<id>')
@check_auth(True)
def data(id: str):
    if not (id+'0')[1:].isdigit():
        return abort(400)
    if not int(id):
        id = DEFAULT
    max_data: dict[str, list[dict[str, str]]] = json.load(
        open('max_messages.json', encoding='utf-8'))
    return jsonify(max_data[id])


@app.route('/max/send/<id>', methods=['POST'])
@check_auth(True)
def send_message(id: str):
    if not (id+'0')[1:].isdigit():
        return abort(400)

    data = request.get_json()
    text = data.get('text', '').strip()

    if not text:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400

    # Записываем ID чата и текст сообщения в транспортный файл для обработки Max.py
    with open(TRANPORT_FILE, 'w') as f:
        f.write(f'SEND:{id}:{text}')

    # Ждем подтверждения отправки
    timeout = 30  # таймаут в секундах
    import time
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = open(TRANPORT_FILE, 'r').read()
        if result == 'DONE':
            return jsonify({'status': 'success'})
        elif result.startswith('ERROR:'):
            pass
        time.sleep(0.1)

    return jsonify({'error': 'Таймаут отправки сообщения'}), 500
