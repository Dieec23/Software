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

def measure():
  # This function measures a distance
  GPIO.output(GPIO_TRIGGER, True)
  # Wait 10us
  time.sleep(0.0001)
  GPIO.output(GPIO_TRIGGER, False)
  start = time.time()

  while GPIO.input(GPIO_ECHO)==0:
    start = time.time()

  while GPIO.input(GPIO_ECHO)==1:
    stop = time.time()

  elapsed = stop-start
  distance = (elapsed * speedSound)/2

  return distance

def measure_average():
  # This function takes 3 measurements and
  # returns the smallest distance.

  distance1=measure()
  print("Distance1 : {0:5.1f}".format(distance1))
  time.sleep(0.0001)
  distance2=measure()
  print("Distance2 : {0:5.1f}".format(distance2))
  time.sleep(0.0001)
  distance3=measure()
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

  return distance

def picture(file_path):
  now = datetime.now()
  time = now.strftime("%H%M%S%f")
  pic_name = 'pic-' + time + '.jpg'
  camera_path = os.path.join(file_path, pic_name)
  camera.capture(camera_path)
  camera.stop_preview()

  return

def getData(now, distance, temp_data):
  # store data in temp dict
  data = {}
  data['time'] = format(now)
  data['dist'] = format(distance)
  data['temp'] = format(temp_data)

  return data

def saveData(file_name, json_data):
  # save json_data to file
  with open(file_name, "a+") as my_file:
    my_file.write(json.dumps(json_data))
    my_file.flush()

  return 1

# -----------------------
# Globals
# -----------------------
POST()

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# Define GPIO to use on Pi
GPIO_TRIGGER = 23
GPIO_ECHO    = 24

# OMRON definitions
i2c_bus = smbus.SMBus(1)
OMRON_1 = 0x0a
OMRON_BUFFER_LENGTH = 35
temp_data = [0]*OMRON_BUFFER_LENGTH

# PigPio defaults
pi = pigpio.pi()
version = pi.get_pigpio_version()
# handle = pi.i2c_open(1, 0x0a)

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
curTime = initTime
print(initTime)

#  JSON storage for variables
json_data = {} # Dictionary
json_data['sample'] = {}
json_data['initialTime'] = format(initTime)
json_data['sampleRate'] = '.2'
json_data['arrayName'] = '1'

# Log File
file_name = setUp()
file_path = cSetUp()

# Set pins as output and input
GPIO.setup(GPIO_TRIGGER,GPIO.OUT)  # Trigger
GPIO.setup(GPIO_ECHO,GPIO.IN)      # Echo

# Set trigger to False (Low)
GPIO.output(GPIO_TRIGGER, False)

# Allow module to settle
#  time.sleep(0.5)

# -----------------------
# Main Script
# -----------------------

# Wrap main content in a try block so we can
# catch the user pressing CTRL-C and run the
# GPIO cleanup function. This will also prevent
# the user seeing lots of unnecessary error
# messages.
try:
  while True:
    # Get current time
    now = datetime.now()
    sampleTime = now.strftime("%H%M%S%f")
    if (int(sampleTime) - int(initTime) > 12000000):
      break
    if (int(sampleTime) - int(curTime) >= 60):
      curTime = now.strftime("%H%M%S%f")
      picture(file_path)
    distance = measure_average()
    handle = pi.i2c_open(1, 0x0a)
    result = i2c_bus.write_byte(OMRON_1, 0x4c)
    (bytes_read, temp_data) = pi.i2c_read_device(handle, len(temp_data))
    pi.i2c_close(handle)
    print("Sample Time: " + now.strftime("%H%M%S%f"))
    print("Lowest Distance : {0:5.1f}".format(distance))
    print("Bytes read from Omron D6T: " + str(bytes_read))
    print("Data read from Omron D6T : ")
    for x in range(bytes_read):
      print(temp_data[x])

    json_data['sample'][format(readingNum)] = getData(now, distance, temp_data)
    saveData(file_name, json_data)
    readingNum += 1
    #  time.sleep(.25)

except KeyboardInterrupt:
  # User pressed CTRL-C
  print('Stopping process')
  # Reset GPIO settings
  GPIO.cleanup()
  pi.i2c_close(handle)
  pi.stop()
