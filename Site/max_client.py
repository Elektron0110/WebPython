from flask import Blueprint as Flask, render_template, session, jsonify
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
    return render_template("max.html", name="Alexis", prompt=prompt, session=session)


@app.route('/max/all')
def maxall():
    chats: list[dict[str, str]] = json.load(open('max_chats.json', encoding='utf-8'))
    fstring = f'<a href="/max/{chats[0]["id"]}">{chats[0]["type"]} | {chats[0]["name"]}</a>\n<br>\n'
    return fstring+'</a>\n<br>\n'.join([f'<a href="/max/{chat["id"]}">{chat["name"]}' for chat in chats[1:]])


@app.route('/max/<x>')
def maxx(x):
    if 'user' in session:
        prompt = session.get('user')
    else:
        prompt = 'Вход/Регистрация'
    open(TRANPORT_FILE,'w').write(x)
    while open(TRANPORT_FILE).read() != 'DONE': pass
    return render_template("max.html", name="Alexis", prompt=prompt, session=session)


@app.route('/max/data/<id>')
def data(id):
    id = int(id)
    if not id: id = DEFAULT
    open(TRANPORT_FILE,'w').write(str(id))
    while open(TRANPORT_FILE).read() != 'DONE': pass
    max_data: dict[int, list[dict[str, str]]] = json.load(open('max_messages.json', encoding='utf-8'))
    return jsonify(max_data[id])
