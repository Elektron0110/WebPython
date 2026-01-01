import json, os
import paho.mqtt.client as mqtt
from datetime import datetime

# Параметры подключения
BROKER_HOST = "m6.wqtt.ru"
BROKER_PORT = 19310
USERNAME = "Qwerty"
PASSWORD = "1234567890"
SUBS = ['Temperature', 'Humidity', 'Led', 'Pressure', 'Um2T', 'Um2H', 'Um3T', 'Um3H']
TOPICS = {'Um1': ['Temperature', 'Humidity', 'Led', 'Pressure'],
          'Um2': ['Um2T', 'Um2H'],
          'Um3': ['Um3T', 'Um3H']}
data = {}
datae = {}


# Callback при подключении к брокеру
def on_connect(client, userdata, flags, rc):
	if not os.path.isdir('graph'): os.mkdir('graph')
	if os.path.isfile(f'graph/{datetime.today().strftime('%Y.%m.%d')}'):
		global datae
		datae = json.loads(open(f'graph/{datetime.today().strftime('%Y.%m.%d')}').read())
	if rc == 0:
		for topic in SUBS:
			client.subscribe(topic)
	else:
		print(f"Ошибка подключения (код: {rc})")


# Callback при получении сообщения
def on_message(client, userdata, msg):
	topic = msg.topic
	for um in TOPICS:
		if topic in TOPICS[um]:
			topic = 'Temperature' if topic[-1:] == 'T' else ('Humidity' if topic[-1:] == 'H' else topic)
			if datae:
				if int(list(datae.keys())[-1][-5:].replace(':', '')) > int(datetime.now().strftime('%H%M')):
					datae.clear()
			if um not in data.keys():
				data[um] = {}
			if datetime.now().strftime('%Y.%m.%d %H:%M') not in datae.keys():
				datae[datetime.now().strftime('%Y.%m.%d %H:%M')] = {}
			data[um][topic] = msg.payload.decode()
			datae[datetime.now().strftime('%Y.%m.%d %H:%M')][msg.topic] = msg.payload.decode()
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
