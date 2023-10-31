import serial
import time
import math
import struct
#from inputimeout import inputimeout



arduino = serial.Serial(port='/dev/ttyACM1',  baudrate=115200, timeout=.1)

targetX=0
targetY=0
posX=0
posY=0
escape=0

dragging=False

balls = [
    [0,0,1,1], [1.5, 0, 1.5, 1]
]

REV = 1600
RAYON = 1.6
EMPIRICAL = 5.02

########## EVIDEMMENT CHANGER ###########
X_MIN = -30
X_MAX = 150
Y_MIN = -21
Y_MAX = 21

RAIL_LENGTH = 1.2
RAIL_LENGTH_LAT = 0.2
#########################################


def convertXtoSteps(x):
    return int((2*EMPIRICAL*x/(RAYON*math.pi))*REV)  #x in cm

def convertYtoSteps(y):
    return int(((EMPIRICAL*y/(RAYON*math.pi))*REV))  #y in cm

def stepsToX(s):
    return (RAYON*math.pi*s)/(2*EMPIRICAL*REV) #cm

def stepsToY(s):
    return (RAYON*math.pi*s)/(EMPIRICAL*REV)  #cm






#---------------------SEND TARGET----------------
ball_detected = False 
#ball_detected --> true if computer vision detects a ball

def sendTarget(x,y):
    x_old=x
    y_old=y
    if not ball_detected :
        try:
            #d = inputimeout("Enter a numberd: ",timeout = 5)
            #x = inputimeout("Enter a number1: ",timeout = 5)
            #y = inputimeout("Enter a number2: ",timeout = 5)
            escape = input("Enter a numberd: ")
            if int(escape)== 0:  #Ce truc va disparaâitre quand il n'y aura plus d'input donc 
                            #pour le moment, on peut laisser cette mocheté
                x = input("Enter a number1: ")
                y = input("Enter a number2: ")

        except Exception:
            return
    else:
        '''CONDITION à DETERMINER QUAND S'ÉCHAPPER À GAUCHE A GAUCHE'''
        '''if d :'''
        escape = 1
        '''else:'''
        escape = -1
        
    try : 
        escape = int(escape)
        if(not escape):
            x = float(x)
            y = float(y)
            if(abs(x-x_old)<.001 and abs(y-y_old)<0.001):
                return x_old, y_old
            if x > X_MIN and x < X_MAX and y > Y_MIN and y < Y_MAX:
                print("CORRECT INPUT") 
                #x = convertXtoSteps(x)
                #y = convertYtoSteps(y)
                time.sleep(0.1)
                data = f"{escape},{convertXtoSteps(x)},{convertYtoSteps(y)}\n"  # Format the data as per the expected delimiter                   
            else:
                print("WRONG INPUT2")
                return x_old, y_old  #CHECK --> BIZARRE

        elif(escape ==1 or escape ==-1): 
            data = f"{escape}\n"
        else:
            print("WRONG INPUT d")
            return x_old, y_old  #CHECK --> BIZARRE
        arduino.write(data.encode())  # Encode and send the data
        exit()
    except ValueError:
        print("WRONG INPUT")
        return x_old,y_old  #CHECK --> BIZARRE
    return x,y
    
#coef=0
time.sleep(2)
while True:

    #print("ard------")
    #print(arduino.in_waiting)
    #print(arduino.read())
    #while(arduino.in_waiting):
    if arduino.in_waiting:
        data = arduino.read()

        if data == b'T':
        #if arduino.in_waiting >=1 and  arduino.in_waiting<7:
            #data_type = arduino.read().decode()
            dragging = True#arduino.read()))
            # Process the received boolean values
            print("Received:", dragging)
            #if not dragging:
                #x=x+coef*RAIL_LENGTH_LAT
                #y=y+RAIL_LENGTH
                #coef=0
            time.sleep(0.5)
        
        elif data == b'F':
            dragging = False#arduino.read()))
            # Process the received boolean values
            print("Received:", dragging)

        elif data==b'R':
            print("RECU")
            

        
        #elif arduino.in_waiting >3 and not dragging:
            #elif data_type == 'l':  # Long values
        elif(data ==b'X'):
                #data=arduino.read()
                #if(data==b'X'):

                posX_bytes = arduino.read(4)

                posX = struct.unpack('<l', posX_bytes)[0]
                #long_value2 = struct.unpack('l', long_value2_bytes)[0]

                print("Received Long Values:", stepsToX(posX))#, stepsToY(long_value2))
                #time.sleep(5)

                data=arduino.read()
                if(data==b'Y'):
                    posY_bytes = arduino.read(4)
    
                    posY = struct.unpack('<l', posY_bytes)[0]
                    #long_value2 = struct.unpack('l', long_value2_bytes)[0]

                    print("Received YYYYYYyyy:", stepsToY(posY))#, stepsToY(long_value2))
        
    #print("------")'''

    #time.sleep(5)     
    #ICI COMPUTER VISION
    #JE PENSE QU'A UN CERTAIN MOMENT IL FAUT AVOIR UN TABLEAU QUI STOCKE LES BALLES QUI SONT DEJA ARRIVEES
    #arduino.flushInput()

    if(not dragging):# and not arduino.in_waiting):
        targetX,targetY =  sendTarget(targetX,targetY)
        #time.sleep(2)
        #ICI DECIDER OU ALLER

        #Ceci n'est pas à ignorer
        #------- algo pour envoyer go_in_rest
        '''
        if(not ball_detected and not in_rest(x,y))
            x,y = go_in_rest();
        '''
        #NE PAS IGNORER



        #sendTarget()
        #time.sleep(0.01)

    '''
    while True:
        if arduino.in_waiting > 0:
            dragging = bool(ord(arduino.read()))
            # Process the received boolean values
            print("Received:", dragging)
            if(not dragging):
                break
        elif arduino.in_waiting <= 0 and not dragging:
            break
    '''
    '''
    if(not ball_detected and not in_rest(x,y))
        go_in_rest();
    '''
 

    