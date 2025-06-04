import subprocess as sp
import threading as th

launch = True
python = ['Broker.py', 'Site.py']
exe = ['Broker.exe', 'Site.exe']

if launch:
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

	for name in python:
		thread = th.Thread(target=launcher, args=name)
		thread.start()

else:
	def launcher(*file):
		file = str(file).replace('(', '').replace(')', '').replace(',', '')
		file = file.replace(' ', '').replace("'", '')
		try:
			program = th.Thread(target=sp.run,
			                    args=(file,),
			                    kwargs={'check': False})
			program.start()
		except Exception as e:
			print(e)

	for name in exe:
		thread = th.Thread(target=launcher, args=name)
		thread.start()