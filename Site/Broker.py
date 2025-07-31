import paho.mqtt.client as mqtt

# Параметры подключения
BROKER_HOST = "m6.wqtt.ru"
BROKER_PORT = 19310
USERNAME = "Qwerty"
PASSWORD = "1234567890"
SUBS = ['Temperature', 'Humidity', 'Led', 'Um2T', 'Um2H']
TOPICS = {'Um1': ['Temperature', 'Humidity', 'Led'],
          'Um2': ['Um2T', 'Um2H']}
data = {}


# Callback при подключении к брокеру
def on_connect(client, userdata, flags, rc):
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
			if um not in data.keys():
				data[um] = {}
			data[um][topic] = msg.payload.decode()
	open('data', 'w').write(str(data).replace("'", '"'))


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
