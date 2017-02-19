# Base Code reference-
# http://www.raspberrypi-spy.co.uk/tag/ultrasonic/
# Modifications by Paul Garmer and Chris Smith

# -----------------------
# Import required Python libraries
# -----------------------
from __future__ import print_function
from picamera import PiCamera
import RPi.GPIO as GPIO
from datetime import datetime
import time
import json
import os
import smbus
import sys
import getopt
import pigpio

# -----------------------
# Globals
# -----------------------
GPIO.cleanup()
# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# Define GPIO to use on Pi
GPIO1_TRIGGER = 23
GPIO1_ECHO    = 24
GPIO2_TRIGGER = 22
GPIO2_ECHO    = 25

# Set pins as output and input
GPIO.setup(GPIO1_TRIGGER,GPIO.OUT)  # Trigger
GPIO.setup(GPIO1_ECHO,GPIO.IN)      # Echo
GPIO.setup(GPIO2_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO2_ECHO, GPIO.IN)

# Set trigger to False (Low)
GPIO.output(GPIO1_TRIGGER, False)
GPIO.output(GPIO2_TRIGGER, False)

# PigPio defaults
pi = pigpio.pi()
version = pi.get_pigpio_version()
# OMRON definitions
i2c_bus = smbus.SMBus(1)
OMRON_1 = 0x0a
OMRON_BUFFER_LENGTH = 35
temp_data = [0]*OMRON_BUFFER_LENGTH
handle = pi.i2c_open(1, 0x0a)
# pi.i2c_close(1, OMRON_1)

# Speed of sound in cm/s at temperature
temperature = 20
speedSound = 33100 + (0.6*temperature)

# Camera variables
camera = PiCamera()
camera.rotation = 180
camera.resolution = (1024, 768)
camera.start_preview()
#  time.sleep(1)

# Sampling parameters
readingNum = 0
now = datetime.now()
initTime = now.strftime("%H%M%S%f")
pictureTimer = initTime
tempTimer = initTime
print(initTime)

#  JSON storage for variables
json_data = {} # Dictionary
json_data['sample'] = {}
json_data['initialTime'] = format(initTime)
json_data['sampleRate'] = '.2'
json_data['arrayName'] = '1'


# Allow module to settle
#  time.sleep(0.5)

# -----------------------
# Function Definitions
# -----------------------
def POST():
  #  This function will perform a Power On Self Test to make sure the env is
  #  ready for action
  return 1

def setUp():
  #  This function will set up logging. It will check what day it is. If there
  #  is a log file for today, it will append all future logs to that file. If
  #  there is not a file for today, it will create a new log file to write to.
  now = datetime.now()
  day = now.strftime("%Y%m%d")
  path = '/var/log/contacts/'
  if not os.path.exists(path):
    os.makedirs(path)
  file = day + '.log'
  file_name = path + file

  return file_name

def cSetUp():
  now = datetime.now()
  day = now.strftime("%Y%m%d")
  path = '/var/log/pictures/' + day
  if not os.path.exists(path):
    os.makedirs(path)

  return path

def measure(TRIGGER, ECHO):
  # This function measures a distance
  GPIO.output(TRIGGER, True)
  # Wait 10us
  time.sleep(0.0001)
  GPIO.output(TRIGGER, False)
  while GPIO.input(ECHO)==0:
    start = time.time()
    # print('waiting for echo')

  while GPIO.input(ECHO)==1:
    stop = time.time()

  elapsed = stop-start
  distance = (elapsed * speedSound)/2

  return distance

def measure_average(GPIO_TRIGGER, GPIO_ECHO):
  #TODO reduce number of decimal places
  # This function takes 3 measurements and
  # returns the smallest distance.
  distance1=measure(GPIO_TRIGGER, GPIO_ECHO)
  print("Distance1 : {0:5.1f}".format(distance1))
  time.sleep(0.0001)
  distance2=measure(GPIO_TRIGGER, GPIO_ECHO)
  print("Distance2 : {0:5.1f}".format(distance2))
  time.sleep(0.0001)
  distance3=measure(GPIO_TRIGGER, GPIO_ECHO)
  print("Distance3 : {0:5.1f}".format(distance3))


  if distance1 <= distance2:
    if distance1 <= distance3:
      distance = distance1
      return distance
    else:
      distance = distance3
      return distance
  else:
    if distance2 <= distance3:
      distance = distance2
      return distance
    else:
      distance = distance3
      return distance
  
  
  #"drop" values of under 6cm and over 2000cm to smooth error collection
    if ((distance < 6) or (distance > 2000)):
      distance = 9999
  
  #rounds to whole number
  distance = math.round(distance, 0)
  
  return distance

def picture(file_path):
  now = datetime.now()
  time = now.strftime("%H%M%S%f")
  pic_name = 'pic-' + time + '.jpg'
  camera_path = os.path.join(file_path, pic_name)
  camera.capture(camera_path)
  camera.stop_preview()

  return

def getData(now, distance1, distance2, temp_data):
  # store data in temp dict
  data = {}
  data['time'] = format(now)
  data['dist1'] = format(distance1)
  data['dist2'] = format(distance2)
  data['temp'] = temp_data

  return data

def saveData(file_name, json_data):
  # save json_data to file
  #  data = json_data.decode("utf8")
  with open(file_name, "w") as my_file:
    my_file.write(json.dumps(json_data))
    my_file.flush()

  return 1

def decodeTempData(raw_data):
    temp = {}
    temp["PTAT"]= 256*raw_data[1]+ raw_data[0] #reference temp inside the sensor

    for i in range(0,15): #4x4 grid of temps
        #[0] = [1]+[0], [1] = [3]+[2], etc. /10 puts the decimal in place
        temp[i] = (256*raw_data[2*i+3]+raw_data[2*i+2])/10 #in deg C with 1/10 deg C precision

    #temp["PEC"] = raw_data[35] #packet error check code, based on SM Bus specification

    return temp
# -----------------------
# Main Script
# -----------------------

# Wrap main content in a try block so we can
# catch the user pressing CTRL-C and run the
# GPIO cleanup function. This will also prevent
# the user seeing lots of unnecessary error
# messages.
POST()

# Log File
file_name = setUp()
file_path = cSetUp()

try:
  while True:
    # Get current time
    now = datetime.now()
    sampleTime = now.strftime("%H%M%S%f")
    print(str(now.strftime("%H:%M:%S.%f")))
    # TODO: Fix time so script doesn't end early!
    if (int(sampleTime) - int(initTime) > 12000000):#shut off after x hours
      break
    if (int(sampleTime) - int(pictureTimer) >= 60):#take picture every 60 ms
      pictureTimer = now.strftime("%H%M%S%f")
      picture(file_path)
    distance = measure_average(GPIO1_TRIGGER, GPIO1_ECHO)
    distance1 = measure_average(GPIO2_TRIGGER, GPIO2_ECHO)
    if (int(sampleTime) - int(tempTimer) > 25): #every 25ms take temp
      # TODO: At times OMRON returns -81 bits read
      handle = pi.i2c_open(1, 0x0a)
      result = i2c_bus.write_byte(OMRON_1, 0x4c)
      (bytes_read, temp_data) = pi.i2c_read_device(handle, len(temp_data))
      pi.i2c_close(handle)
    print("Sample Time: " + now.strftime("%H%M%S%f"))
    print("Lowest Distance : {0:5.1f}".format(distance))
    print("Lowest Distance : {0:5.2f}".format(distance1))
    print("Bytes read from Omron D6T: " + str(bytes_read))
    print("Data read from Omron D6T : ")
    for x in range(bytes_read):
      print(temp_data[x])
    temperature = decodeTempData(temp_data)

    json_data['sample'][format(readingNum)] = getData(sampleTime, distance, distance1, temperature)
    saveData(file_name, json_data)
    readingNum += 1
    #  time.sleep(.25)

except KeyboardInterrupt:
  # User pressed CTRL-C
  print('Stopping process')
  # Reset GPIO settings
  GPIO.cleanup()
  #  pi.i2c_close(handle)
  pi.stop()
