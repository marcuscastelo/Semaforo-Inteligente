from darkflow.net.build import TFNet
import cv2
import numpy as np
import time
import signal
import sys

confidence = 0.4

options = {
	'model': 'cfg/yolo.cfg',
	'load': 'bin/yolo.weights',
	'threshold':confidence,
	'gpu': 0.7
}

tfnet = TFNet(options)

#capture = cv2.VideoCapture('crowd.mp4')
capture = cv2.VideoCapture(0) #Camera detection
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)

searchlabels = ['car','person','truck']

while capture.isOpened():
	stime = time.time()
	ret, frame = capture.read()
	results = tfnet.return_predict(frame)
	for l in searchlabels:
		qtdp = len([i for i in results if i['label']==l and i['confidence'] > confidence])
		print(qtdp,l,'found')
	if ret:
		for result in results:
			tl = (result['topleft']['x'], result['topleft']['y'])
			br = (result['bottomright']['x'], result['bottomright']['y'])
			label = '{}: {:.0f}%'.format(result['label'], result['confidence']*100)
			frame = cv2.rectangle(frame, tl, br, (0,0,255), 3)
			frame = cv2.putText(frame,label, tl, cv2.FONT_HERSHEY_COMPLEX,1,(0,0,0),2)
		cv2.imshow('frame', frame)
		print('FPS {:.1f}'.format(1/(time.time()-stime)))
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	else:
		sigr()	
		break

signal.signal(signal.SIGINT, sigr)

def sigr(signal, frame):
	capture.release()
	cv2.destroyAllWindows()
	sys.exit(0)