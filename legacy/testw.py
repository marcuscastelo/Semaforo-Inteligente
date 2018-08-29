from darkflow.net.build import TFNet
import cv2
import numpy as np
import time
import signal
from contextlib import contextmanager
import sys, os

class Leitor:
	def __del__(self, signal, frame):
		self.capture.release()
		cv2.destroyAllWindows()
		sys.exit(0)

	def __init__(self, href):
		self.confidence = 0.4
		self.option = {
			'model': 'cfg/yolo.cfg',
			'load': 'bin/yolo.weights',
			'threshold':self.confidence,
			'gpu': 0.7
		}

		self.tfnet = TFNet(self.option)

		self.capture = cv2.VideoCapture(href)
		self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
		self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)

		self.colors = {'car':(238, 23, 23),'truck':(0, 255, 21),'bus':(3, 0, 255),'person':(0, 255, 243)}
	
	def read(self):
		if self.capture.isOpened():
			print('kill')
			stime = time.time()
			ret, frame = self.capture.read()
			if ret:
				results = self.tfnet.return_predict(frame)
				qtds = {}
				for l in searchlabels:
					qtd = len([i for i in results if i['label']==l and i['confidence'] > self.confidence])
					qtds[l]=qtd
				# for result in results:
				# 	tl = (result['topleft']['x'], result['topleft']['y'])
				# 	br = (result['bottomright']['x'], result['bottomright']['y'])
				# 	label = result['label']
				# 	if label not in self.colors:
				# 		self.colors[label] = 200 * np.random.rand(3)
				# 	frame = cv2.rectangle(frame, tl, br, self.colors[label], 3)
				# 	frame = cv2.putText(frame,label, tl, cv2.FONT_HERSHEY_COMPLEX,1,(0,0,0),2)
				# cv2.imshow('frame', frame)
				# print('FPS {:.1f}'.format(1/(time.time()-stime)))
				return qtds
			else: return -2

global searchlabels, leitor_h, leitor_v
def start(labels = ['car','person','truck','bus']):
	searchlabels = labels
	leitor_h = Leitor('http://127.0.0.1:5000/video_feed_h')
	r = -1
	while r == -1:
		r = leitor_h.read()
		print('GAY FODA:', r)
		time.sleep(1/10.0)
	print('GAY:',r)
	#leitor_v = Leitor('http://127.0.0.1:5000/video_feed_v')