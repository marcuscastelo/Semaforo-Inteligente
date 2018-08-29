from darkflow.net.build import TFNet
import numpy as np
import cv2
import matplotlib.pyplot as plt
import signal
import sys


labels = ['dog','cat','truck','bicycle','car','person']

options = {"model": "cfg/yolo.cfg", "load": "bin/yolo.weights", "threshold": 0.25}

tfnet = TFNet(options)

img = cv2.imread("./sample_img/sample_office.jpg")
results = tfnet.return_predict(img)

colors = [tuple(255 * np.random.rand(3)) for i in range(5)]

sizer = int(img.shape[1]/768)

for res, color in zip(results,colors):
	tl = (res['topleft']['x'],res['topleft']['y'])
	br = (res['bottomright']['x'],res['bottomright']['y'])
	label = res['label']
	img = cv2.rectangle(img,tl,br,color, sizer*3)
	img = cv2.putText(img,label, tl, cv2.FONT_HERSHEY_COMPLEX,sizer,(0,0,0),sizer*2)

for j in range(0,len(labels)):
	item = [i for i in results if i['label'] in labels[j]]
	result = len(item)
	print(result,labels[j],'found')

img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
plt.imshow(img)
plt.show()


signal.signal(signal.SIGINT, sigr)

def sigr(signal, frame):
	capture.release()
	cv2.destroyAllWindows()
	sys.exit(0)