// Define the pin connected to the optocoupler signal
#define CAMERA_PIN 3

// Initialise a fps variable to store the framerate
int fps;

// Initialise a duration variable to store the experiment duration
unsigned long duration;

// Variable to store the interval between image captures
int CAPTURE_INTERVAL;

// Variable to store the time of the last image capture
unsigned long lastCaptureTime = 0;

boolean  toggle1 = 0;

unsigned long readInteger() {
  unsigned long ret = 0;
  while (true) {
    while (Serial.available() < 1) {
      ; // Wait for data to be available
    }
    char newChar = Serial.read();
    if (newChar == '*') {
      break; // Stop reading when '*' is encountered
    }
    if (newChar != '*' && newChar > 47) {
      int newDigit = newChar - '0';
      ret = ret * 10;
      ret = ret + newDigit;
    }
  }
  return ret;
}

void setTimerInterrupts(int fps)
{  
  int prescale_8_CMR    = (16000000 / (16*fps)) -1; // For FPS going from 31 to 2000
  int prescale_1024_CMR = (16000000 / (512*fps)) -1; // For FPS going from 1 to 30

  TCCR1A = 0;// set entire TCCR1A register to 0
  TCCR1B = 0;// same for TCCR1B
  TCNT1  = 0;//initialize counter value to 0
  //Serial.println(prescale_8_CMR);
  //Serial.println(prescale_1024_CMR);
  // set compare match register
  if (prescale_8_CMR > 256 && prescale_8_CMR < 65,536) 
  {
    OCR1A  = prescale_8_CMR; // (must be <65536)
  }
  else
  {
    OCR1A  = prescale_1024_CMR;
  }
  // turn on CTC mode
  TCCR1B |= (1 << WGM12);

  // set prescaler 
  if (prescale_8_CMR > 256 && prescale_8_CMR < 65,536) 
  {
    // Set CS11 bit for 8 prescaler
    TCCR1B |= (1 << CS11);  
  }
  else
  {
    // Set CS10 and CS12 bits for 1024 prescaler
    TCCR1B |= (1 << CS12) | (1 << CS10); 
  }
 
  // enable timer compare interrupt
  TIMSK1 |= (1 << OCIE1A);
}

void setup() {
  // Set the camera pin as output
  pinMode(CAMERA_PIN, OUTPUT);

  // Initialize serial communication at 9600 baud
  Serial.begin(9600);

  // Send acknowledgment message
  Serial.println("Arduino Ready");

}

ISR(TIMER1_COMPA_vect)
{
  //timer1 interrupt 1Hz toggles pin 13 (LED)
  if (toggle1)
  {
    digitalWrite(CAMERA_PIN,HIGH);
    toggle1 = 0;
  }
  else
  {
    digitalWrite(CAMERA_PIN,LOW);
    toggle1 = 1;
  }
}

void loop() {
// Check if there's data available on the serial port
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    if (command == "start") {
      //Serial.print("start ok");
      fps = readInteger();
      duration = readInteger();   

   
      // If the command is "start", start capturing images
      Serial.print("Received updated fps value from Python: ");
      Serial.println(fps);
      Serial.print("Received updated duration value from Python: ");
      Serial.println(duration);

      // Temporarily disable interrupts
      noInterrupts();

      // Set up timer interrupts with the received fps value
      setTimerInterrupts(fps);

      // Re-enable interrupts
      interrupts();

      // Capture images for the specified duration
      unsigned long startTime = millis();
      
      while (millis() - startTime < duration * 1000) {
        // Just wait while the ISR handles the image captures
      }
      
      //delay(100);
      // After the duration has passed, stop capturing images
      TIMSK1 &= ~(1 << OCIE1A);
      digitalWrite(CAMERA_PIN, LOW);
      delay(500);
      // Send "done" message to Python script
      Serial.println("done");
    }
  }
}
