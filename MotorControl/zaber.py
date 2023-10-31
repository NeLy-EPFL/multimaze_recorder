import serial

zaber = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

# Send a command to the Zaber motor

#command = "/home\n" 

command="/move abs 433000\n"

#command ="/1 move rel -100000\n"  # Replace this with the actual command you want to send
zaber.write(command.encode())

# Read the response from the Zaber motor
response = zaber.read(100)  # Replace 100 with an appropriate buffer size

if response:
    print("Received:", response)
else:
    print("No response within the timeout period.")

zaber.close()  # Close the serial port when done