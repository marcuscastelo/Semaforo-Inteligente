import socket
import json
import cv2
import time
import mss
import numpy as np
from darkflow.darkflow.net.build import TFNet
import signal
import sys
import utils
import threading
import imutils

class ConnectionHandler:
	def __init__(self, laddr):
		#Definição de auxiliares
		self.formatter = JsonFormatter()
		
		#Inicialização socket
		print('Inicializando módulo de conexão...')
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		print('Socket criado com sucesso.')
		self.sock.bind(laddr)
		print('Socket atribuído a',laddr)
		self.sock.listen(1)

	def wait_for_connection(self):
		print('Aguardando conexão...')
		conn, caddr = self.sock.accept()
		print('Conectado a',caddr)

		while True:
			print('Esperando mensagem...')
			data = conn.recv(2048)
			print('Mensagem recebida.')
			if len(data) == 0:
				print('Mensagem vazia... Wtf?')
				continue
			obj = self.formatter.convert_raw_data_to_obj(data)
			print('Objeto formado\n',obj)
			response = self.process_header(obj)
			if response != 'alala' and response != None:
				print('Resposta formada, enviando:\n',response)
				conn.send(self.formatter.serialize_with_null_bytes(response))
				print('Resposta enviada')
			if response == 'alala':
				print('Um erro inesperado aconteceu @wait_for_connection')

	def process_header(self, obj):
		print('Header Recebido')
		if obj['Header'] == 'InitData':
			print('Dados iniciais recebidos!')
			self.maths = TrafficMaths(obj['Content'])
			camThread.start()

			return None
		elif obj['Header'] == 'MeasurementData':
			print('Dados de medição recebidos')
			return {'Cross1':self.maths.calc_green_times(obj['Content'])}
		else:
			print('Dados inesperados recebidos:', data)
		return 'alala'

class JsonFormatter:
	def convert_raw_data_to_obj(self, raw):
		return json.loads(raw.split(b'\0')[0])
	def serialize_with_null_bytes(self, obj):
		a = json.dumps(obj).encode('utf-8')
		for i in range(300-len(a)):
			a+=b'\0'
		return a

class Cross:
	def __init__(self, I, t1, t2):
		self.I = I
		self.s1 = Semaphore(t1)
		self.s2 = Semaphore(t2)
		if self.s1.green + self.s1.yellow != self.s2.red or self.s2.green + self.s2.yellow != self.s1.red:
			raise Exception("Incoerência nos semáforos: t1: "+t1+" t2: "+t2+' I: '+I)
		self.ciclo = self.s1.green + self.s2.green + I + self.s1.yellow + self.s2.yellow

class Semaphore:
	def __init__(self, times):
		self.green, self.yellow, self.red = times
		self.nfaixas = 1 #Apenas uma faixa
		self.tvadich = self.filamax = 0
		self.saturationflow = 1

class TrafficMaths:
	def __init__(self, obj):
		#Iniciar constantes
		tmax = 120
		tmin = 25

		self.carsp1=self.carsp2=1

		#Receber dados iniciais
		I = obj['Cross1']['IntersectionTime']
		t1 = (obj['Cross1']['Sem1']['Green'],obj['Cross1']['Sem1']['Yellow'],obj['Cross1']['Sem1']['Red'])
		t2 = (obj['Cross1']['Sem2']['Green'],obj['Cross1']['Sem2']['Yellow'],obj['Cross1']['Sem2']['Red'])
		self.cross = Cross(I,t1,t2)

	def calc_green_times(self, obj):
		s1 = self.cross.s1
		s2 = self.cross.s2

		carsp1 = obj['Cross1']['Sem1']['CarsPassed']
		carsp2 = obj['Cross1']['Sem2']['CarsPassed']
		print('Passaram',carsp1,'carros no s1')
		print('Passaram',carsp2,'carros no s2')

		if carsp1 != 0:
			self.carsp1 = carsp1
		if carsp2 != 0:
			self.carsp2 = carsp2

		s1.flow = (self.carsp1 / (s1.green + s1.yellow)) * 3600
		s2.flow = (self.carsp2 / (s2.green + s2.yellow)) * 3600
		print('Fluxo em s1:',s1.flow)
		print('Fluxo em s2:',s2.flow)

		if s1.flow > s1.saturationflow:
			s1.saturationflow = s1.flow
			print('Alterando Fs de s1:',s1.saturationflow)
		if s2.flow > s2.saturationflow:
			s2.saturationflow = s2.flow
			print('Alterando Fs de s2:',s2.saturationflow)

		s1.y = s1.flow / s1.saturationflow
		s2.y = s2.flow / s2.saturationflow
		print('Taxa de ocupação de s1:',s1.y)
		print('Taxa de ocupação de s2:',s2.y)

		self.cross.Y = s1.y + s2.y
		print('Taxa de ocupação do cruzamento: ',self.cross.Y)

		s1.tvns = obj['Cross1']['Sem1']['NSGreen']
		s2.tvns = obj['Cross1']['Sem2']['NSGreen']
		print('Tempo de verde não saturado de s1: ',s1.tvns)
		print('Tempo de verde não saturado de s2: ',s2.tvns)

		s1.tvutil = carsp1/s1.nfaixas * 2
		s2.tvutil = carsp1/s2.nfaixas * 2
		print('Tempo de verde útil de s1:',s1.tvutil)
		print('Tempo de verde útil de s2:',s2.tvutil)

		s1.tvoc = s1.tvns - s1.tvutil
		s2.tvoc = s2.tvns - s2.tvutil
		print('Tempo de verde ocioso de s1:',s1.tvoc)
		print('Tempo de verde ocioso de s2:',s2.tvoc)

		s1.tvminc = s1.green - s1.tvoc
		s2.tvminc = s2.green - s2.tvoc
		print('Tempo de verde mínimo por ciclo de s1:',s1.tvminc)
		print('Tempo de verde mínimo por ciclo de s2:',s2.tvminc)

		s1.tvminh = s1.tvminc * 3600 / self.cross.ciclo
		s2.tvminh = s2.tvminc * 3600 / self.cross.ciclo
		print('Tempo de verde mínimo por hora de s1:',s1.tvminh)
		print('Tempo de verde mínimo por hora de s2:',s2.tvminh)

		cars1 = qtdcarros['Sem1']
		cars2 = qtdcarros['Sem2']
		print('Fila em s1:',cars1)
		print('Fila em s2:',cars2)

		if obj['Cross1']['Sem1']['Stage'] == 'R':
			if cars1 > s1.filamax:
				s1.filamax = cars1
				print('  ***  Nova fila máxima para s1:',cars1)
			s1.tvadich = (s1.filamax - cars1) * 2
			print('Tempo de verde adicional a s1 por hora:',s1.tvadich)
		if obj['Cross1']['Sem2']['Stage'] == 'R':
			if cars2 > s2.filamax:
				s2.filamax = cars2
				print('  ***  Nova fila máxima para s2:',cars2)
			s2.tvadich = (s2.filamax - cars2) * 2
			print('Tempo de verde adicional a s2 por hora:',s2.tvadich)

		s1.tvminh += s1.tvadich
		s2.tvminh += s2.tvadich
		print('Tempo de verde mínimo por hora NOVO de s1:',s1.tvminh)
		print('Tempo de verde mínimo por hora NOVO de s2:',s2.tvminh)

		s1.ni = obj['Cross1']['Sem1']['NMCars'] #Carros q passam no sem sem vel max
		s2.ni = obj['Cross1']['Sem2']['NMCars'] #Carros q passam no sem sem vel max
		print ('Número de carros perdem tempo verde s1:',s1.ni)
		print ('Número de carros perdem tempo verde s2:',s2.ni)

		s1.nf = obj['Cross1']['Sem1']['YellowPassed'] #Carros q passam no amarelo
		s2.nf = obj['Cross1']['Sem2']['YellowPassed'] #Carros q passam no amarelo
		print('Número de carros ganham tempo amarelo s1:',s1.nf)
		print('Número de carros ganham tempo amarelo s2:',s2.nf)
		
		s1.tti = 10 #aceleração constante
		s2.tti = 10 #aceleração constante

		s1.tpi = s1.tti - s1.ni/s1.saturationflow
		s2.tpi = s2.tti - s2.ni/s2.saturationflow
		print('Tempo perdido no início em s1: ',s1.tpi)
		print('Tempo perdido no início em s2: ',s2.tpi)

		s1.taf = s1.nf/s1.saturationflow
		s2.taf = s2.nf/s2.saturationflow
		print('Tempo ganho no fim de s1:',s1.taf)
		print('Tempo ganho no fim de s2:',s2.taf)

		self.cross.tp = (self.cross.I + s1.yellow + s2.yellow) + (s1.tpi + s2.tpi) - (s1.taf + s2.taf)
		print('\n\nTempo perdido no semáforo:',self.cross.tp)

		self.cross.tcot = (1.5 * self.cross.tp + 5)/(1-self.cross.Y)
		print('Tempo de ciclo ótimo:',self.cross.tcot)

		if self.cross.tcot < 30:
			self.cross.tcot = 30
		elif self.cross.tcot > 120:
			self.cross.tcot = 120

		print('Tempo de ciclo ótimo:',self.cross.tcot)
		tvt = self.cross.tcot - self.cross.I - s1.yellow - s2.yellow
		print('Tempo de verde total:',tvt)
		s1.green = s1.tvminh/(s2.tvminh+s1.tvminh) * tvt
		s2.green = tvt - s1.green
		print('\n\n\nTempo de verde s1:',s1.green)
		print('Tempo de verde s2:',s2.green,'\n\n\n\n\n\n\n\n\n\n\n\n')

		return [s1.green,s2.green]

class ScreenRecorder:
	def capture(self, tl,br):
		with mss.mss() as sct:
		    box = {'top': tl[1], 'left': tl[0], 'width': br[0]-tl[0], 'height': br[1]-tl[1]}
		    t = time.time()
		    img = np.array(sct.grab(box))
		return img

class MyDarkflow:
	def __init__(self):
		self.confidence = 0.4    

		self.option = {
		    'model': 'cfg/yolo.cfg',
		    'load': 'bin/yolo.weights',
		    'threshold':self.confidence,
		    'gpu': 0.7
		}

		self.tfnet = TFNet(self.option)
		self.colors = {'car':(238, 23, 23),'truck':(0, 255, 21),'bus':(3, 0, 255),'person':(0, 255, 243)}

	def highlight_vehicles(self, img):
		results = self.tfnet.return_predict(img)
		for result in results:
			#Pega posição e tipo do veículo
			tl = (result['topleft']['x'], result['topleft']['y'])
			br = (result['bottomright']['x'], result['bottomright']['y'])
			label = result['label']

			#Dá cor à label
			if label not in self.colors:
				self.colors[label] = 200 * np.random.rand(3)
			
			#Desenha quadrado em volta do veículo
			img = cv2.rectangle(img, tl, br, self.colors[label], 3)
			img = cv2.putText(img,label, tl, cv2.FONT_HERSHEY_COMPLEX,1,(0,0,0),2)
		return (img, len(results))

qtdcarros = {'Sem1':0,'Sem2':0}

def startCam():
	rec = ScreenRecorder()
	df = MyDarkflow()
	while 1:
		sem1 = rec.capture((84,176),(591,368))
		sem1 = cv2.cvtColor(np.array(sem1), cv2.COLOR_BGRA2BGR)
		sem1, cars1 = df.highlight_vehicles(sem1)
		cv2.imshow('Sem1',sem1)
		qtdcarros['Sem1'] = cars1
	
		sem2 = rec.capture((527,350),(812,871)) 
		sem2 = cv2.cvtColor(np.array(sem2), cv2.COLOR_BGRA2BGR)
		sem2 = imutils.rotate_bound(sem2, 270)
		sem2, cars2 = df.highlight_vehicles(sem2)
		cv2.imshow('Sem2',sem2)
		qtdcarros['Sem2'] = cars2
	
		time.sleep(1/60.)
		if cv2.waitKey(25) & 0xFF == ord('q'):
			cv2.destroyAllWindows()
			break

camThread = threading.Thread(target=startCam)

handler = ConnectionHandler(('127.0.0.1',11414))
handler.wait_for_connection()






