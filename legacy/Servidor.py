import socket
import threading
import sys


class Server():
    def __init__(self,host='localhost',port=4000):

        self.clientes = []
        self.port = port
        self.host = host
        print(self.host)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((str(host), int(port)))
        self.sock.listen(10)
        self.sock.setblocking(False)

        acceptConnection = threading.Thread(target=self.acceptConnection)
        processMsg = threading.Thread(target=self.processMsg)

        acceptConnection.daemon = True
        acceptConnection.start()

        processMsg.daemon = True
        processMsg.start()

        while True:
            msg = input('')
            if msg == '/close':
                self.sock.close()
                sys.exit()
            else:
                pass

    def msgReplayer(self, msg, cliente):
        for c in self.clientes:
            try:
                if c != cliente:
                    c.send(msg)
            except Exception as e:
                print('Error MR:', e)
                self.clientes.remove(c)

    def acceptConnection(self):
        print('Ouvindo no endereço',self.host,'na porta',self.port)
        while True:
            try:
                connection, address = self.sock.accept()
                connection.setblocking(False)
                self.clientes.append(connection)
                print("Usuário foi conectado")
            except Exception as e:
                pass

    def processMsg(self):
        while True:
            if len(self.clientes) > 0:
                for c in self.clientes:
                    try:
                        data = c.recv(1024)
                        if data:
                            self.msgReplayer(data, c)
                            print("Menssagem processada")
                    except Exception as e:
                        pass

s = Server(input('Defina o host de operação:'),input('Defina a porta de operação:'))