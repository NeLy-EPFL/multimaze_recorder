import serial
import time
import math
import struct

import cv2

#from inputimeout import inputimeout

import graph_adjusted as graph

#-------LIBRARIES FOR COMPUTER VISION------
import numpy as np
from skimage.io import imshow, imread
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from skimage.feature import match_template, peak_local_max
#-------------------------------------------

#Open the serial port to communicate with the arduino
arduino = serial.Serial(port='/dev/ttyACM0',  baudrate=115200, timeout=.1)

#Open the serial port to communicate with the Zaber motor
zaber = serial.Serial(port='/dev/ttyACM1', baudrate=115200, timeout=.1)


#home the Zaber motor
command = "/home\n" 
zaber.write(command.encode())
ZABER_START = 350000
command="/move abs "+str(ZABER_START)+"\n"
time.sleep(2.5)
zaber.write(command.encode())
time.sleep(2.5)

zaber_dragging = False

#Position of the final goal
targetX=0
targetY=0

#Position of the magnet
START_X = 0
START_Y = 0
posX=START_X
posY=START_Y

#transmitted to arduino to know whether to drag_back or to move
escape=0

#Boolean to inform if the magnet is currently dragging back
dragging=False


'''
    ENCORE À AJUSTER  --> Une idée possible est de hardcoder les destinations des balles en cm en plus des pixels 
    --> Comme ça au lieu de convertir pixels to cm, on envoie directement x_cm et y_cm et on évite la distortion due à la caméra
    ---> NE PAS OUBLIER QUE LA CAMERA N'EST QUE LE SUPPORT --> CE QUI IMPORTE C'EST L'ENVIRONNEMENT PHYSIQUE
'''


BALLS_DESTINATION = [
    [[71,195, [26.49,  18.6]],[154,195,[25.91, 18.6]],[245,195,[25.34, 18.6]],[327,195,[24.74, 18.6]],[417,195,[24.27, 18.6]],[500,195,[23.57, 18.6]]], #top-left
    
    [[1565,195,[17.57, 18.7]],[1650,195,[16.85, 18.7]],[1735,195,[16.3, 18.7]],[1820,195,[15.81, 18.7]],[1913,195,[15.3, 18.7]],[2000,195,[14.7, 18.7]]], #top_middle  
    
    [[3057,190,[8.45, 18.8]],[3143,190,[7.85, 18.8]],[3230,190, [7.3,  18.8]],[3315,190, [6.8, 18.8]],[3407,190, [6.25,  18.8]],[3492,190,[5.75, 18.8]]], #top_right  
    
    [[71,1350,[26.49,  11.7]],[154,1350,[25.91, 11.7]],[245,1350,[25.34, 11.7]],[327,1350,[24.74, 11.7]],[417,1350,[24.27, 11.7]],[500,1350,[23.57,  11.7]]], #middle_left
    
    [[1565,1350,[17.57, 11.8]],[1650,1350,[16.85, 11.8]],[1735,1350,[16.3, 11.8]],[1820,1350,[15.81, 11.8]],[1913,1350,[15.3, 11.8]],[2000,1350, [14.7,  11.8]]], #middle_middle
    
    [[3057,1350, [8.45,  11.9]],[3143,1350, [7.85,  11.9]],[3230,1350, [7.3,  11.9]],[3315,1350, [6.8, 11.9]] ,[3407,1350, [6.25,  11.9]],[3492,1350,[5.75, 11.9]]], #middle_right 5 + 6.7
    
    [[71,2508,[26.49, 4.7]],   [154,2508,[25.91, 4.7]], [245,2508,[25.34, 4.7]], [327,2508,[24.74, 4.7]], [417,2508,[24.27, 4.7]], [500,2508,[23.57, 4.7]]], #bottom_left 17.25 + 6.4
    
    [[1565,2508,[17.57, 4.8]],[1650,2508,[16.85, 4.8]],[1735,2508,[16.3, 4.8]],[1820,2508,[15.81, 4.8]],[1913,2508,[15.3, 4.8]],[2000,2508, [14.7, 4.8]]], #bottom_middle 8.25 + 6.5
    
    [[3057,2508,[8.45, 4.9]],[3143,2508,[7.85, 4.9]],[3230,2508, [7.3, 4.9]],[3315,2508, [6.8, 4.9]],[3407,2508, [6.25, 4.9]],[3492,2508,[5.75, 4.9]]] #bottom_right
]

########## EVIDEMMENT CHANGER ###########
X_MIN = -30
X_MAX = 30
Y_MIN = -20
Y_MAX = 20

#########################################

#----------------UTILS--------------------
REV = 1600
RAYON = 1.6
EMPIRICAL = 5.02

def convertXtoSteps(x):
    return int((2*EMPIRICAL*x/(RAYON*math.pi))*REV)  #x in cm

def convertYtoSteps(y):
    return int(((EMPIRICAL*y/(RAYON*math.pi))*REV))  #y in cm

def stepsToX(s):
    return (RAYON*math.pi*s)/(2*EMPIRICAL*REV) #cm

def stepsToY(s):
    return (RAYON*math.pi*s)/(EMPIRICAL*REV)  #cm

def closeEnough(x,y,threshold):
    try:
        return abs(x-y)<threshold
    except Exception:
        print("Error in closeEnough function")
        return False 


#---------------------COMPUTER VISION (Pattern Matching)-------------------------
'''
    Normalement A NE Pas Toucher --> TOUT FONCTIONNE PARFAITEMENT
    Maximum ajuster le threshold + si on hardcode les destinations des balles en cm, il faudra 
    changer convertPixelsToCm(dest[0]) en x_cm et convertPixelsToCm(dest[1]) en y_cm 
'''

#Regions to divide the image to 9 parts (The only parts where it is possible to find a ball)
DIVIDE_REGIONS = [[25,550,130,450],  [1520,2050,130,450],[3020,3520,130,450],
                  [25,550,1300,1650],[1520,2050,1300,1650] , [3020,3520,1300,1650],
                  [25,550,2420,2820],[1520,2050,2420,2820], [3020,3520,2420,2820]]

#If needed, patch creation taken from the middle region to match the size + code to visualize the patch
'''
PATCH_X_MIN=200
PATCH_X_MAX=230
PATCH_Y_MIN=245
PATCH_Y_MAX=275
sample_div = sample[1300:1650, 1520:2050]
patch = sample_div[PATCH_Y_MIN:PATCH_Y_MAX, PATCH_X_MIN:PATCH_X_MAX]

fig, ax = plt.subplots(1,2,figsize=(10,10))
ax[0].add_patch(Rectangle((PATCH_X_MIN, PATCH_Y_MIN), PATCH_X_MAX-PATCH_X_MIN, PATCH_Y_MAX-PATCH_Y_MIN, edgecolor='b', facecolor='none'));
ax[0].set_title('Patch Location',fontsize=15)

#Showing Patch
ax[0].imshow(sample_div,cmap='gray')
patch = sample_div[PATCH_Y_MIN:PATCH_Y_MAX, PATCH_X_MIN:PATCH_X_MAX]
ax[1].imshow(patch,cmap='gray')
ax[1].set_title('Patch',fontsize=15)
plt.show()

cv2.imwrite('python\patch.jpg',patch)
'''

#pattern to be matched (patch)
patch = imread('patch.jpg')

'''
    Il y a peut-être juste ça à ajuster
'''
#Threshold to detect if a ball has reached a ball_destination
THRESHOLD_DETECTION_READY = 20 

#List to store all the balls that are ready to be dragged back
balls_ready=[]

PATCH_WIDTH, PATCH_HEIGHT = patch.shape

#Function to read an image and detect the balls that reached a destination
def balls_detection(image):
    #Read new image
    sample2 = imread(image)

    #plot new image
    '''
    fig, ax = plt.subplots(1,2,figsize=(10,10))
    ax[0].imshow(sample2,cmap='gray')
    ax[1].imshow(sample2,cmap='gray')
    ax[0].set_title('Grayscale',fontsize=15)
    ax[1].set_title('Template Matched',fontsize=15)
    '''
    

    '''
    rect = plt.Rectangle((68, 1356), patch_height, patch_width, color='g', 
                fc='none')
    ax[1].add_patch(rect)
    '''
    #length ball_destination
    len_dest = len(BALLS_DESTINATION)

    #Do pattern matching for each of the divided regions
    for i in range(len(DIVIDE_REGIONS)):
        x_min, x_max, y_min, y_max = DIVIDE_REGIONS[i]
        sample_div = sample2[y_min:y_max, x_min:x_max]
        sample_mt = match_template(sample_div, patch)

        for y, x in peak_local_max(sample_mt, threshold_abs=0.76):
            #Add the detected rectangles to the image
            '''
            rect = plt.Rectangle((y+y_min, x+x_min), patch_height, patch_width, color='r', 
                                    fc='none')
            ax[1].add_patch(rect)
            '''

            '''CHECK if patch_width/2 and patch_height/2 are correct'''
            x = x + x_min + PATCH_WIDTH / 2
            y = y + y_min + PATCH_HEIGHT / 2

            if i in range(len_dest):
                #Check if a ball reached a destination
                for dest in BALLS_DESTINATION[i]:
                    #If a ball reached a destination, append the list balls_ready
                    if closeEnough(dest[0],x,THRESHOLD_DETECTION_READY) and closeEnough(dest[1], y,THRESHOLD_DETECTION_READY):                     
                        try:
                            if not dest[2] in balls_ready:
                                balls_ready.append(dest[2])
                        except Exception:
                            print("EXCEPTION 1   ", dest)
                        break
    
                    #Add the detected rectangles that are matching a destination to the image
                    '''
                    rect = plt.Rectangle((dest[0], dest[1]), patch_height, patch_width, color='b', 
                                fc='none')
                    ax[1].add_patch(rect)
                    '''

    #plt.show()



#------------------------ Best Moment strategy ---------------------------
#-------------------- Motion plannning using a graph ---------------------

THRESHOLD_REST = 0.05
THRESHOLD_MAGNET_ARRIVED = 0.05
THRESHOLD_SAME_GOAL = 0.05

'''
    SUR LE VRAI SETUP, ADAPTER CES POSITIONS
    (Les * représentent les x de repos et les | représentent les rails)
    *||||||*  *||||||*  *||||||*
    *||||||*  *||||||*  *||||||*
    *||||||*  *||||||*  *||||||*

    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    EN CHANGEANT REST_X NE PAS OUBLIER DE CHANGER LA VALEUR DES COL DANS GRAPH_MAP
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''
REST_X = [4, 10, 13, 19, 22, 28]
ESCAPE_BACK = 1

ESCAPE_GOAL = 0
def find_nearest_point(array, XA, YA):
    nearest_point = array[0]
    if len(array)>1:
        min = np.sqrt((array[0][0] - XA) ** 2 + (array[0][1] - YA) ** 2)
        nearest_point=array[0]
        for ar in array:
            d=np.sqrt((ar[0] - XA) ** 2 + (ar[1] - YA) ** 2)
            if(min>d):
                min = d
                nearest_point = ar
    return nearest_point

def find_nearest_X(array, XA):
    nearest_X = array[0]
    if len(array)>1:
        min = abs(array[0] - XA)
        #nearest_point=array[0]
        for ar in array:
            d = abs(ar - XA)
            if(min>d):
                min = d
                nearest_X = ar
    return nearest_X

#******INTERPRETATION OF COMPUTER VISION****
def computerVisionInterpretation(x,y,posX,posY,path):
    towards_rest = False
    if len(balls_ready) :
        '''
        If at least a ball reached its destination, then the goal of the magnet is the closest ball
            *If the magnet reached the final destination, then escape = 1 to trigger dragBack + remove the ball from the list of balls_ready
            *If the magnet is not at the final destination, then escape = 0 to allow the magnet to move towards the ball
        '''
        #Determine the closest ball_ready to the magnet --> Goal
        x,y = find_nearest_point(balls_ready,posX,posY) 

        print("check dumm  ",x,"   ",y)
        print("check dumm  22  ",posX,"   ",posY)

        #If the goal is close enough to the magnet, then trigger drag_back 
        # and remove the ball from the list balls_ready 
        if closeEnough(x,posX,THRESHOLD_MAGNET_ARRIVED) and closeEnough(y,posY,THRESHOLD_MAGNET_ARRIVED):
            path = []
            escape = ESCAPE_BACK
            balls_ready.remove([x,y])
            print("CLOSE")

        #If the magnet is far from the ball, allow it to move towards it
        else: 
            escape = ESCAPE_GOAL
        
    #If no ball reached a desination, go to rest --> go to the nearest X where the magnet can rest
    # --> y is set to the current posY 
    else:
        escape = ESCAPE_GOAL
        x = find_nearest_X(REST_X,posX)
        y = posY

        towards_rest = True

    return x,y,escape,path,towards_rest

def goalReached(x, y, arrived, path, towards_rest):
    '''
        Qu'on soit clair le path retourné par graph_map ne contient pas le noeud de départ
        mais contient les noeuds qui "font les coins" + le noeud D'ARRIVEE !!!
    '''

    size_path = len(path)
    data =""
    
    at_rest = False

    print(path)
    
    if(size_path > 1):  #New target = first node of the shortest path
        print("hahhh")
        realTargetX, realTargetY = graph.getNodePosition(path[0])
        data = f"{ESCAPE_GOAL},{convertXtoSteps(realTargetX-START_X)},{convertYtoSteps(realTargetY-START_Y)}\n" 
        arrived = False   
        #remove first node of the path since the command to go towards it has already been sent
        path.pop(0)
        #print("x  y   ",realTargetX,"   ",realTargetY)
        #print("pos  ",posX,"   ",posY)

    elif (size_path == 1): #Go directly towards the goal
        print("gvhbhj")
        #print("else  x  y   ",x,"   ",y)
        #print("else  pos  ",posX,"   ",posY)
        data = f"{ESCAPE_GOAL},{convertXtoSteps(x-START_X)},{convertYtoSteps(y-START_Y)}\n" 
        arrived = False
        path.pop(0)


    elif(size_path == 0):
        # If we were going towards rest and we reached the final destination, we are actually at rest
        if towards_rest:
            at_rest = True
        #TROUVER UNE SOLUTION POUR LE CAS OU ON EST ARRIVE A DESTINATION ET QU'ON EST PAS EN REST
            #NORMALEMENT ON DEVRAIT JAMAIS AVOIR UN PATH VIDE SANS ÊTRE EN REST
            #SAUF SI ON A PAS BOUGE LA BALLE (COMPRENDRE POURQUOI? + TRADUIRE CA EN CONDITION + GERER CE PROBLEME)
        print("IN REST")

        '''
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            ENLEVER
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        '''
        #BALLS_DESTINATION[4]=[[1561,1350],[1646,1350],[1731,1350],[1816,1350],[1900,1350],[1985,1350]] #middle_middle
        '''
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            ENLEVER
        !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        '''
    arduino.write(data.encode())  # Encode and send the data to the Arduino

    return arrived,path, at_rest

def setNewGoal(x, y, posX, posY, path, towards_rest, at_rest):
    '''
        Set new goal --> establish new shortest path towards this goal
        --> new target = first node of the shortest path
    '''              
    ESCAPE = 0

    #Reset arrived to false 
    arrived = False

    #print("CORRECT INPUT") 
    #time.sleep(0.1)

    #Establish new shortest path
    if not towards_rest:
        path = graph.shortest_path([posX,posY],[x,y],at_rest)
        
    #Reset realTargetX and realTargetY
    realTargetX = 0
    realTargetY = 0
    path_size = len(path)
    print("path ",path)
    if path_size > 1:  #New target = first node of the shortest path
        print("path", path)
        realTargetX, realTargetY = graph.getNodePosition(path[0])
        #remove first node of the path since the command to go towards will be sent now
        path.pop(0)

    else:  #Go directly towards the goal
        realTargetX = x
        realTargetY = y

    print("elif x  y   ",realTargetX,"   ",realTargetY)

    data = f"{ESCAPE},{convertXtoSteps(realTargetX-START_X)},{convertYtoSteps(realTargetY-START_Y)}\n"  
    arduino.write(data.encode())  # Encode and send the data to the Arduino

    return arrived,path

def dragBack(zaber_dragging):
    '''
        Trigger drag back --> push the ball
    '''
    # Zaber goes down
    if not zaber_dragging:
        command ="/1 move rel 85000\n"
        print("ZZZZZZZZZZAAAAAAAAAAABBEEEEERRRRR         BACK")
        zaber.write(command.encode())
        zaber_dragging = True
        data = f"{ESCAPE_BACK}\n"
        arduino.write(data.encode())  # Encode and send the data
        time.sleep(0.5)
    return zaber_dragging
#Function to send the target to the robot
def sendTarget(x,y,posX,posY,arrived,path, at_rest, zaber_dragging):
    x_old,y_old = x,y

    #********************COMPUTER VISION INTERPRETATION*************************
    try:
        x,y,escape,path,towards_rest=computerVisionInterpretation(x,y,posX,posY,path)
    except Exception:
        print("EXCEPTION 0")
        return x_old,y_old,arrived,path, at_rest, zaber_dragging

    #********************GOAL ANALYSIS AND MOTORS CONTROL**********************
    try : 

        #if allowed to move
        if(not escape):
            print("***************************************")
            #''''''''''''''''''''''If the goal did not change'''''''''''''''''''''''''''''''''''''''''
            if closeEnough(x,x_old,THRESHOLD_SAME_GOAL) and closeEnough(y,y_old,THRESHOLD_SAME_GOAL): 
                '''
                    Goal did not change --> the path does not change neither
                    --> The task is, therefore, to check the position of the 
                        magnet in respect to the previously-set path 

                        --> If (posMagnet == posFirstNode) *** Arrived ***
                            ---> Then the new target is the next node in the path

                        --> ELse If (posMagnet == Goal)  *** Arrived --> to goal ***
                            (This condition should never be satisfied since it is already checked above)
                            ---> return 

                        --> Else *** not arrived ***
                            ---> Then don't change the target and leave the function                                            
                '''
                
                if(arrived):  #---> if (posMagnet == posFirstNodeOfTheRemainingPath)
                    arrived, path, at_rest = goalReached(x,y,arrived, path, towards_rest)

                elif(not arrived): # Do NOTHING --> Continue towards the same goal
                    return x_old,y_old,arrived, path,at_rest, zaber_dragging
                
            #''''''''''''''''''''''''''''IF THE GOAL CHANGED'''''''''''''''''''''''''''
            #Check whether the position is acceptable
            elif x > X_MIN and x < X_MAX and y > Y_MIN and y < Y_MAX: 
                arrived, path = setNewGoal(x,y,posX,posY,path,towards_rest, at_rest)
                at_rest = False
        
            else:
                print("WRONG INPUT2")
                return x_old,y_old,arrived,path, at_rest
            
        #-----------------TRIGGER DRAG BACK--------------
        else: 
            zaber_dragging = dragBack(zaber_dragging)
            path = []
            
    except ValueError:
        print("WRONG INPUT")
        return x_old, y_old,arrived,path, at_rest, zaber_dragging
    
    return x,y,arrived,path, at_rest, zaber_dragging
    

i=516
k=0
arrived = False
at_rest = True

#shortest path towards the goal
path=[]

'''
    Ce sleep est essentiel sinon la première commande envoyée à l'arduino est ignorée
'''
time.sleep(2) 

#graph.plotGraph()

#empty the serial before starting --> pour le fun
while(arduino.in_waiting):
    arduino.read()

import os
import glob
folder = f"/home/matthias/Videos/MotorControlRecording"

while True:
    if arduino.in_waiting:
        data = arduino.read()
        if data == b'T' and zaber_dragging:
            dragging = True
            print("Received:", dragging)
        
        elif data == b'F':
            if dragging and zaber_dragging:
                dragging = False

                # Zaber goes up
                command ="/1 move rel -85000\n"  
                print("ZZZZZZZZZZAAAAAAAAAAABBEEEEERRRRR")
                zaber.write(command.encode())
                zaber_dragging = False
                print("Received:", dragging)
                time.sleep(0.2)
        elif not zaber_dragging:
            if data==b'R':
                print("RECU")

            elif(data==b'A'):
                arrived=True
                print("RECEIVED ARRIVED    ",arrived)

            elif(data ==b'X'):
                    posX_bytes = arduino.read(4)

                    #posX = stepsToX(struct.unpack('l', posX_bytes)[0])
                    posX_temp = stepsToX(struct.unpack('<l', posX_bytes)[0])

                    #Normalement ce truc est inutile mais on ne sait jamais
                    #Je l'ai mis parce que je me suis trompé et j'envoyer l'adresse d'une variable locale
                    if(posX_temp < 30):
                        posX=posX_temp+START_X
                
                        #print("Received Long Values:", posX*659/4)
                        #time.sleep(0.5)

                        data=arduino.read()
                        if(data==b'Y'):
                            posY_bytes = arduino.read(4)
            
                            posY = stepsToY(struct.unpack('<l', posY_bytes)[0])+START_Y
                            #print("Received YYYYYYyyy:", posY*659/4)
                    

    #while(arduino.in_waiting):
        #arduino.read() 
    
    #image = 'python\image'+str(i)+'.jpg'
    #Juste pour avancer moins rapidement 
    if(k%5000==0):

#TO BE CHECKED --> k%5000 changed by sleep 0.5

        if(not dragging):# and not arduino.in_waiting):
            try:    
                list_files = glob.glob(os.path.join(folder, '*.jpg'))
                image = max(list_files, key=os.path.getctime)
                list_files.remove(image)
                image = max(list_files, key=os.path.getctime)
                #image = f"magnets/image{i}.jpg"
                #image = f"C:\\Users\\salim\\Documents\\Summer_in_the_lab-RAMDYA_LAB\\Magnets_2\\image{i}.jpg"
                print("iiiiii    ",image)
                balls_detection(image)
                i=i+1
                targetX,targetY,arrived,path, at_rest, zaber_dragging =  sendTarget(targetX,targetY,posX,posY,arrived,path, at_rest, zaber_dragging)
                
            except:
                print("Wrong image")
            #ICI DECIDER OU ALLER
            #time.sleep(0.2)
        time.sleep(0.5)  
    k=k+1
