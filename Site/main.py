import subprocess as sp
import threading as th

files = ['Broker', 'Site']


def launcher(*file):
	file = str(file).replace('(', '').replace(')', '').replace(',', '')
	file = file.replace(' ', '').replace("'", '')
	try:
		program = th.Thread(target=sp.run,
		                    args=(('python', file),),
		                    kwargs={'check': False})
		program.start()
	except Exception as e:
		print(e)


for name in files:
	file_name = name + '.py'
	thread = th.Thread(target=launcher, args=file_name)
	thread.start()