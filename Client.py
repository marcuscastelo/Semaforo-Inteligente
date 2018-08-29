from socket import *
import cv2
import numpy as np
np.set_printoptions(threshold=np.nan)

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', 1415))

def mdc(num1, num2):
    resto = None
    while resto is not 0:
        resto = num1 % num2
        num1  = num2
        num2  = resto

    return num1

#while True:  
	
serverSocket.settimeout(1)
try:
	message, address = serverSocket.recvfrom(1024)    
	print (address,' ',message)
	serverSocket.sendto(b'ok',address)
except Exception as e:
	pass

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1)

sss = cv2.imread('img.jpg')
img = bytes(sss)
#message = b'test'
addr = ("127.0.0.1", 1414)

qtd = mdc(len(img),48)

a = []
unit = len(img)//qtd
for i in range(qtd):
	a.append(img[i*unit:(i+1)*unit])

#print (list(img))	
#print (np.array(list(b''.join(a))).reshape(375,500,3) == sss)

for i in a:
	clientSocket.sendto(i, addr)