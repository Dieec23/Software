#pip install openpyxl
from openpyxl import Workbook #excel
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

	    current_data["chain_base"] = False
	    current_data["chain_begin_time"] = 0.00
	    current_data["chain_begin_array"] = array
	    current_data["chain_end_time"] = 0.00
	    current_data["chain_end_array"] = array
	    current_data["chain_begin_sample"] = 0

#    print combined_data[1]["sample"][unicode(20)]["chain_end_time"]	

def checkDuration(combined_data, settings):
    contactCount = 0
    contactList = []  # static list of contact times
    contactDur = {}   # mutible dictionary of contact times and durations

    # go through each  array to build chains
    for array in range(1, settings["numArrays"]+1):
        # all readings in each array
        for reading in combined_data[array]["sample"]:
            current_data = combined_data[array]["sample"][reading]
	    # if current reading is a contact
            if current_data["contact"] == True:
		#check previous samples
		i = 1
		#j = 1
		#k = 1
		while (float(current_data["time"]) - float(combined_data[array]["sample"][unicode(int(reading)-i)]["time"]) <= .30):
		    prev_data = combined_data[array]["sample"][unicode(int(reading)-i)]
		    if prev_data["contact"] == True:
			current_data["chain_begin_sample"] = prev_data["chain_begin_sample"]
		    	current_data["chain_begin_time"] = float(prev_data["chain_begin_time"])
		    	current_data["chain_begin_array"] = prev_data["chain_begin_array"]
		        combined_data[int(current_data["chain_begin_array"])]["sample"][unicode(current_data["chain_begin_sample"])]["chain_end_time"] = float(current_data["time"])
		        combined_data[int(current_data["chain_begin_array"])]["sample"][unicode(current_data["chain_begin_sample"])]["chain_end_array"] = array
			break
		    elif float(current_data["time"]) - float(combined_data[array]["sample"][unicode(int(reading)-i-1)]["time"]) > .30 and prev_data["contact"] == False:
				
			#establish as base of next chain
			contactCount += 1
			current_data["chain_base"] = True
		        current_data["chain_begin_sample"] = reading
		        current_data["chain_begin_time"] = current_data["time"]
		        current_data["chain_begin_array"] = array
		        current_data["chain_end_time"] = current_data["time"]
		        current_data["chain_end_array"] = array
			break
		    else:
		        i += 1

        for reading in combined_data[array]["sample"]:
            current_data = combined_data[array]["sample"][reading]
	    if current_data["contact"] == True:
		logging.debug("Sample: {}, bt: {} et: {}, bs:{}".format(reading, current_data["chain_begin_time"], current_data["chain_end_time"], current_data["chain_begin_sample"]))

        logging.debug("Total number of Samples: {}".format(settings["sampleCount"]))
        logging.debug("Total number of Contacts: {}".format(contactCount))


    #return a dictionary with all the important contact information
    return contactDur

def createExcel(contacts, settings):
    wb = Workbook()

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
