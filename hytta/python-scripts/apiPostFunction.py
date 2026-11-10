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

#
# 10/11-26, redesign of storage format
# Example of new format:
#
#  
# Function that updates the file with current temperture from a given sensor
#
#  Required input structure
#  {"objecttag":"ESP32_BAD","sensors" :[{"sensorvalue": "11504", "sensortag": "mC"}, 
# {"sensorvalue": "41.4446", "sensortag": "Humidity"}]}
#
#  Lookup apiserverconstants for correct names in structure
#
#  Required file structure: (Modified 10/11-26)
#
#   JSON Array with sensor values
#   [
#    {"ds1820-gang": { "temp":"12.187","timestamp": "02.11.2026 22:45:05"}},
#    {"temp-stue": { "mctemp":"18305","Humidity":"40.2848","timestamp": "02.11.2026 22:45:05"}},
#    {"ds1820-stue":{"temp":"16.94","timestamp": "02.11.2026 22:45:05"}},
#    {"ESP32_BAD": {"mctemp":"13146","Humidity":"52.5701","timestamp": "02.11.2026 22:45:36"}}
#.  ]
def sensorSaveV2(config, sensorvalues, logger):
    #
    # Fetch the current sensordb
    #
    sensorDB = get_sensor_db(config, logger)
    if sensorDB is None:
        return None
    elif sensorDB == -1:  # Fiel does not exist create new
        sensorDB=[]
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
    # New version for new format
    #
    key_names = {
        "mC": "mctemp",
        "Temp": "temp",
        "Celsius": "temp",
        "Humidity":"Humidity",
    }
    # 
    # First flatten the structure to match sensorDB
    new_sensor_gauges = {}
    for sensor in sensorvalues["sensors"]:
        if "sensortag" in sensor:
            tag = sensor["sensortag"]
            new_sensor_gauges[key_names.get(tag, tag)] = sensor["sensorvalue"]

        if "timestamp" in sensor:
            new_sensor_gauges["timestamp"] = sensor["timestamp"]
        else:
            new_sensor_gauges["timestamp"] = get_NPT_time(config, logging)

    #
    # Update sensordb
    #
    # iterate over sensordb and find sensorname

    found=False
    for item in sensorDB:
        if sensorvalues[SENSOR_NAME] in item:
            item[sensorvalues[SENSOR_NAME]] = new_sensor_gauges
            found = True
            break
    if found is False:
        sensorDB.append({sensorvalues[SENSOR_NAME]:new_sensor_gauges})
    #
    # check for sensor temp, two values are allowed
    #

    #
    # Save current values
    #
    try:
        current_sensor_file = open(config[SENSORDB_FILENAME], "w")
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
        return -1
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
    config[SERVER_TIME_FORMAT] = "%d.%m.%Y %H:%M:%S"
    logging.basicConfig(
                filename='/Users/ingeos/projects/homeautomation/temp/apilog',
                filemode="w",
                format="%(name)s → %(levelname)s: %(message)s",
            )
    testpost=[]
    testpost.append('{"objecttag":"ESP32_BAD","sensors" :[{"sensorvalue": "12504", "sensortag": "mC"}, {"sensorvalue": "41.4446", "sensortag": "Humidity"}]}')
    testpost.append('{"objecttag":"test2","sensors" :[{"sensorvalue": "11504", "sensortag": "temp"}]}')
    testpost.append('{"objecttag":"test3","sensors" :[{"sensorvalue": "15.04", "sensortag": "temp"}]}')
    testpost.append('{"objecttag":"test3","sensors" :[{"sensorvalue": "17.04", "sensortag": "Celsius"},{"timestamp": "02.11.2026 22:45:05"}]}')
    config[SENSORDB_FILENAME]='/Users/ingeos/projects/homeautomation/temp/newsensordb'
    for i in range(0,4):
        sensorSaveV2(config, json.loads(testpost[i]), logging)


if __name__ == "__main__":
    main()
