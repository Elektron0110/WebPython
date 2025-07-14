from multiprocessing import Process
import Broker, Site

# def launcher(num):
# 	print(num)
# 	if num == 0:
# 		try:
# 			print(num)
# 			Process(target=Broker.broker).run()
# 		except Exception as e:
# 			print(e)
# 	else:
# 		try:
# 			print(num)
# 			Process(target=Site.site).run()
# 		except Exception as e:
# 			print(e)

if __name__ == '__main__':
	for i in range(2):
		# Process(target=launcher, args=(i,)).run()
		Process(target=Broker.broker).run()
		Process(target=Site.site).run()