from darkflow.net.build import TFNet
import cv2
import numpy as np
import time
import signal
import sys
import utils


confidence = 0.4    

option = {
    'model': 'cfg/yolo.cfg',
    'load': 'bin/yolo.weights',
    'threshold':confidence,
    'gpu': 0.7
}

tfnet = TFNet(option)


WIDTH = 326
HEIGHT = 238

capture = cv2.VideoCapture('video.mp4')
capture.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH) # R (935,526),(1279,684),(1253,284),(1278, 367)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

#searchlabels = ['car','person','truck']

colors = {'car':(238, 23, 23),'truck':(0, 255, 21),'bus':(3, 0, 255),'person':(0, 255, 243)}

r_exit_pts = np.array([[[748,714],[693,521],[1276,234],[1279,715]]])
#r_exit_pts = np.array([[[733,688],[705,555],[1255,490],[1278, 622]]])

base = np.zeros((HEIGHT,WIDTH) + (3,), dtype='uint8')

exit_mask = cv2.fillPoly(base, r_exit_pts, (255, 255, 255))[:, :, 0]


DIVIDER_COLOUR = (255, 255, 0)
BOUNDING_BOX_COLOUR = (255, 0, 0)
CENTROID_COLOUR = (0, 0, 255)
CAR_COLOURS = [(0, 0, 255)]
EXIT_COLOR = (66, 183, 42)

class VehicleCounter():
    '''
        Counting vehicles that entered in exit zone.

        Purpose of this class based on detected object and local cache create
        objects pathes and count that entered in exit zone defined by exit masks.

        exit_masks - list of the exit masks.
        path_size - max number of points in a path.
        max_dst - max distance between two points.
    '''

    def __init__(self, exit_masks=[], path_size=10, max_dst=30, x_weight=1.0, y_weight=1.0):

        self.exit_masks = exit_masks

        self.vehicle_count = 0
        self.path_size = path_size
        self.pathes = []
        self.max_dst = max_dst
        self.x_weight = x_weight
        self.y_weight = y_weight

    def check_exit(self, point):
        for exit_mask in self.exit_masks:
            try:
                if exit_mask[point[1]][point[0]] == 255:
                    return True
            except:
                return True
        return False

    def __call__(self, matches):
        objects = matches
        #print('\n\n\n\n\n\n\n\n\n\n****************************************************\n',objects,'********************\n\n\n\n\n\n\n')

        points = np.array(objects)[:, 0:2]
        points = points.tolist()

        # add new points if pathes is empty
        if not self.pathes:
            for match in points:
                self.pathes.append([match])

        else:
            # link new points with old pathes based on minimum distance between
            # points
            new_pathes = []

            for path in self.pathes:
                _min = 999999
                _match = None
                for p in points:
                    if len(path) == 1:
                        # distance from last point to current
                        d = utils.distance(p[0], path[-1][0])
                    else:
                        # based on 2 prev points predict next point and calculate
                        # distance from predicted next point to current
                        xn = 2 * path[-1][0][0] - path[-2][0][0]
                        yn = 2 * path[-1][0][1] - path[-2][0][1]
                        d = utils.distance(
                            p[0], (xn, yn),
                            x_weight=self.x_weight,
                            y_weight=self.y_weight
                        )

                    if d < _min:
                        _min = d
                        _match = p

                if _match and _min <= self.max_dst:
                    points.remove(_match)
                    path.append(_match)
                    new_pathes.append(path)

                # do not drop path if current frame has no matches
                if _match is None:
                    new_pathes.append(path)

            self.pathes = new_pathes

            # add new pathes
            if len(points):
                for p in points:
                    # do not add points that already should be counted
                    if self.check_exit(p[1]):
                        continue
                    self.pathes.append([p])

        # save only last N points in path
        for i, _ in enumerate(self.pathes):
            self.pathes[i] = self.pathes[i][self.path_size * -1:]

        # count vehicles and drop counted pathes:
        new_pathes = []
        for i, path in enumerate(self.pathes):
            d = path[-2:]

            if (
                # need at list two points to count
                len(d) >= 2 and
                # prev point not in exit zone
                not self.check_exit(d[0][1]) and
                # current point in exit zone
                self.check_exit(d[1][1]) and
                # path len is bigger then min
                self.path_size <= len(path)
            ):
                self.vehicle_count += 1
            else:
                # prevent linking with path that already in exit zone
                add = True
                for p in path:
                    if self.check_exit(p[1]):
                        add = False
                        break
                if add:
                    new_pathes.append(path)

        self.pathes = new_pathes

        print('#VEHICLES FOUND: %s' % self.vehicle_count)

        return self.vehicle_count

class Visualizer():

    def __init__(self, save_image=False, image_dir='images'):
        super(Visualizer, self).__init__()

        self.save_image = save_image
        self.image_dir = image_dir

    def check_exit(self, point, exit_masks=[]):
        for exit_mask in exit_masks:
            if exit_mask[point[1]][point[0]] == 255:
                return True
        return False

    def draw_pathes(self, img, pathes):
        if not img.any():
            return

        for i, path in enumerate(pathes):
            path = np.array(path)[:, 1].tolist()
            for point in path:
                cv2.circle(img, point, 2, CAR_COLOURS[0], -1)
                cv2.polylines(img, [np.int32(path)], False, CAR_COLOURS[0], 1)

        return img

    def draw_boxes(self, img, pathes, exit_masks=[]):
        for (i, match) in enumerate(pathes):

            contour, centroid = match[-1][:2]
            if self.check_exit(centroid, exit_masks):
                continue

            x, y, w, h = contour

            cv2.rectangle(img, (x, y), (x + w - 1, y + h - 1),
                          BOUNDING_BOX_COLOUR, 1)
            cv2.circle(img, centroid, 2, CENTROID_COLOUR, -1)
        return img
    def draw_ui(self, img, vehicle_count, exit_masks=[]):
        # this just add green mask with opacity to the image
        for exit_mask in exit_masks:
            _img = np.zeros(img.shape, img.dtype)
            _img[:, :] = EXIT_COLOR
            print('\n\n\n',img,'\n\n\n',_img,'\n\n\n\n',exit_mask)
            mask = cv2.bitwise_and(_img, _img, mask=exit_mask)
            cv2.addWeighted(mask, 1, img, 1, 0, img)
        # drawing top block with counts
        cv2.rectangle(img, (0, 0), (img.shape[1], 50), (0, 0, 0), cv2.FILLED)
        cv2.putText(img, ("Vehicles passed: {total} ".format(total=vehicle_count)), (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        return img

    def __call__(self, context):
        frame = context['frame'].copy()
        pathes = context['pathes']
        exit_masks = context['exit_masks']
        vehicle_count = context['vehicle_count']

        frame = self.draw_ui(frame, vehicle_count, exit_masks)
        frame = self.draw_pathes(frame, pathes)
        frame = self.draw_boxes(frame, pathes, exit_masks)

        return context


vc = VehicleCounter(exit_masks=[exit_mask], y_weight=2.0)
vis = Visualizer()

context = {'pathes':[],'exit_masks':[exit_mask],'vehicle_count':0}

while capture.isOpened() or True:
    stime = time.time()
    ret, frame = capture.read()
    if ret:
        print(frame.shape)
        results = tfnet.return_predict(frame)
        #for l in searchlabels:
        #    qtdp = len([i for i in results if i['label']==l and i['confidence'] > confidence])
        #    print(qtdp,l,'found')
        matches = []
        for result in results:
            tl = (result['topleft']['x'], result['topleft']['y'])
            br = (result['bottomright']['x'], result['bottomright']['y'])
            label = result['label']
            if label not in colors:
                colors[label] = 200 * np.random.rand(3)
            frame = cv2.rectangle(frame, tl, br, colors[label], 3)
            frame = cv2.putText(frame,label, tl, cv2.FONT_HERSHEY_COMPLEX,1,(0,0,0),2)

            x,y = tl
            w,h = (br[0]-tl[0],br[1]-tl[1])
            centroid = utils.get_centroid(x,y,w,h)
            matches.append(((x,y,w,h),centroid))
            #print(matches)
        vc(matches)
        context['frame'] = frame
        context = vis(context)

        cv2.imshow('frame', frame)
        print('FPS {:.1f}'.format(1/(time.time()-stime)))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        pass
        
