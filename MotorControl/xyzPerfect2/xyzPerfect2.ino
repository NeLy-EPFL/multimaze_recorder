#include <AccelStepper.h>

#define DIR_PIN_X 5
#define STEP_PIN_X 3
#define INTERFACE_X 1
#define DIR_PIN_Y 9
#define STEP_PIN_Y 6
#define INTERFACE_Y 1

#define DELIMITER ','

#define RAIL_LENGTH -3517    //2.2 cm

#define STEPPER_X_LIMIT 95923
#define STEPPER_Y_LIMIT 33573

AccelStepper stepperX=AccelStepper(INTERFACE_X,STEP_PIN_X,DIR_PIN_X);
AccelStepper stepperY=AccelStepper(INTERFACE_Y,STEP_PIN_Y,DIR_PIN_Y);

// Function that takes care of dragging back the balls
void dragBack(){
  
  // tells python that we enter in drag mode
  Serial.write("T");

  // reduce y-speed in order not to scare the fly
  stepperY.setMaxSpeed(1000);
  stepperY.setAcceleration(500);


  // drag on y-axis
   stepperY.move(RAIL_LENGTH);
   stepperY.runToPosition();

  // tells python that we left drag mode
  Serial.write("F");

  // reset speed
  stepperY.setMaxSpeed(8000);
  stepperY.setAcceleration(4000);
}

void setup()
{  
    Serial.begin(115200);
    Serial.setTimeout(1);

    stepperX.setMaxSpeed(20000);
    stepperX.setAcceleration(14000);
    stepperY.setMaxSpeed(8000);
    stepperY.setAcceleration(4000);

}

//Store current position of the motors
long currX = 0;
long currY = 0;

int escape = 0; //escape == 1 --> enters drag_back mode

int k = 0; // variable to send the values a little bit slower

bool dir = true; //true --> x ; false -->y
bool arrived = false;

//goal position
long x = 0;
long y = 0;

void loop()
{   
    bool recu = false;
     //Read instructions sent by python
     while (Serial.available() > 0) {
        //delay(30);
        String data = Serial.readStringUntil(DELIMITER);
        escape = data.toInt();
        delay(50);

        if (data.length() > 0 and !recu) {
          if (!escape) {
              // Read the two variables when the value is 0
              dir = true;
              arrived = false;
              x = Serial.readStringUntil(DELIMITER).toFloat();
              delay(50);
  
              y = Serial.readStringUntil(DELIMITER).toFloat();      
          }

          //SEND ACKNOWLEDGMENT
          Serial.write("R");
          recu = true;
          Serial.write((byte*)&x, sizeof(long));
          Serial.write("y");
          Serial.write((byte*)&y, sizeof(long));
          Serial.write("e");
          if(!escape) 
            Serial.write("0");
          else if (escape==1)
              Serial.write("1"); 
          else Serial.write("N");

          //DOUBLE CHECK -- Stop if exceeding the limit of the motors
          if(x>STEPPER_X_LIMIT)
             x = stepperX.currentPosition();
          if(y>STEPPER_Y_LIMIT)
             y = stepperY.currentPosition();
        }
    } 

   
    if(escape){ //DRAG_BACK
      delay(50);
        //tells python that we enter in drag mode
      Serial.write("T");
      long y_temp = stepperY.currentPosition();
      dragBack();

      //if it did not work, tell python (BUT DOSE NOT SEEM TO DO SO)
      if (stepperY.currentPosition() - y_temp > -100)
        Serial.write("f");

      escape = 0;
      x = stepperX.currentPosition();
      y = stepperY.currentPosition();
    }
    else if (escape == 0){ //go to X and Y
        stepperX.moveTo(x);
        stepperY.moveTo(y);
        
        stepperX.run();

        if(dir and stepperX.currentPosition()== x)
          dir = false;
        
        if(!dir){
          stepperY.run();
        }
    } 


    //SEND POSITION TO PYTHON
    if(k>10){
      long currX1 = stepperX.currentPosition();
      long currY1 = stepperY.currentPosition();
      recu = true;
      
      //This whole part is to avoid the approximations
      //if the motor is reasonably close to the goal position, just send the goal position
      
      if(abs(currX - currX1) > 1000 || abs(currY - currY1)> 500){
        currX = currX1;
        currY = currY1;
        Serial.write("X");
        Serial.write((byte*)&currX, sizeof(long));

        Serial.write("Y");
        Serial.write((byte*)&currY, sizeof(long));
      }
      else if (!arrived and stepperX.currentPosition()==x && stepperY.currentPosition()==y){
        arrived = true;
        currX=x;
        currY=y;
        Serial.write("A");
        Serial.write("X");
        Serial.write((byte*)&currX, sizeof(long));
        Serial.write("Y");
        Serial.write((byte*)&currY, sizeof(long));
      }
      k=0;
    }else k++;

    
}
