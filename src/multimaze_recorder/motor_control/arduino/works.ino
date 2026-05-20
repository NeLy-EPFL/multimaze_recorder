  // Bounce.pde
// -*- mode: C++ -*-
//
// Make a single stepper bounce from one limit to another
//
// Copyright (C) 2012 Mike McCauley
// $Id: Random.pde,v 1.1 2011/01/05 01:51:01 mikem Exp mikem $

#include <AccelStepper.h>

#define DIR_PIN_X 5
#define STEP_PIN_X 3
#define INTERFACE_X 1
#define DIR_PIN_Y 9
#define STEP_PIN_Y 6
#define INTERFACE_Y 1

#define DELIMITER ','

#define RAIL_LENGTH -3517    //2.2 cm //!!!!!!!!!!!!!!!!!!! 



// Define a stepper and the PIns it will use
//AccelStepper stepper; // Defaults to AccelStepper::FULL4WIRE (4 PIns) on 2, 3, 4, 5
AccelStepper stepperX=AccelStepper(INTERFACE_X,STEP_PIN_X,DIR_PIN_X);
AccelStepper stepperY=AccelStepper(INTERFACE_Y,STEP_PIN_Y,DIR_PIN_Y);

long tirma=0;
bool dragBack(){

  // reduce y-speed
  stepperY.setMaxSpeed(1000);
  stepperY.setAcceleration(500);
  while(Serial.available()>0)
    Serial.read();

  //tells python that we enter in drag mode
  long y_temp =stepperY.currentPosition();
   Serial.write("T");
    //drag on y-axis

  while(stepperY.currentPosition() - y_temp > RAIL_LENGTH){
   stepperY.move(RAIL_LENGTH);
    stepperY.run();
  }
     Serial.write("T");
    //drag on y-axis
delay(400);
  //tells python that we left drag mode
  Serial.write("F");

  //reset speed
  stepperY.setMaxSpeed(8000);
  stepperY.setAcceleration(4000);
  return true;
}

void setup()
{  
    Serial.begin(115200);
    Serial.setTimeout(1);

    // Change these to suit your stepper if you want
    stepperX.setMaxSpeed(20000);
    stepperX.setAcceleration(14000);
    stepperY.setMaxSpeed(8000);
    stepperY.setAcceleration(4000);

}

//Store current position of the motors
long currX = 0;
long currY = 0;

//escape == 1 --> enters drag_back mode
int escape = 0;

int k = 0;

bool dir = true; //true --> x ; false -->y
bool arrived = false;
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

          /*if(x==0 && y ==0){
            x = stepperX.currentPosition();
            y = stepperY.currentPosition();
            Serial.write("W");
          }
          else {*/
            Serial.write("R");
            recu = true;
          Serial.write((byte*)&x, sizeof(long));
          //delay(500);
          //Serial.println(currY);
          Serial.write("y");
          Serial.write((byte*)&y, sizeof(long));
          Serial.write("e");
          if(!escape) 
            Serial.write("0");
          else Serial.write("1");          
        
          
        }
    } 
  
      if(escape==1){ 
        delay(50);
        bool done = false;
        Serial.write("T");
        done = dragBack();

        if (!done)
          Serial.write("e");

        escape = 0;
        x = stepperX.currentPosition();
        y = stepperY.currentPosition();
      }else{
          stepperX.moveTo(x);
          stepperY.moveTo(y);

          stepperX.run();

          if(dir and stepperX.currentPosition()== x)
            dir = false;
          if(!dir){
            stepperY.run();
          }
      } 

    if(k>10){
      long currX1 = stepperX.currentPosition();
      long currY1 = stepperY.currentPosition();
      recu = true;
      if(abs(currX - currX1) > 1000 || abs(currY - currY1)> 500){
        currX = currX1;
        currY = currY1;
        //Serial.println(currX);
        //Serial.println(currY);
        //if(Serial.available()==0){
          //Serial.println("+-+-+-+-+-+-");
          //Serial.println(currX);
        Serial.write("X");
        Serial.write((byte*)&currX, sizeof(long));
        //delay(500);
        //Serial.println(currY);
        Serial.write("Y");
        Serial.write((byte*)&currY, sizeof(long));
          //delay(100);
        //} 
      }
      else if (!arrived and stepperX.currentPosition()==x && stepperY.currentPosition()==y){
        arrived = true;
        currX=x;
        currY=y;
        //if(Serial.available()==0){
        //Serial.println("+-+-+-+-+-+-");
        //Serial.println(currX);
        Serial.write("A");
        //delay(50);
        Serial.write("X");
        Serial.write((byte*)&currX, sizeof(long));
        //delay(500);
        //Serial.println(currY);
        Serial.write("Y");
        Serial.write((byte*)&currY, sizeof(long));
        //delay(100);
        //} 
      }
      k=0;
    }else k++;

    
}
