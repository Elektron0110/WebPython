import json, os
import paho.mqtt.client as mqtt
from datetime import datetime

# Параметры подключения
BROKER_HOST = "m6.wqtt.ru"
BROKER_PORT = 19310
USERNAME = "Qwerty"
PASSWORD = "1234567890"
data = {}
datae = {}


# Callback при подключении к брокеру
def on_connect(client, userdata, flags, rc):
	if not os.path.isdir('graph'): os.mkdir('graph')
	if os.path.isfile(f'graph/{datetime.today().strftime('%Y.%m.%d')}'):
		global datae
		datae = json.loads(open(f'graph/{datetime.today().strftime('%Y.%m.%d')}').read())
	if rc == 0:
		client.subscribe('#')
	else:
		print(f"Ошибка подключения (код: {rc})")


# Callback при получении сообщения
def on_message(client, userdata, msg):
	topic:str = msg.topic
	if topic.startswith(('Um', 'Temperature', 'Humidity', 'Pressure')):
		um = topic[:3] if topic.startswith('Um') else 'Um1'
		topic = 'Temperature' if topic[3:] == 'T' else (
				'Humidity' if topic[3:] == 'H' else (
				'Pressure' if topic[3:] == 'P' else topic))
		if datae:
			if int(list(datae.keys())[-1][-7:].replace(':', '')) > int(datetime.now().strftime('%H%M%S')):
				datae.clear()
		if um not in data.keys():
			data[um] = {}
		if datetime.now().strftime('%Y.%m.%d %H:%M:%S') not in datae.keys():
			datae[datetime.now().strftime('%Y.%m.%d %H:%M:%S')] = {}
		data[um][topic] = msg.payload.decode()
		datae[datetime.now().strftime('%Y.%m.%d %H:%M:%S')][msg.topic] = msg.payload.decode()
	open('data', 'w').write(str(data).replace("'", '"'))
	open(f'graph/{datetime.today().strftime('%Y.%m.%d')}', 'w').write(str(datae).replace("'", '"'))


# Создаем клиента
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

try:
	client.connect(BROKER_HOST, BROKER_PORT, 60)
	client.loop_forever()
except Exception as e:
	print(e)
