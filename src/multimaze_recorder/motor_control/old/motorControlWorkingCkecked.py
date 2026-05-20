import serial
import time
import math
import struct


#from inputimeout import inputimeout

import GraphNewUpdated as graph

#-------LIBRARIES FOR COMPUTER VISION------
import numpy as np
from skimage.io import imshow, imread
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from skimage.feature import match_template, peak_local_max
#-------------------------------------------

#Open the serial port to communicate with the arduino
arduino = serial.Serial(port='/dev/ttyACM1',  baudrate=115200, timeout=.1)

#Open the serial port to communicate with the Zaber motor
zaber = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)



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
final_target = 4

#Position of the magnet
START_X = 0
START_Y = 0
posMagnet = [START_X, START_Y]

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
    [[71,195, 7],[154,195,13],[245,195,19],[327,195,25],[417,195,31],[500,195, 37]], #top-left
    
    [[1565,195, 55],[1650,195,61],[1735,195,67],[1820,195,73],[1913,195,79],[2000,195,85]], #top_middle  
    
    [[3057,190,103],[3143,190,109],[3230,190, 115],[3315,190, 121],[3407,190, 127],[3492,190,133]], #top_right  
    
    [[71,1350,9],[154,1350,15],[245,1350,21],[327,1350,27],[417,1350,33],[500,1350,39]], #middle_left
    
    [[1565,1350,57],[1650,1350,63],[1735,1350,69],[1820,1350,75],[1913,1350,81],[2000,1350, 87]], #middle_middle
    
    [[3057,1350, 105],[3143,1350, 111],[3230,1350, 117],[3315,1350, 123] ,[3407,1350, 129],[3492,1350,135]], #middle_right 5 + 6.7
    
    [[71,2508,11],   [154,2508,17], [245,2508,23], [327,2508,29], [417,2508,35], [500,2508,41]], #bottom_left 17.25 + 6.4
    
    [[1565,2508,59],[1650,2508,65],[1735,2508,71],[1820,2508,77], [1913,2508,83],[2000,2508, 89]], #bottom_middle 8.25 + 6.5
    
    [[3057,2508,107],[3143,2508,113],[3230,2508, 119],[3315,2508, 125],[3407,2508, 131],[3492,2508, 137]] #bottom_right
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
ESCAPE_BACK = 1

GO_TO_GOAL = 0

def find_nearest_point(array, posMagnet):
    if array != []:
        nearest_point = array[0]
        nearest_point_pos = graph.getNodePosition(array[0])
        if len(array)>1:
            x = posMagnet[0]
            y = posMagnet[1]
            min = np.sqrt((nearest_point_pos[0] - x) ** 2 + (nearest_point_pos[1] - y) ** 2)
            for ar in array:
                pos = graph.getNodePosition(ar)
                d = np.sqrt((pos[0] - x) ** 2 + (pos[1] - y) ** 2)
                if(min>d):
                    min = d
                    nearest_point = ar
                    nearest_point_pos = pos
    return nearest_point, nearest_point_pos

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
def dragBack(zaber_dragging, wrong_input,stopped):
    '''
        Trigger drag back --> push the ball
    '''
    # Zaber goes down
    time.sleep(0.3)

    if not zaber_dragging or wrong_input or stopped:
        time.sleep(0.05)
        command ="/1 move rel 83000\n"
        time.sleep(0.05)
        zaber.write(command.encode())
        zaber_dragging = True
        data = f"{1}\n"
        time.sleep(0.05)
        print("arduino told to drag back   ",data)
        arduino.write(data.encode())  # Encode and send the data
    return zaber_dragging

def computerVisionInterpretation(posMagnet, zaber_dragging, wrong_input,stopped):
    if len(balls_ready) :
        rest = False
        '''
        If at least a ball reached its destination, then the goal of the magnet is the closest ball
            *If the magnet reached the final destination, then escape = 1 to trigger dragBack + remove the ball from the list of balls_ready
            *If the magnet is not at the final destination, then escape = 0 to allow the magnet to move towards the ball
        '''
        #Determine the closest ball_ready to the magnet --> Goal
        node, [x,y] = find_nearest_point(balls_ready,posMagnet) 

        #If the goal node is close enough to the magnet, then trigger drag_back 
        # and remove the ball from the list balls_ready 
        if closeEnough(x,posMagnet[0],THRESHOLD_MAGNET_ARRIVED) and closeEnough(y,posMagnet[1],THRESHOLD_MAGNET_ARRIVED):
            balls_ready.remove(node)
            print("CLOSE")
            zaber_dragging = dragBack(zaber_dragging, wrong_input,stopped)
        
    #If no ball reached a destination, go to rest --> go to the nearest X where the magnet can rest
    # --> y is set to the current posY 
    else:
        node = graph.find_nearest_rest(posMagnet)
        stopped = False
        rest = True

    return node,zaber_dragging, stopped, rest




def setGoal(path):
    '''
        Set new goal --> establish new shortest path towards this goal
        --> new target = first node of the shortest path
    '''              
        
    if path != []:  #New target = first node of the shortest path
        pos = graph.getNodePosition(path[0])
        real_target[0] = pos[0] - START_X
        real_target[1] = pos[1] - START_Y
        #remove first node of the path since the command to go towards will be sent now
        path.pop(0)

    return real_target, path



#Function to send the target to the robot
def sendTarget(real_target, final_target, posMagnet,arrived, path, zaber_dragging,wrong_input, stopped,pos_remove):
    
    final_target_old = final_target
    #********************COMPUTER VISION INTERPRETATION*************************
    try:
        final_target, zaber_dragging, stopped, rest = computerVisionInterpretation(posMagnet,zaber_dragging, wrong_input,stopped)
    except Exception:
        print("EXCEPTION 0")
        return real_target, final_target_old, arrived, path, zaber_dragging, stopped

    #********************GOAL ANALYSIS AND MOTORS CONTROL**********************
    try : 

        #if allowed to move
        if(not (zaber_dragging or wrong_input)):
            #''''''''''''''''''''''If the goal did not change'''''''''''''''''''''''''''''''''''''''''
            if final_target_old == final_target: 
                '''
                    Goal did not change --> the path does not change neither
                    --> The task is, therefore, to check the position of the 
                        magnet in respect to the previously-set path 

                        --> If (posMagnet == posFirstNode) *** Arrived ***
                            ---> Then the new target is the next node in the path

                        --> Else *** not arrived ***
                            ---> Then don't change the target and leave the function                                            
                '''
                
                if(arrived):  #---> if (posMagnet == posFirstNodeOfTheRemainingPath)
                    real_target, path = setGoal(path)
                    arrived = False

                elif(not arrived): # Do NOTHING --> Continue towards the same goal
                    if(not stopped or rest):
                        return real_target, final_target_old,arrived, path, zaber_dragging, stopped
                

            #''''''''''''''''''''''''''''IF THE GOAL CHANGED'''''''''''''''''''''''''''
            else :
                #Reset arrived to false 
                arrived = False
                path = graph.shortest_path(posMagnet,final_target)
                real_target, path = setGoal(path)
            
            data = f"{GO_TO_GOAL},{convertXtoSteps(real_target[0])},{convertYtoSteps(real_target[1])}\n"  
            print("goal sent to arduino   ",data)
            arduino.write(data.encode())  # Encode and send the data to the Arduino
            
    except ValueError:
        print("WRONG INPUT")
        return real_target, final_target_old, arrived,path, zaber_dragging, stopped
    
    return real_target, final_target,arrived,path, zaber_dragging, stopped
    

i=516
k=0
arrived = False

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


zaber_dragging = False
wrong_input = False
real_target = [0,0]
stopped = True
tirma = 0
pos_remove = [0,0]
while True:


    #while(arduino.in_waiting):
        #arduino.read() 
    
    #image = 'python\image'+str(i)+'.jpg'
    #Juste pour avancer moins rapidement 
    if(k%5000==0):
        print("*********")


        if(not dragging and not zaber_dragging):
            try:    
                list_files = glob.glob(os.path.join(folder, '*.jpg'))
                image = max(list_files, key=os.path.getctime)
                list_files.remove(image)
                image = max(list_files, key=os.path.getctime)
                
                #image = f"magnets/image{i}.jpg"
                #image = f"C:\\Users\\salim\\Documents\\Summer_in_the_lab-RAMDYA_LAB\\Magnets_2\\image{i}.jpg"
                print(image)
                balls_detection(image)
            except:
                print("Wrong image")
            i=i+1
            real_target, final_target,arrived,path,zaber_dragging, stopped =  sendTarget(real_target, final_target, posMagnet, arrived, path, zaber_dragging, wrong_input,stopped,pos_remove)
            time.sleep(0.1)


        time.sleep(0.5)  
        

            #ICI DECIDER OU ALLER
            #time.sleep(0.2)
            
    k=k+1
    if arduino.in_waiting:
        data = arduino.read()
        wrong_input = False
       

        if data == b'T' and zaber_dragging:
            dragging = True
            print("Arduino begins dragging back")
        elif data==b'y':
            yd_bytes = arduino.read(4)
            print("YD  ",stepsToY(struct.unpack('<l', yd_bytes)[0])+START_Y)
            
        elif data == b'F':
            if dragging and zaber_dragging:
                dragging = False
                # Zaber goes up
                command ="/1 move rel -83000\n"  
                zaber.write(command.encode())
                zaber_dragging = False
                print("Dragging back done by Arduino")

                time.sleep(0.2)
        elif data == b'f':
            print("ESCAPE")
            stopped = True
        elif not dragging:        
            if data==b'R':
                x_bytes = arduino.read(4)
                received_x = stepsToX(struct.unpack('<l', x_bytes)[0])+START_X
        
                data=arduino.read()
                if(data==b'y'):
                    y_bytes = arduino.read(4)

                    received_y = stepsToY(struct.unpack('<l', y_bytes)[0])+START_Y
                    data=arduino.read()
                    if(data==b'e'):
                        data=arduino.read()
                        print(data)
                        if(data==b'\x00' or data == b'0'):
                            escape = 0
                        elif(data==b'\x01' or data == b'1'):
                            escape = 1
                        
                    if((not escape and not zaber_dragging) or (escape and zaber_dragging) and closeEnough(received_x, real_target[0], 0.2) and closeEnough(received_y, real_target[1], 0.2)):
                        if(not escape):
                            print("Arduino going towards ",real_target)
                        if(escape):
                            print("Arduino acknowledges drag back")
                            dragging = True
                    else:
                        print("Arduino received wrong input ",[escape, received_x, received_y]," instead of ",[zaber_dragging,real_target])
                        wrong_input = True
            elif data==b'W':
                print("Wrong input")
                wrong_input=True

            elif(data==b'A'):
                arrived=True
                print("Arduino sent ARRIVED")
            
            elif(data ==b'X'):
                    pos_remove = posMagnet.copy()
                    posX_bytes = arduino.read(4)

                    #posX = stepsToX(struct.unpack('l', posX_bytes)[0])
                    posX_temp = stepsToX(struct.unpack('<l', posX_bytes)[0])

                    #Normalement ce truc est inutile mais on ne sait jamais
                    #Je l'ai mis parce que je me suis trompé et j'envoyer l'adresse d'une variable locale
                    if(posX_temp < 30):
                        
                        posMagnet[0]=posX_temp+START_X
                

                        data=arduino.read()
                        if(data==b'Y'):
                            posY_bytes = arduino.read(4)
            
                            posMagnet[1] = stepsToY(struct.unpack('<l', posY_bytes)[0])+START_Y
                    if(closeEnough(pos_remove[0],posMagnet[0],0.02) and closeEnough(pos_remove[1],posMagnet[1],0.02)):
                        tirma = tirma+1
                        if(tirma > 5):
                            print("SAME POSITION")
                            stopped = True
                    elif ((real_target[0] - pos_remove[0])*(posMagnet[0]-pos_remove[0]) < -0.25 or 
                            (real_target[1] - pos_remove[1])*(posMagnet[1]-pos_remove[1]) < -0.25):
                        tirma = tirma+1
                        if(tirma > 5):
                            print("OPPOSITE DIRECTION")
                            print(real_target)
                            print(pos_remove)
                            print(posMagnet)
                            stopped = True
                    else: 
                        stopped = False
                        tirma =0
