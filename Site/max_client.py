from flask import Blueprint as Flask
import json

TRANPORT_FILE = "max.helpfile"
DEFAULT = open('default.helpfile').readlines()[0][:-1]

app = Flask(__name__, 'new_broker')


@app.route('/max')
def max():
    max_data: dict[int, list[dict[str, str]]] = json.load(open('max_messages.json', encoding='utf-8'))
    default_chat = max_data[DEFAULT]
    return str(default_chat)


@app.route('/max/all')
def maxall():
    chats: list[dict[str, str]] = json.load(open('max_chats.json', encoding='utf-8'))
    fstring = f'<a href="/max/{chats[0]["id"]}">{chats[0]["type"]} | {chats[0]["name"]}</a>\n<br>\n'
    return fstring+'</a>\n<br>\n'.join([f'<a href="/max/{chat["id"]}">{chat["name"]}' for chat in chats[1:]])


@app.route('/max/<x>')
def maxx(x):
    open(TRANPORT_FILE,'w').write(x)
    while open(TRANPORT_FILE).read() != 'DONE': pass
    max_data: dict[int, list[dict[str, str]]] = json.load(open('max_messages.json', encoding='utf-8'))
    chat = max_data[x]
    return str(chat)
