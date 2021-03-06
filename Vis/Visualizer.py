#Get the controller right: combining distance with direction
#Get smooth path

#generat path from graph (and path from image)
#BM: split project up

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import ImageFetcher
import Conversion
zoom=16

class Drone:
    __handleRadius = 3
    __lineLenght = 6
    __circle = None
    __line = None
    #The static kinematics:
    # __position        2D vector    
    # __orientation     floating point value
    # __velocity        floating point value
    # __rotation        floating point value

    #The steering kinematics:
    # linear/acceleration   floating point value
    # angular              floating point value

    def __init__(self, initialPosition, initialOrientation):
        self.__setPosition(initialPosition) 
        self.__orientation = initialOrientation 
        self.__velocity = 0.0
        self.__rotation = 0.0

    def __str__(self):
        return "drone: pos="+str(self.__position)+" ori="+str(self.__orientation)+" vel="+str(self.__velocity)+" rot="+str(self.__rotation)

    def __setPosition(self, newPosition):
        self.__position = newPosition
        if self.__circle is not None:
            self.__circle.center = newPosition
            xList = [newPosition[0],newPosition[0]+np.cos(self.__orientation)*self.__lineLenght]
            self.__line[0].set_xdata(xList)
            yList = [newPosition[1],newPosition[1]+np.sin(self.__orientation)*self.__lineLenght]
            self.__line[0].set_ydata(yList)
 
    def getPosition(self):
        return self.__position

    #Drawing drone
    def setupDrawing(self, figure):
        centerX, centerY = self.__position[0],self.__position[1]
        self.__circle = plt.Circle((centerX,centerY), self.__handleRadius,fc=np.random.random(3),picker=True, alpha=0.5)
        figure.gca().add_patch(self.__circle)
        xList = [centerX,centerX+np.cos(self.__orientation)*self.__lineLenght]
        yList = [centerY,centerY+np.sin(self.__orientation)*self.__lineLenght]
        self.__line = figure.gca().plot(xList, yList)
    
    #move the drone by curser
    def pickedUpAndMoved(self, newPosition, index):
        #moving a Drone
        if newPosition is not None:
            self.__setPosition(newPosition)

    def kinematicsUpdate(self, linear, angular): 
        print "kinematicsUpdate",linear, angular
        #update position and orientation
        self.__setPosition(self.__position +  self.__velocity * np.array([np.cos(self.__orientation), np.sin(self.__orientation)]))
        self.__orientation += self.__rotation

        #update steering: velocity and rotation 
        self.__velocity += linear
        self.__rotation = np.max(np.min(angular, np.pi*0.01),-np.pi*0.01)


class Path:
    __handleRadius = 6
    __controlPoints={}
    __controlPointsCircles={}
    __controlPointsLines=None
    __curves=None

    def pickedUpAndMoved(self, position, index):
        if index is not None:
             self.__setControlPoint(index, position)


    def __init__(self, viaPoints):
        for (i,p) in zip(range(0,len(viaPoints)),viaPoints):   
            self.__setControlPoint(i, p)

    #map from matplotlib-artists to some object that can change data
    __artistToControlPointIndex={}


    def __setControlPoint(self, index, coordinates):
        #Set control point with the give index (start at zero)
        global __controlPoints
        self.__controlPoints[index] = coordinates
        if index in self.__controlPointsCircles.keys():
            self.__controlPointsCircles[index].center = coordinates            

        #connecting lines
        if self.__controlPointsLines is not None:
            xy = self.__getXYCoordinatList()
            self.__controlPointsLines[0].set_xdata(xy[0])
            self.__controlPointsLines[0].set_ydata(xy[1])

        #update the quartic polynomials ...

        #and connecting curves...

    def getControlPointsDict(self):
        return (self.__controlPoints)

    def __getXYCoordinatList(self):
        xList = []
        yList = []
        for p in self.__controlPoints.values():
            xList.append(p[0])
            yList.append(p[1])
        return (xList, yList)

    #Path drawing
    def setupDrawing(self, figure):
        #connecting lines
        xy = self.__getXYCoordinatList()
        self.__controlPointsLines = figure.gca().plot(xy[0], xy[1])

        #Prepare for picking events
        for i,p in self.__controlPoints.iteritems():
            centerX, centerY = p[0], p[1]
            circle = plt.Circle((centerX,centerY), self.__handleRadius,fc=np.random.random(3),picker=True, alpha=0.5)
            self.__controlPointsCircles[i]=circle
            figure.gca().add_patch(circle)

            #Prepare for picking events
            self.__artistToControlPointIndex[circle]=i

    #Picking logic for Path control points
    def selectControlPoint(self, artist):
        if(artist in self.__artistToControlPointIndex):
            controlIndex = self.__artistToControlPointIndex[artist]
            return(controlIndex)

    #Control system aux
    __minDistLineStartPointIndex = 0 #Keep track of progress along path (avoid get used line segments)
    def calcSignedDistToPath(self, point):
        minDist = 2**31 #a big number
        minDistLineStartPoint=None
        for i in range(self.__minDistLineStartPointIndex,len(self.__controlPoints)-1):
            a=self.__controlPoints[i]
            b=self.__controlPoints[i+1]
            dist = signedDistanceToLineSegment(a,b,point)
            print a,b,"dist=",dist
            if np.abs(dist) <= np.abs(minDist):
                minDist = dist      
                minDistLineStartPoint=a
                self.__minDistLineStartPointIndex = i
        res = minDist*np.sign((b[0]-b[0])*(point[1]-a[1]) - (b[1]-a[1])*(point[0]-a[0]))
        print "calcSignedDistToPath", self.__minDistLineStartPointIndex, minDistLineStartPoint, res, minDistLineStartPoint
        return res

#calculate the signed distance to a line segment defined by p1 and p2 as 
#endpoints.
def signedDistanceToLineSegment(p1, p2, p3): # x3,y3 is the point
    def leftSideCheck(p1, p2, p3):
        return ((p1-p2)[0] * (p1-p3)[1] - (p1-p2)[1] * (p1-p3)[0]) > 0

    x1,y1 = p1[0], p1[1]
    x2,y2 = p2[0], p2[1]
    x3,y3 = p3[0], p3[1]
    px = x2-x1
    py = y2-y1

    num = px*px + py*py
    u =  ((x3 - x1) * px + (y3 - y1) * py) / float(num)
    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3
    
    dist = np.sqrt(dx*dx + dy*dy)
    
    if leftSideCheck(p1, p2, p3):
        return dist 
    else:
        return -dist 
    
import PID
class Controller:
    __ctl = PID.PID(P=0.013 , I=0.00225, D=0.43  )
    __drone = None
    __path = None

    def __init__(self, drone, path):
        self.__drone = drone
        self.__path = path

    def __call__(self):
        if self.__drone is not None and self.__path is not None:
            return self.__ctl.update(self.error())
        else:
            return 0

    def error(self):
        err = self.__path.calcSignedDistToPath(self.__drone.getPosition())
        print "err="+str(err)
        return err  
################################################################################


#Plot
plt.ion()
figure = plt.figure('map')
figure.gca().set_aspect('equal')


#make a Catmull Rom spline path
path = Path([np.array([103, 225]),
             np.array([ 99, 204]),
             np.array([ 93, 183]),
             np.array([ 84, 158]),
             np.array([ 79, 129]),
             np.array([ 84, 103]),
             np.array([ 94,  78]),
             np.array([111,  53]),
             np.array([131,  42]),
             np.array([154,  41]),
             np.array([177,  49]),
             np.array([194,  64]),
             np.array([202,  82]),
             np.array([212,  109]),
             np.array([221, 144]),
             np.array([224, 170]),
             np.array([226, 191])
             ])
path.setupDrawing(figure)


#make the drone
drone = Drone(np.array([ 100, 225]), -np.pi/2)
drone.setupDrawing(figure)


controller = Controller(drone, path)
linear = 1
def UpdateDrone():
    global linear
    ctl = controller()
    angular = ctl # min(max(ctl,-0.02*np.pi), 0.02*np.pi)
    print "UpdateDrone", ctl, angular
    drone.kinematicsUpdate(linear, angular)
    figure.canvas.draw()
    linear = 0 #constant speed/no acceleration
    print str(drone)+"\n"

timer = figure.canvas.new_timer(interval=20)
timer.add_callback(UpdateDrone)
timer.start()

#State for user picking logic 
movable = None
index = None #spline path controle point index

def on_pick(event):
    global movable,index,controller, drone
    index = path.selectControlPoint(event.artist)
    if index is not None:
        movable = path
    else:
        movable = drone
        drone.__rotation=0
        controller = Controller(drone, path)

def motion_notify_event(event):
    global figure
    if movable is not None:
        movable.pickedUpAndMoved(np.array([event.xdata, event.ydata]), index)
    figure.canvas.draw()

def button_press_event(event):
    pass

def button_release_event(event):
    global movable, index
    movable, index = None, None

figure.canvas.mpl_connect('pick_event', on_pick)
figure.canvas.mpl_connect('motion_notify_event', motion_notify_event)
figure.canvas.mpl_connect('button_press_event', button_press_event)
figure.canvas.mpl_connect('button_release_event', button_release_event)

#Background image
image = ImageFetcher.ImageFetcher(55.410600, 10.379845, zoom).fetch()	
plt.imshow(image)

#Disable default keys on the plot e.g. 'k' is logaritmic scale
figure.canvas.mpl_disconnect(figure.canvas.manager.key_press_handler_id)

#Display the figures on screen
plt.show(block=True)


################################################################################

def printCoordinates(event):
    global figure
    if event.xdata is not None and event.ydata is not None:
        px, py = np.ceil(event.xdata), np.ceil(event.ydata)
        print("pixel: "+str(px)+", "+str(py))
        mx, my=Conversion.PixelsToMeters(px, py, zoom)
        print("mx="+str(mx)+" my="+str(my))
        lat, lon=Conversion.MetersToLatLon( mx, my )
        print("Lat="+str(lat)+" lon="+str(lon) +"    "+ str(lat)+","+str(lon))

#PVM
