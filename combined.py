#pip install openpyxl
from penpyxl import Workbook #excel
import argparse
import os
import json
import logging

def combineData(directories):

    combined_data = {}
    logging.info( "Combining Arrays")
    for path in directories:
        with open(path) as json_file:
            data = json.load(json_file)
            logging.info("Formating array: \"{}\" from file: \"{}\"".format(data["arrayName"], path))
            # each array is named numerically from 1 going clockwise
            combined_data[int(data["arrayName"])] = data
    return combined_data

def getSettings(combined_data):

    #defaults
    settings = {}
    settings["RANGE"] = 72 # detection range in inches
    settings["HUMAN_TEMP_MAX"] = 99 # degrees F
    settings["HUMAN_TEMP_MIN"] = 88 # deg F
    settings["numArrays"] = 0
    settings["sampleRate"] = 0.0
    settings["initialTime"] = 0
    settings["sampleCount"] = 0

    settings["numArrays"] = len(combined_data)
    if settings["numArrays"] >= 1:
        logging.info( "All arrays successfully formatted")
    else:
        logging.error("No JSON files loaded")

    # get configuration settings
    logging.info("Checking configuration settings")

    try:
        settings["sampleRate"] = float(combined_data[1]["sampleRate"])
        settings["initalTime"] = int(combined_data[1]["initialTime"])
    except Exception as e:
        logging.error("Settings do not exist, check JSON: {}".format(e))

    # 1 -> end of array
    for i in range(1,settings["numArrays"]+1):

        # check for matching sample rates
        if float(combined_data[i]["sampleRate"])!= settings["sampleRate"]:
            logging.error("Inconsistent sample Rates")

        # keep latest initial time
        if settings["initialTime"] < int(combined_data[i]["initialTime"]):
            settings["initialTime"] = int(combined_data[i]["initialTime"])

        # increase by number of samples in each array
        settings["sampleCount"] += len(combined_data[i]["sample"])

    logging.info("Keeping latest starting time: {}".format(settings["initialTime"]))
    logging.info( "Sample Rate: {}".format(settings["sampleRate"]))
    logging.info("Total number of samples: {}".format(settings["sampleCount"]))
    return settings

def checkForContacts(combined_data, settings):
    logging.info("Checking array for potential contacts")
    # go through all arrays
    for array in range(1, settings["numArrays"]+1):
        # and all readings in each array
        for reading in combined_data[array]["sample"]:

            current_data = combined_data[array]["sample"][reading]
            if float(current_data["dist"]) <= settings["RANGE"] and settings["HUMAN_TEMP_MIN"] <= float(current_data["temp"]) <= settings["HUMAN_TEMP_MAX"]:
                    logging.debug("Contact Criteria met in array {}, reading {}: {}".format(array, reading, current_data))
                    current_data["contact"] = True
            else:
                current_data["contact"] = False

def checkDuration(combined_data, settings):
    contactCount = 0
    contactList = []  # static list of contact times
    contactDur = {}   # mutible dictionary of contact times and durations

    # go through all arrays
    for array in range(1, settings["numArrays"]+1):
        # and all readings in each array
        for reading in combined_data[array]["sample"]:
#	    print combined_data[array]["sample"][reading]["contact"]
            current_data = combined_data[array]["sample"][reading]
	    # if current reading is a contact]
            if current_data["contact"] == True:

		#PSEUDOCODE: establish base of contact chain and pass array number and start timestamp forward
		# whithin loop, once first contact == true event found: 
		    # current_data["chain_base"] = True
		    # current_data["chain_begin_sample"] = reading
		    # current_data["chain_begin_time"] = current_data["time"]
		    # current_data["chain_begin_array"] = array
		    # current_data["chain_end_time"] = current_data["time"]
		    # current_data["chain_end_array"] = array

		# continue looping, for each contact == true sample, check for a previous contact == true sample within window of time (same array first, then neigboring arrays)
		# if previous contact == true is found:
		    # current_data["chain_begin_time"] = combined_data[array<+-1>]["sample"][<reading# found in loop>]["chain_begin_time"]
		    # current_data["chain_begin_array"] = combined_data[array<+-1>]["sample"][<reading# found in loop>]["chain_begin_array"]
		    # combined_data[current_data["chain_begin_array"]]["sample"][current_data["chain_begin_sample"]]["chain_end_time"] = current_data["time"]
		    # combined_data[current_data["chain_begin_array"]]["sample"][current_data["chain_begin_sample"]]["chain_end_array"] = array

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

        logging.debug("Total number of Samples: {}".format(settings["sampleCount"]))
        logging.debug("Total number of Contacts: {}".format(contactCount))

        for i in range(0, len(contactDur)):
            logging.debug("Contact {}:  Start-time: {}  Duration: {}".format(i, float(contactDur[i][0]), float(contactDur[i][1])))

    #return a dictionary with all the important contact information
    return contactDur

def createExcel(contacts, settings):
    wb = Workbook(guess_types=True)

    #grab active worksheet
    ws = wb.active
    ws.title = "Title"

    #save overwrites existing file without warning
    wb.save("test.xlsx")


def process(args):

    #load JSON
    combined_data = combineData(args.directories)

    #configure settings
    settings = getSettings(combined_data)

    #Mark each reading whether contact or not
    checkForContacts(combined_data, settings)

    #find streaks of continuous contact
    contacts = checkDuration(combined_data, settings)

    #export data to excelsheet
    createExcel(contacts, settings)

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
