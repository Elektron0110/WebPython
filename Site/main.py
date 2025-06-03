import subprocess as sp
import threading as th

files = ['Broker', 'Site']


def launcher(file):
	program = th.Thread(target=sp.run, args=('python', file, {'check': False}))
	program.start()


for name in files:
	thread = th.Thread(target=launcher, args=(name+'.py'))
	thread.run()