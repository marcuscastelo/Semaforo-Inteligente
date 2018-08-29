import socket
import threading
import sys
import time
import pickle

class Client():

    def __init__(self,username,host='localhost',port=4000):

        self.username = str(username)
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect(((str(host)),int(port)))

        self.sock.send(pickle.dumps(self.username + ' entrou do chat\n'))
        print('Você entrou do chat.\n')

        msgListener = threading.Thread(target=self.msgListener)
        msgListener.daemon = True
        msgListener.start()

        while True:
            msg = str(input(''))
            if msg == '/leave':
                self.sock.send(pickle.dumps(self.username +' saiu do chat\n'))
                self.sock.close()
                print('Você saiu do chat.\nFinalizando o programa...')
                time.sleep(5)
                sys.exit()
            else:
                self.msgSender(msg)

    def msgListener(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if data:
                    print(pickle.loads(data))
            except Exception as e:
                pass

    def msgSender(self,msg):
        self.sock.send(pickle.dumps(self.username+': '+str(msg)))

c = Client(input('Nome de usuário: '),input('Endereço IP do servidor: '),input('Porta do servidor: '))