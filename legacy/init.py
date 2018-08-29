import threading
import main_web
import testw
import time

def init_web_server():
	main_web.app.run()

webserver = threading.Thread(target=init_web_server)
webserver.daemon = True
webserver.start()

print('\nwaiting for flask\n*****')
time.sleep(5)



leitordeamon = threading.Thread(target=testw.start)
leitordeamon.daemon = True
leitordeamon.start()

#testw.searchlabels = [] //Retringe elementos
# r1 = testw.leitor_h.read()
#r2 = testw.leitor_v.read()

#print(r1,'--',r2)

while True:
	pass