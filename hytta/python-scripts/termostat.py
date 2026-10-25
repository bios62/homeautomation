import requests
import json
import sys
import urllib.parse
import os.path
from tplib import *
from common import *

# from rpiglobals import rpiInitVariables
import datetime
import pytz
from datetime import datetime
import time
import platform
import argparse
from sqlite3 import Error

# --- Combined Constants ---


# termostatV10
#
#  V4 Update: Adjuster interval +/- 0.5 of dtemp
#  V5 and V6: experimental, abandoned
#
#  V7 added funtion for dynamic settin of low temp based on time interval
#  Current version, no real funtion
#  V7 More failsafe code for reading temp sensors, migrated out to sensorlib.py
#  V9 added adjust of termostat based on price table
#  V9 switched from sensorlib.py to commonV1.py
#  V10 replaced CommonV1 with commonV2.py, commonv2 uses snake_case not CammelCase for functions
#  V11, changed all dictopnary references to constants from common
#
# Fetches config info about active zones from file
# Fecthes and saves temp settings for active zones from cloud
# fetches sockets for active zones
# Check relay state for active zones
# if temp deviates with more thatn +/- 0.5 degree, sets relays in zone accordingly
#
# Python version: 3
# E
# Modifictions
#   5/8-20 added save of desired temp in main
#   4/8-20 Added support for platform to set default siteConfigFile
#   3/2-21  Adjusted dtemp interval. Not implemented
#   2/4-21 Changed togle relay not to return if single member in group was not found
#   25/9-22 Added adjustTemp funtion for dynamic selection when temp is low, not implemented, only using defaultTemp
#   25/9-22 Restructured code for readin of sensors, moved to sensorlib
#   25/9 added adjust temp function, no real value
#   25/9 added calcualtion of age of temp files for remote and local
#   25/9 Added backuptemp calculation
#   22/10 CLeaned up termostat code
#   8/10-23 migrated to commonV2
#   15/12-24 Added additional check for elprice adjustment
#   03/01-26 Added code for usage of sensordb, ws look up each termomerter type
#
# Usage:
# python termostatV9.py [--configfile filename]

progVersion = "1.0 22102022"

USE_SENSORDB=False

if platform.system().lower() == "linux":
    siteConfigFile = "/home/pi/conf/siteconfig.json"
else:
    siteConfigFile = "C:\\usr\\demo_projects\\pi\\hytta\\config.json"


def getGroupsNLA_moved_to_CommonV2(siteConfig):
    #
    #  Fetch all groups
    #
    headers = {"content-type": "application/json"}
    g = requests.get(siteConfig[KEY_GROUP_CONFIG_URL], headers=headers)
    localConfig = []
    if g.ok:
        #
        # Fetch memerships
        #
        m = requests.get(siteConfig[KEY_MEMBERS_URL], headers=headers)
        if m.ok:
            allGroups = g.json()[KEY_ITEMS]
            allmembers = m.json()[KEY_ITEMS]
            #
            # Iterate through and add member array
            #
            for group in list(allGroups):
                #
                # iterate through all memers of a group
                #
                members = []
                for member in list(allmembers):
                    if member[KEY_GROUPNAME] == group[KEY_GROUPNAME]:
                        members.append(member[KEY_MEMBERNAME])
                group[KEY_MEMBERS] = members
                localConfig.append(group)
            f = open(siteConfig[KEY_GROUP_CONFIG_FILE], "w")
            f.write(json.dumps(localConfig))
            f.close()
            return localConfig
        else:
            print("API call for members failed: " + str(m.status_code))
            return False
    else:
        print("API call for groups failed: " + str(g.status_code))
        return False


def getDesiredTempSetting(tempSettingURL):
    print("Fetching desired temp setting")
    headers = {"content-type": "application/json"}
    r = requests.get(tempSettingURL, headers=headers)
    if r.ok:
        return r.json()[KEY_ITEMS]
    else:
        return False


#
# Loads site local configuration
#
# loads group memer configuration from file, assumes changes are rare
# if the file is not found, loads from iot service
#
def loadSiteConfig_NLU(siteConfigFile):
    #
    # Load master config file to get groupConfigFile path,
    # confURL, for static group membership
    # tempConfigURL for dynamic temp setting
    # groupconfig, contains statig gruop names and group sensor setup
    #
    allConfig = {}
    try:
        f = open(siteConfigFile, "r")
        strsiteconfig = f.read()
        siteConfig = json.loads(strsiteconfig)
        f.close()
    except IOError:
        print("Site Config File" + siteConfigFile + " is not accessible")
        return False

    tempSettingURL = siteConfig[KEY_TEMP_SETTING_URL]
    groupConfigFileName = siteConfig[KEY_GROUP_CONFIG_FILE]
    socketConfigFileName = siteConfig[KEY_SOCKET_CONFIG_FILE]
    #
    # Load static membership,
    # if file exists, load local file
    # if not fetch form OT database
    #
    if os.path.isfile(groupConfigFileName):
        try:
            f = open(groupConfigFileName, "r")
            strconfig = f.read()
            groups = json.loads(strconfig)
            f.close()
        except IOError:
            print(
                "Member Config File"
                + groupConfigFileName
                + " exists but is not accessible"
            )
            return False
    else:
        #
        # Group Config did not exists need to fetch it from iot database
        #
        groups = get_groups(siteConfig)
    #
    # Read the socket input file and add it to a dict
    # File is in host format  ip name
    # stored as an array  the config json
    allSockets = []
    try:
        fp = open(socketConfigFileName)
        line = fp.readline().strip("\n")
        allSockets = []
        while line:
            pos = line.find(" ")
            ip = line[:pos]
            host = line[pos + 1 :].lstrip()
            sockets = {}
            sockets[KEY_SOCKETNAME] = host
            sockets[KEY_IP] = ip
            allSockets.append(sockets)
            line = fp.readline().strip("\n")
    except IOError:
        print(
            "Socket Config File "
            + socketConfigFileName
            + " exists but is not accessible"
        )
        return False
    #
    # build dics result
    #

    allConfig[KEY_GROUPS] = groups
    allConfig[KEY_SITE_CONFIG] = siteConfig
    allConfig[KEY_TP_SOCKETS] = allSockets
    return allConfig


#
# printResult
#
# Prints resut of setting relay state
#
def printResult(result):
    if KEY_SET_RELAYSTATE in result[KEY_SYSTEM]:
        print(
            " Command, Error Code: "
            + str(result[KEY_SYSTEM][KEY_SET_RELAYSTATE][KEY_ERR_CODE]),
            end=" ",
        )
    elif KEY_GET_SYSINFO in result[KEY_SYSTEM]:
        print(" Relay state: " + str(result[KEY_SYSTEM][KEY_GET_SYSINFO][KEY_RELAYSTATE]))
    else:
        print(" Unknown result ")
        print(result)


#
# toggleRelay
# Last changed 31/3-2020
#
# turns a tplink socket on or off
# Parameters
#   socketList      list of all sockets
#   relayList       list of all sockets to be canged
#   state           ON or OFF
#
# the funtion return False upon either socket not found or scket creatin failed
#
def toggleRelay(socketList, relayList, state):
    #
    # iterate through the list of sockets and verify if it esist in the list of sockets to be changed
    #
    #
    #  Iterate through the list of relays and find matchin socket
    #
    print(json.dumps(relayList))
    for relay in list(relayList):
        #
        # Iterate over sockets to get IP address
        #
        onsw = '{"system":{"set_relay_state":{"state":1}}}'
        offsw = '{"system":{"set_relay_state":{"state":0}}}'
        info = '{"system":{"get_sysinfo":{}}}'
        relayCommand = onsw
        if state == 0:
            relayCommand = offsw
        elif state == 1:
            relayCommand = onsw
        else:
            relayCommand = info
        socketFound = False
        for i in range(len(socketList)):
            if relay == socketList[i][KEY_SOCKETNAME]:
                print(
                    "  Device: "
                    + socketList[i][KEY_SOCKETNAME]
                    + " "
                    + socketList[i][KEY_IP]
                    + " CMD:"
                    + relayCommand
                )
                result = do_tplink(socketList[i][KEY_IP], relayCommand, 9999)
                if result:
                    print("    ", end=" ")
                    printResult(result)
                    result = do_tplink(socketList[i][KEY_IP], info, 9999)
                    print("    ", end=" ")
                    printResult(result)
                else:
                    print("     Connection failure " + socketList[i][KEY_IP])
                socketFound = True
        if not socketFound:
            print("     Socket:" + relay + " Not found in socket hostfile")
            # return(False)  // Continue for rest of members f group
    return True


#
# turn socket on or off based 2 conditions
#   group is inuse
#   temp is outside range
#
# Changes 03.01.26. Added code for usage of sensordb
# Dependendt on "compilationflag USE_SENSORDB"
#
def termostat(allConfig, desiredTemp):
    #
    # iterate through all groups, static values
    #
    currentTemp = {}

    #
    # If sensor db is used read all temp prior to processing
    #
    if allConfig[KEY_SITE_CONFIG][KEY_USE_SENSORDB].lower() == 'true':
        all_temp=get_all_sensordb(allConfig[KEY_SITE_CONFIG])
                  

    for member in list(allConfig[KEY_GROUPS]):
        #
        # Iterate through all current settings and fetch sensor temp value and desired temp
        #
        if member[KEY_INUSE] == "Y":
            #
            # If current temp is 0.5 below desiredTemp, flip on sockets
            # If current temp is 0,5 above desiredtemp, flip off sockets
            # desiredtemp is based on which of the two settings applies
            #
            # Iterate through desiredTemp dict and find high/low/ and selected

            #
            #  Correction logic for usage of adjusted temp is added
            #  Iterate over desiretemp, to find desiretemp for group that match current group
            #  If not found dtemp== False
            #
            dtemp = False  # Generate error in code if not set
            for tempSetting in list(desiredTemp):
                if tempSetting[KEY_GROUPNAME] == member[KEY_GROUPNAME]:
                    currentTempSetting = tempSetting[KEY_SELECTEDTEMP]
                    if (
                        tempSetting[KEY_SELECTEDTEMP] == "L"
                        and member[KEY_USETERMOSTAT] == "Y"
                    ):
                        dtemp = adjustTemp(
                            allConfig[KEY_SITE_CONFIG],
                            tempSetting[KEY_LOWTEMP],
                            tempSetting[KEY_ADJUSTEDTEMP],
                        )
                    elif (
                        tempSetting[KEY_SELECTEDTEMP] == "H"
                        and member[KEY_USETERMOSTAT] == "Y"
                    ):
                        dtemp = tempSetting[KEY_HIGHTEMP]
                    break
                #
            #
            if (
                member[KEY_USETERMOSTAT] == "Y"
            ):  # Slave config not implemented stue ekstra
                #  Find current temp for group
                #
                if dtemp is False:  # Severe error, termostat is Y but no setpoint
                    print(
                        "Temp setpoint for group: " + member[KEY_GROUPNAME] + " Not Found"
                    )
                    return False
                #
                # Use the "old" style if USE_SENSORDB is not set to True
                #
                
                if allConfig[KEY_SITE_CONFIG][KEY_USE_SENSORDB].lower() != 'true':
                    #
                    # Find current temp for the group
                    #
                    # 12/2-2023 this code is not safe, needs to be restructured as not all temp are found, including backuptemp
                    #
                    ctemp = get_temp_for_group(
                        allConfig[KEY_SITE_CONFIG],
                        member,
                    )
                    if ctemp is False:
                        print(
                            "Severe error: temp not found for: "
                            + member[KEY_GROUPNAME]
                            + " "
                            + allConfig[KEY_SITE_CONFIG][member[KEY_SENSORCONFIG]]
                        )
                    #   ctemp=getBackupTemp(member['groupname'],currentTemp)
                    #   if ctemp is not False:
                    #       print('Using backuptemp for '+member['groupname'])
                else:  # Use Sensorddb. 
                    # Code for backup sensor moved to sensordb code
                    # Dependent on Local sensrodb file pointed to by siteconfig
                    # TODO: all_temp
                    if member[KEY_GROUPNAME] in all_temp:
                        ctemp=all_temp[member[KEY_GROUPNAME]]
                    else:
                        print(f'temp fro group {member[KEY_GROUPNAME]} is not found')
                        print(all_temp)
                        ctemp=False
                    if ctemp is False:
                        print(
                            "Severe error: temp not found for: "
                            + member[KEY_GROUPNAME]
                            + " "
                            + allConfig[KEY_SITE_CONFIG][member[KEY_SENSORCONFIG]]
                        )
                #
                # If no current temp is found exit
                #
                # if ctemp is False:
                #   print("Severe error: backuptemp not found for: "+member['groupname'])
                #   return(False)   # SHALL NOT EXIT stops processing
                #
                #  Flip relay on or off dependentent on temp deviation
                #
                if not ctemp == False:
                    if float(ctemp[KEY_TEMP]) < (dtemp - 0.5):  # temp to low
                        print(
                            "Group: "
                            + member[KEY_GROUPNAME]
                            + " temp to low: set temp: "
                            + str(dtemp).strip("\n")
                            + " real temp: "
                            + str(ctemp[KEY_TEMP])
                        )
                        toggleRelay(allConfig[KEY_TP_SOCKETS], member[KEY_MEMBERS], 1)
                    elif float(ctemp[KEY_TEMP]) > (dtemp + 0.5):
                        print(
                            "Group: "
                            + member[KEY_GROUPNAME]
                            + " temp to high: set temp: "
                            + str(dtemp).strip("\n")
                            + " real temp: "
                            + str(ctemp[KEY_TEMP])
                        )
                        toggleRelay(allConfig[KEY_TP_SOCKETS], member[KEY_MEMBERS], 0)
                    else:
                        print(
                            "Group: "
                            + member[KEY_GROUPNAME]
                            + " temp within range: set temp: "
                            + str(dtemp).strip("\n")
                            + " real temp: "
                            + str(ctemp[KEY_TEMP])
                        )
                    # toggleRelay(allConfig['tpSockets'],member['members'],0) # If within range, leave it

            else:
                #
                # Not controlled by sensor, flip to on if temp is set to high, flip off if temp is set to low
                #
                if currentTempSetting == "H":
                    print("Group: " + member[KEY_GROUPNAME] + " set ON")
                    toggleRelay(allConfig[KEY_TP_SOCKETS], member[KEY_MEMBERS], 1)
                else:
                    print("Group: " + member[KEY_GROUPNAME] + " set OFF")
                    toggleRelay(allConfig[KEY_TP_SOCKETS], member[KEY_MEMBERS], 0)


#
#  adjustTemp
#
#  Based on timeof day or later interface to Norpool, adjust temp
#
#  14.12.24 If default temp is below adjustet temp, dont make any attempt to adjust
#
def adjustTemp(siteConfig, defaultTemp, adjustTemp):
    #
    # Read time of day
    #
    tz = pytz.timezone("Europe/Oslo")
    currentDateTime = datetime.now(tz)
    # If timeofday is between interval adjust temp
    #
    #  Currently not implemented, just use defaultTemp

    if defaultTemp < adjustTemp :
        print(f'temp setpoint ({str(defaultTemp)}) is below adjustment setpoint ({str(adjustTemp)}), skipping adjustment')
        return defaultTemp
    elprice_structure_verified=False
    try:
        with open(siteConfig[KEY_EL_PRICE_FILE], "r") as infile:
            currPrice = json.load(infile)
        #
        # Verify structure
        #
        elprice_structure_verified= verify_price_structure(currPrice)
    except:
        #
        # norpool data not available
        #
        print("I/O Error when reading: " + siteConfig[KEY_EL_PRICE_FILE])
    if not  elprice_structure_verified:
        if (currentDateTime.hour > 6 and currentDateTime.hour < 11) or (
            currentDateTime.hour > 14 and currentDateTime.hour < 19
        ):
            print(f'Adjust temp on estimate: {str(adjustTemp)}')
            return adjustTemp
        else:
            return defaultTemp
    #
    # norpool net 24 hours are available
    #  
    hourPrice = findHourPrice(currPrice, currentDateTime.hour)
    avgPrice = getAvgPrice(currPrice)
    print("CurrentPrice: " + str(hourPrice) + " Average Price: " + str(avgPrice))
    if hourPrice > avgPrice:
        print("Adjust based on norpool")
        return adjustTemp
    else:
        print("no norpool adjustment")
    return defaultTemp


#
#  backupTemp
#  backup for Gang == Stue
#  backup for Stue == gang
#
def getBackupTemp(groupName, currentTemp):
    if groupName == "Stue":
        return currentTemp["Gang"]
    elif groupName == "Gang":
        return currentTemp["Stue"]

#
# Iterate through all prices
# Find current hour
# Lookup the price pr. current hour
#
#  Todo: verify that the prices is for the current day
#  Todo: Return false if no hour found
#
def findHourPrice(dayPrices, hour):
    count = len(dayPrices)
    for i in range(0, count):
        sTime = dayPrices[i][KEY_TIME_START]
        eTime = dayPrices[i][KEY_TIME_END]
        startTime = datetime.strptime(sTime[:22] + sTime[23:], "%Y-%m-%dT%H:%M:%S%z")
        if hour == startTime.hour:
            break
    if i < count:
        return dayPrices[i][KEY_NOK_PER_KWH]

#
#  Verify the structure of the elprices
#
def verify_price_structure(dayPrices):
    count = len(dayPrices)
    if count != 24 :
        #
        # Wrong structure
        #
        print(f'Elprice structure incomplete: {str(count)} rows')
        return(False)
    #
    #  Check if the first price is within this day
    #
    current_time=datetime.now(pytz.timezone("Europe/Oslo"))
    
    try:
        start_time_in_file=dayPrices[0][KEY_TIME_START]
        el_time=datetime.strptime(start_time_in_file,'%Y-%m-%dT%H:%M:%S%z')
        if el_time.year==current_time.year and el_time.month == current_time.month and el_time.day == current_time.day:
            return True
        print(f'el time is wrong date: {start_time_in_file}')
        return False
    except Exception as e:
        print("Time conversion for elprice failed")
        print(e)
        return(False)
#
# Iterate over all prices and calculate todays
# AVG price
#
#  Todo: verify that the prices is for the current day
#
def getAvgPrice(dayPrices):
    if dayPrices != False:
        count = len(dayPrices)       
        #
        # Iterate over prices and calculate todays avg price.
        #
        priceAcc = 0
        
        for i in range(0, count):
            priceAcc = priceAcc + dayPrices[i][KEY_NOK_PER_KWH]
        avgPrice = priceAcc / count
        return avgPrice
    else:
        return False


#
# Main
#
def main():
    global siteConfigFile

    #
    # Identify program
    #
    print()
    print("Termostat V7 version: " + progVersion)
    print()
    #
    # process comand line onl one optin available, -f filename for sysconfig fiel
    #
    argsParser = argparse.ArgumentParser(description="Termostat program")
    argsParser.add_argument(
        "--configfile", default=siteConfigFile, type=str, help="Site Config File"
    )
    args = argsParser.parse_args()
    siteConfigFile = args.configfile

    #
    # Load static site config information
    #
    allConfig = load_site_config(siteConfigFile)
    if not allConfig:
        print("Error Loading confguration")
        return 1
    if allConfig[KEY_SITE_CONFIG][KEY_USE_SENSORDB].lower == 'true':
        print('Configuration loaded, using sensordb')
    else:
        print('Configuration loaded, using classic temp')
    #
    # Fetch dynamic temp setting
    #
    print("Fetch dynamic temp setting")
    desiredTemp = getDesiredTempSetting(allConfig[KEY_SITE_CONFIG][KEY_TEMP_SETTING_URL])
    #
    # Save current desired temp values, to be consumed by other programs
    # Works as cache for the desired temp config
    #
    fp = open(allConfig[KEY_SITE_CONFIG][KEY_DESIREDTEMPFILE], "w")
    fp.write(json.dumps(desiredTemp))
    fp.close()
    #
    # Process termostat
    #
    print("Processing Termostat settings")
    termostat(allConfig, desiredTemp)
    #
    print("Termostat setting completed")


if __name__ == "__main__":
    main()