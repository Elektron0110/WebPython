import subprocess as sp
import threading as th

files = ['Broker', 'Site']


def launcher(file):
	try:
		program = th.Thread(target=sp.run,
		                    args=('python', file),
		                    kwargs={'check': False})
		program.start()
	except Exception as e:
		print(f"Ошибка при запуске {file}: {e}")


# Основной код
threads = []
for name in files:
	file_name = name + '.py'
	thread = th.Thread(target=launcher, args=(file_name,))
	thread.start()
	threads.append(thread)

# Ждем завершения всех потоков
for t in threads:
	t.join()