import subprocess as sp

try:
	sp.run(['python', 'Broker.py'])
	sp.run(['python', 'Site.py'])
except Exception as e:
	print(e)