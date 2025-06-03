import os.path
import paho.mqtt.client as mqtt

ex = """Temperature
Humidity"""

if not os.path.isfile(f"topics"):
	open(f"topics", 'w').write(ex)

# Параметры подключения
BROKER_HOST = "m6.wqtt.ru"
BROKER_PORT = 19310
USERNAME = "Qwerty"
PASSWORD = "1234567890"
TOPICS = open('topics', 'r').read().split("\n")
data = {}


# Callback при подключении к брокеру
def on_connect(client, userdata, flags, rc):
	if rc == 0:
		for topic in TOPICS:
			client.subscribe(topic)
	else:
		print(f"Ошибка подключения (код: {rc})")


# Callback при получении сообщения
def on_message(client, userdata, msg):
	data[msg.topic] = msg.payload.decode()
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
