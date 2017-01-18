import argparse
import os
import json
import logging
                                    
def process(args):
  
  RANGE = 72 # detection range in inches
  HUMAN_TEMP_MAX = 99 # degrees F
  HUMAN_TEMP_MIN = 88 # deg F
  numArrays = 0
  sampleRate = 0.0
  initialTime = 0

  sampleCount = 0
  contactCount = 0
  contactList = []  # static list of contact times
  contactDur = {}   # mutible dictionary of contact times and durations
  
  # combine JSON files
  combined_data= {}  
 
  for s in args.directories:
    
    with open(s) as json_file:
      
      data = json.load(json_file)
      logging.info("Formating array: \"{}\" from file: \"{}\"".format(data["arrayName"], s)) 
      # each array is named numerically from 1 going clockwise
      combined_data[int(data["arrayName"])] = data
  
  numArrays = len(combined_data)
  if numArrays >= 1:
    logging.info( "All arrays successfully formatted")
  else:
    logging.error("No JSON files loaded")
  
  # get configuration settings
  logging.info("Checking configuration settings")
  
  
  try:
    sampleRate = float(combined_data[1]["sampleRate"])
    initalTime = int(combined_data[1]["initialTime"])
  except Exception as e:
    logging.error("Settings do not exist, check JSON: {}".format(e))
 
  # 1 -> end of array
  for i in range(1,numArrays+1):
    
    # check for mathinc sample rates
    if float(combined_data[i]["sampleRate"])!= sampleRate:
      logging.error("Inconsistent sample Rates")
    
    # keep latest initial time 
    if initialTime < int(combined_data[i]["initialTime"]):
      initialTime = int(combined_data[i]["initialTime"])

    # increase by number of samples in each array
    sampleCount += len(combined_data[i]["sample"])
 
  logging.info("Keeping latest starting time: {}".format(initialTime))
  logging.info( "Sample Rate: {}".format(sampleRate))  
  logging.info("Total number of samples: {}".format(sampleCount))
  logging.info("Checking array for potential contacts")
  # go through all arrays
  for array in range(1, numArrays+1):
    # and all readings in each array
    for reading in combined_data[array]["sample"]:

      current_data = combined_data[array]["sample"][reading]
      if float(current_data["dist"]) <= RANGE:
        if HUMAN_TEMP_MIN <= float(current_data["temp"]) <= HUMAN_TEMP_MAX:
          logging.debug("Contact Criteria met in array {}, reading {}: {}".format(array, reading, combined_data[array]["sample"][reading]))
          current_data["contact"] = True
          contactList.append(float(current_data["time"]))
  logging.info("Checking contact durations")

  contactList.sort()
  print contactList
  #initialize first contact     #(I know there is a more efficient way to implement 
  time = [contactList[0],0.0] # this, however I am still learning python and 
  contactDur[0] = time    # it is a work in progress...)
  contactDur[0][1] = 0.0
  contactCount += 1   # this also assumes there IS a contact

  # generate list of initial contact times, and corresponding durations
  for i in range(1,len(contactList)):
    if (contactList[i] == (contactList[i-1] + 0.2)):
      contactDur[contactCount-1][1] += 0.2
    else:
      time = [contactList[i], 0.0]
      contactDur[contactCount] = time
      contactDur[contactCount][1] = 0.0
      contactCount += 1

  logging.debug("Total number of Samples: {}".format(sampleCount))
  logging.debug("Total number of Contacts: {}".format(contactCount))

  for i in range(0, len(contactDur)):
    logging.debug("Contact {}:  Start-time: {}  Duration: {}".format(i, float(contactDur[i][0]), float(contactDur[i][1]))) 
                                          
def main():
                                        
  parser = argparse.ArgumentParser(description="description of the program")
                                                                                 
  subparsers = parser.add_subparsers()
                                                                                   
  # instantiate the subfunctions that we provide
  # for now the only one is to process data
                                                                                       
  subparser_process = subparsers.add_parser("process", help="description")
                                                                                        
  # arguments for sub-functions
  
  # pass as many json files as needed
  subparser_process.add_argument("directories", 
                                 help="include all json files", 
                                 nargs="+",
                                 )
                                 
  subparser_process.add_argument('-l', '--log-level',
                              choices=['debug', 'info', 'warning'],
                              metavar='',
                              default="info",
                              help="set log output level "
                              "(choices: %(choices)s "
                              "(default: %(default)s)")
  
  
  #apply defaults
  subparser_process.set_defaults(func=process)                                                                                          
  #instantiate args
  args = parser.parse_args()                                                                                       
  #enable logging
  logging.basicConfig(format='[%(levelname)s][%(asctime)s]: %(message)s',
                      datefmt='%m/%d/%Y %I:%M:%S %p',
                      handlers=[logging.StreamHandler()],
                      level=args.log_level.upper())
  
  #call function
  status = args.func(args)
  
                                                                                          
# once everything is defined launch the main loop
if __name__ == '__main__':
  main()
