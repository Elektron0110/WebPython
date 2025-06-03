import os.path
import random

import paho.mqtt.client as mqtt
from keyboard import add_hotkey as ah

ex = """Um1T
um1H
Um1P
Um2T
Um2H
Um2P"""

if not os.path.isfile(f"topics"):
	open(f"topics", 'w').write(ex)

# Параметры подключения
USER = 'Брокер' + str(random.randint(100, 999))
BROKER_HOST = "m6.wqtt.ru"
BROKER_PORT = 19310
USERNAME = "Qwerty"
PASSWORD = "1234567890"
TOPICS = open('topics', 'r').read().split("\n")
data = {}


# Callback при подключении к брокеру
def on_connect(client, userdata, flags, rc):
	if rc == 0:
		print("Успешное подключение к брокеру")
		client.publish('New', f'{USER} connected.'.encode())
		# Подписываемся на все темы из списка
		for topic in TOPICS:
			client.subscribe(topic)
		client.subscribe('Sistem')
		client.subscribe(USER)
	else:
		print(f"Ошибка подключения (код: {rc})")


# Callback при получении сообщения
def on_message(client, userdata, msg):
	if msg.topic == 'Sistem' and msg.payload.decode()[:5] == '/stop':
		if msg.payload.decode() == '/stop':
			client.disconnect()
		else:
			if msg.payload.decode()[6:] == USER:
				client.disconnect()
	if msg.topic == USER:
		print(msg.payload.decode())
	data[msg.topic] = msg.payload.decode()


# Создаем клиента
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

ah('ctrl+alt+s', lambda: client.publish('Messages', f"{USER} {input('> ')}".encode()))
ah('ctrl+alt+w', lambda: print(data))

try:
	# Подключаемся и запускаем цикл обработки сообщений
	client.connect(BROKER_HOST, BROKER_PORT, 60)
	client.loop_forever()
except Exception as e:
	print(f"Ошибка подключения: {e}")
	client.disconnect()
