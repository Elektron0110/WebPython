import os.path
import paho.mqtt.client as mqtt

# Параметры подключения
BROKER_HOST = "m6.wqtt.ru"
BROKER_PORT = 19310
USERNAME = "Qwerty"
PASSWORD = "1234567890"
SUBS = ['Temperature', 'Humidity']
TOPICS = {'Um1': {'Temperature', 'Humidity'}}
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
	for um, topics in TOPICS:
		if msg.topic in topics:
			data[um][msg.topic] = msg.payload.decode()
	open('data', 'w').write(str(data))


# Создаем клиента
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

try:
	# Подключаемся и запускаем цикл обработки сообщений
	client.connect(BROKER_HOST, BROKER_PORT, 60)
	client.loop_forever()
except Exception as e:
	print(f"Ошибка подключения: {e}")
	client.disconnect()
