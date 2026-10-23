import traceback
import json
import logging
from datetime import datetime
import ntplib  # require pip nstall ntplib
from dateutil.tz import gettz
from const import (
    CONST_DEFAULT_TIMESTAMP as DEFAULT_TIMESTAMP,
    CONST_SENSOR_NAME as SENSOR_NAME,
    CONST_SENSOR_TAG as SENSOR_TAG,
    CONST_SENSOR_TIME as SENSOR_TIME,
    CONST_SENSOR_VALUE as SENSOR_VALUE,
    CONST_SENSOR_VALUES as SENSOR_VALUES,
    CONST_SENSORDB_FILENAME as SENSORDB_FILENAME,
    CONST_SERVER_NTP_SERVER as SERVER_NTP_SERVER,
    CONST_SERVER_TIME_FORMAT as SERVER_TIME_FORMAT,
    CONST_SERVER_TIME_ZONE as SERVER_TIME_ZONE,
)

#
#  Provides list of config parameters
#
# def getConfigParameters():
#    return([SENSORDB_FILENAME])


#########################################################
#
# get_NPT_time
#
# Parameters:
#   local_config, DICT of configuration
#
# Returns:
#   ntp time in UTC, in format DEFAULT_TIME_FORMAT='%d.%m.%Y %H:%M:%S'
#       inheretd from local_config
#
#########################################################
def get_NPT_time(local_config, logging):
    ntp_client = ntplib.NTPClient()
    response = ntp_client.request(local_config[SERVER_NTP_SERVER])
    tzLocal = gettz(local_config[SERVER_TIME_ZONE])
    unixTime = response.tx_time
    pythonTime = datetime.fromtimestamp(unixTime, tz=tzLocal)
    return pythonTime.strftime(local_config[SERVER_TIME_FORMAT])


#
#  Function that updates the file with current temperture from a given sensor
#
#  Required input structure
#  {SENSOR_ID:"name of sensor",SENSOR_VALUE:"gauge value of sensor",SENSOR_TIME:"string with timestamp"}
#  Lookup apiserverconstants for correct names in structure
#
#  Required file structure
#
#   JSON Array with sensor values
#   Format {"sensorname":"name of sensor","sensorvalues" :{"value1":"value1","value2":"value2","timestamp":"time"}}
#   Example {"sensorname":"testsensor1","sensorvalues":{"temp":"3.14","timestamp":"23/04-24 12:00:01.37"}}
def sensorSave(config, sensorvalues, logger):
    filename = config[SENSORDB_FILENAME]
    try:
        #
        # Get current values
        #
        with open(filename, "r") as current_sensor_file:
            sensorDB = json.loads(current_sensor_file.read())

    except FileNotFoundError as fnfe:
        #
        # First time, Allocate empty list
        #
        sensorDB = []  # new ARRAY
    except Exception as e:  # Catch any other I/O error
        logger.error("General Error reading sensorfile: " + filename)
        logger.error(traceback.format_exc())
        return -1
    #
    # Verify that the alltemp structure is an array
    #
    if not isinstance(sensorDB, list):
        logger.error("SensorDb has incorrect JSON structure")
        return -2
    #
    # Build json structure
    # And replace old structure
    # As current values are the only that is of interest
    #
    # iterate over alltemp and find sensorid, if not found, append it
    #
    found = False
    sensor_name = sensorvalues[SENSOR_NAME]
    newvalues = sensorvalues[SENSOR_VALUES]
    #
    # If the timesatmp is zero, use current time, from  NTP server
    # Iterate over the array and find time, is set
    #
    found = False
    for i in range(len(newvalues)):
        if newvalues[i][SENSOR_TAG] == SENSOR_TIME:
            found = i
            break

    if (
        found is not False
        and newvalues[i][SENSOR_VALUE] == DEFAULT_TIMESTAMP
    ):
        # Time is set to default
        newvalues[i][SENSOR_VALUE] = get_NPT_time(config, logging)
    else:
        # Time is not set, Set time
        newvalues.append({SENSOR_TIME: get_NPT_time(config, logging)})
    #
    # Iterate throght the "database" and lookup the incomming key value
    #
    found_in_db = False
    for db_index in range(0, len(sensorDB)):
        sensor_name_from_db = next(iter(sensorDB[db_index]))
        if sensor_name_from_db == sensor_name:
            found_in_db = True
            break
    if found_in_db:
        sensorDB[db_index][sensor_name] = newvalues
    else:
        sensorDB.append({sensor_name: newvalues})
    #
    # Save current values
    #
    try:
        current_sensor_file = open(filename, "w")
        current_sensor_file.write(json.dumps(sensorDB, indent=2))
        current_sensor_file.close()
    except Exception as e:
        logger.error(
            "General I/O Error writing sensorfile: " + filename
        )
        logger.error(traceback.format_exc())
        return -3
    return True


#########################################################
#
# get_sensor_db
#
#  Retrieves sensordb, and returns as DICT
#
# Parameters:
#   config,  all config parameters, points to sensor db
#   logger, output an errors
#
# Returns:
#   sensordb DICT
#   returns None if any error occur
#
#########################################################
def get_sensor_db(config, logger):

    filename = config[SENSORDB_FILENAME]
    try:
        #
        # Get current values
        #
        with open(filename, "r") as current_sensor_file:
            sensorDB = json.loads(current_sensor_file.read())

    except FileNotFoundError as fnfe:
        #
        # First time, Allocate empty list
        #
        logger.error(fnfe)
        logger.error(traceback.format_exc())
        return None
    except Exception as e:  # Catch any other I/O error
        logger.error("General Error reading sensorfile: " + filename)
        logger.error(traceback.format_exc())
        return None
    return sensorDB


#########################################################
#
# main entrypint
#
# Apply any testcode here
#
#########################################################
def main():
    config = {}
    config[SERVER_NTP_SERVER] = "time.google.com"
    config[SERVER_TIME_ZONE] = "Europe/Oslo"
    config[SERVER_TIME_FORMAT] = "%h:%m:%s"
    print(get_NPT_time(config, None))


if __name__ == "__main__":
    main()
