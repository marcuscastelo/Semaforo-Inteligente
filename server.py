from socket import *
import numpy as np
import cv2
import matplotlib.pyplot as plt
from darkflow.net.build import TFNet
# np.set_printoptions(threshold=np.nan)

socket = socket(AF_INET, SOCK_DGRAM)
socket.bind(('', 1414))
socket.settimeout(1)

addr = ("127.0.0.1", 1415)
partes1 = dict()

confidence = 0.4

option = {
	'model': 'cfg/yolo.cfg',
	'load': 'bin/yolo.weights',
	'threshold':confidence,
	'gpu': 0.7
}

tfnet = TFNet(option)

def juntaimg(d,height,width):
	print('junta 0')
	a = []
	print('junta 1')
	for i in range(8):
		a.append(d[i+1])
	print('junta 2')
	a = list(a)
	print('junta 3')
	del d
	print('junta 4')
	img = np.array(a)
	print('junta 5')
	print(height)
	print(img.shape)
	img = np.reshape(img, (height,width,3))
	print('junta 6')
	print ('Completadas 8 partes')
	return img

def predict(searchlabels, frame):
	print ('oi?')
	results = tfnet.return_predict(frame)
	print (results)
	qtds = {}
	for l in searchlabels:
		qtdp = len([i for i in results if i['label']==l and i['confidence'] > confidence])
		qtds[label] = qtdp
	return qtds

print('Waiting Connection...')
while True:  	
	try:

		message, address = socket.recvfrom(1024)
		lm = list(message)    
		#print (address,' ',lm)
		if message == b'SEM@f0rO':
			socket.sendto(b'SEM@f0rO', addr)
		if len(message) > 20:
			socket.sendto(b'OK',address)
			param = message.split(b'-')
			part = int(param[2])
			message = list(message.split(b'-')[3])
			del message[3::4]

			partes1[part] = message
			if len(partes1) == 8:
				print('nao é o dict')
				frame = juntaimg(partes1,height,width)
				print('frame ok')
				result = predict(['car','person','truck','bus'],frame)
				print('result ok')
				print (result)
			# if len(partes2) == 8:
			# 	juntaimg(partes2)
		else:
			message = str(message)
			width = message.split('-')[2]
			height = message.split('-')[3]
			
	except Exception as e:
		pass