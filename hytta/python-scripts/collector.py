import os
import glob
import time
import requests
import urllib3
import sqlite3
import json
import platform
import urllib.parse
from datetime import datetime
import zoneinfo 
from sqlite3 import Error
from tplib import *

# from rpiglobals import rpiInitVariables
from common import *
import common
import argparse

# collector
#
# Collect all stats and updates iotlog table in desired cloud/database
# Collects, relays state of active relays, indoor temp in active zones, outdoor temp if available
##
# Python version: 3
#
# Modifictions
#   18/2  Something
# 	5/8-20 added save of desired temp in main
#   28/11-20 Changed to use socket/device name only no prefix
#   29/12-20 Extended colelction to include out door temp if it is not NULL (None) in the database
#   31/10-21  Added SODA Support
#   2/10-22  Made colelction more robust, swith to use sensorlib.py
#   4/12-22  Fixed minor bug in update to cloud for socket values. changed == 0 to == "1"
#   2/1-23  Changed report input format on JSON payload, SODA API
#   12/2-23  Disabled IP ipaddress 2.
#   14/2-23 removed need for rpiglobals, included in commonV2
#   14/2-23  Swicthed to tplib3, runs on python 3.
#   4/11-23  renamed to tplib when migrating to git and commonV2 to common
#   24/11-25 Added code for using sensordb.json, report it with SODA interface only
# Usage:
# python collector
#

progVersion = "3.0 241125"

# Global string keys used when indexing configuration and payload dictionaries


#
# globals
#
# debug=True
# defaultdebug_flag=2+4+8+16+32
# defaultdebug_flag=127
defaultdebug_flag = 0
global debug_flag
# rpig = None

tplink_devices = {}


def print_result(temp_device, ip_address, result):
    print(
        "Device: "
        + temp_device
        + " IP Address: "
        + ip_address
        + " "
        + "Relay state: "
        + str(result[KEY_SYSTEM][KEY_GET_SYSINFO][KEY_RELAYSTATE])
    )


DBG0 = 0b00000000
DBG1 = 0b00000001
DBG2 = 0b00000010
DBG4 = 0b00000100
DBG8 = 0b00001000
DBG16 = 0b00010000
DBG32 = 0b00100000
DBG64 = 0b01000000


#
# Debug
# debug_flag == 2, debug gettemp operations
# debug_flag == 4, debug texternalipV2
# debug_flag == 8, debug main
# debug_flag == 16  saveSoda
# debug_flag == 32 save_property
#
def print_debug(text, dbg):
    global debug_flag
    if (debug_flag & dbg) > 0:
        print(text)


def getexternalip_NLU(site_config):
    # defining a params dict for the parameters to be sent to the API
    # PARAMS = {'siteid':'=hytta','propertyname':'=ip'}
    PARAMS = "siteid=hytta"
    # sending get request and saving the response as response object
    # r = requests.get(url = rpig.config["currentipURL"], params = PARAMS,verify=False)
    r = requests.get(url=site_config[KEY_CURRENTIPURL], params=PARAMS, verify=False)
    if r:
        r.encoding = "utf-8"
        return r.text
    # extracting data in json format
    else:
        return "127.0.0.0"


def get_external_ip_V2(URL):
    #
    #  Fethc getmyip1URL
    #
    print_debug("Fetching externap IP from: " + URL, DBG4)
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning
    )  # Disable SSL warnings
    headers = {"content-type": "application/json", "User-agent": "Mozilla/5.0"}
    r = False
    try:
        r = requests.get(url=URL, headers=headers, verify=False)
    except Exception as httpError:
        print("Error when fetching external IP (get_external_ip_V2):")
        print(httpError)
        r = False
    #
    # Evaluate result
    #
    if r:
        r.encoding = "utf-8"
        return r.text
    else:
        #
        # Clearly mark the IP as undefined
        #
        return False


#
#  Read the scoket config file
#  Iterate through all sockets and  fetch relay state
#  Externa script updates the socket config file with relay state
#
def collect_device(socketfile):
    # Read device IP addr
    fp = open(socketfile)
    line = fp.readline().strip("\n")
    info = '{"system":{"get_sysinfo":{}}}'
    # iterate through and verify temp
    results = dict()
    i = 1
    while line:
        if len(line) > 1:
            ipAddress = line.split(" ")[0]
            tempDevice = line.split(" ")[1]
            tpState = do_tplink(ipAddress, info, 9999, True)
            result = dict()
            result[KEY_DEVICE] = tempDevice
            result[KEY_IP_ADDRESS] = ipAddress
            if tpState is False:
                result[KEY_RELAYSTATE] = "ERROR"
            else:
                result[KEY_RELAYSTATE] = str(tpState[KEY_SYSTEM][KEY_GET_SYSINFO][KEY_RELAYSTATE])
            results[str(i)] = result
            i = i + 1
        line = fp.readline().strip("\n")
    fp.close()

    return results


def collect(all_config):
    #
    # Globals
    #
    #  Indor temp from DS1820, gang
    #
    #
    temp_stats = {}
    stats={}

    for member in list(all_config[KEY_GROUPS]):
        if member[KEY_INUSE] == "Y":
            print_debug("processing temp group: " + member[KEY_GROUPNAME], DBG64)
            currentTemp = get_temp_for_group(
                all_config[KEY_SITE_CONFIG],
                member
            )
            if not (currentTemp == False):
                temp_stats[member[KEY_GROUPNAME]] = currentTemp
                print_debug(
                    "Group: "
                    + member[KEY_GROUPNAME]
                    + json.dumps(temp_stats[member[KEY_GROUPNAME]]),
                    DBG64,
                )
            else:
                dummyTemp = {KEY_TEMP: "-255", KEY_TIME: "01/01/1970, 00:00:00"}
                temp_stats[member[KEY_GROUPNAME]] = dummyTemp
                print_debug("Group: " + member[KEY_GROUPNAME] + " temp is False", DBG64)
    stats[KEY_TEMP_STATS] = temp_stats
    #
    # Collect socket status
    #
    try:
        tp_states = collect_device(all_config[KEY_SITE_CONFIG][KEY_SOCKET_CONFIG_FILE])
    except Exception as e:
        print("Collection of IP failed")
        raise
    stats[KEY_TP_SOCKETS] = tp_states
    #
    # Get external IP
    #
    ip_stats = {}
    try:
        ipaddress=json.loads(get_external_ip_V2(all_config[KEY_SITE_CONFIG][KEY_GETMYIP1URL]))
        # Return the format dict "ip":"ipaddress"
        ip_stats[KEY_IPADDRESS_FROM_CLOUD1] = ipaddress
    except:
        ip_stats[KEY_IPADDRESS_FROM_CLOUD1] = json.loads(
            '{"ip":"1.1.1.1"}'
        )  # Somethin went wrong...
    stats[KEY_IP_STATS] = ip_stats
    #
    # Get all stats from sensordb
    #
    stats[KEY_SENSOR_STATS]=get_temp_from_sensordb(all_config[KEY_SITE_CONFIG],False)
    stats[KEY_ALLSENSOR_STATS]=get_temp_from_sensordb(all_config[KEY_SITE_CONFIG],True)
    return stats

def save_property(property_name, property_value, site_config):
    #
    # Globals
    #
    #
    # Saving to endpoint
    #
    # api-endpoint
    headers = {"content-type": "application/json"}
    # headers = {"content-type": "application/json", "Authorization": "<auth-key>" }

    payload = {}
    payload[KEY_SITEID] = site_config[KEY_SITEID]
    payload[KEY_LOGNAME] = property_name
    payload[KEY_LOGVALUE] = property_value
    apiURL = site_config[KEY_IOTSTATSURL]
    if (
        site_config[KEY_IOTSTATSCLOUD] == "iosp"
        or site_config[KEY_IOTSTATSCLOUD] == "apex-evry"
        or site_config[KEY_IOTSTATSCLOUD] == "iosjump"
    ):
        data = json.dumps(payload)
        r = requests.post(apiURL, headers=headers, data=data)
        print_debug(apiURL, DBG32)
        print_debug(headers, DBG32)
        print_debug(data, DBG32)
        print_debug(r.status_code, DBG32)
        if r.status_code > 201:
            print("Failed with Status code: " + str(r.status_code))
            print(apiURL)
            print("Payload: ")
            print(data)
        else:
            print_debug("Sucessfully saved property: " + str(r.status_code), DBG32)
            print(
                "Sucessfully saved property: "
                + property_name
                + " value: "
                + property_value
                + " http Status: "
                + str(r.status_code)
            )
    elif site_config[KEY_IOTSTATSCLOUD] == "one.com":  # Not maintained fro a while......
        apiURL += urllib.parse.urlencode(payload)
        r = requests.get(apiURL, headers=headers)
        print_debug(r.status_code, DBG32)
        if r.status_code > 200:
            print(r.text)
            print(r.status_code)


#
#  Save the data to a SODA structure in one REST call
#
def save_property_soda(stats, site_config):
    headers = {"content-type": "application/json", "Authorization": "<auth-key>"}
    data = json.dumps(stats) # Save all stats
    with open('dumpsoda.json','w') as f:
        f.write(data)
    #
    #  Post payload with sodaURL
    #
    r = requests.post(
        site_config[KEY_SODAURL],
        headers=headers,
        auth=(site_config[KEY_SODAUSER], site_config[KEY_SODAPWD]),
        data=data,
    )
    print_debug(r.status_code, DBG16)
    if r.status_code > 201:
        print(r.text)
        print(r.status_code)
    else:
        print("SODA POST Success: ")
        print(str(r.text))


def main():
    global debug_flag
    # global rpig

    stats = {}
    print()
    print("Stats collector version: " + progVersion)
    #
    # Get site config
    #
    if platform.system().lower() == "linux":
        site_config_file = "/home/pi/conf/siteconfig.json"
    else:
        site_config_file = "g:\\demo_projects\\pi\\hytta\\config.json"

    args_parser = argparse.ArgumentParser(description="Collector program")
    args_parser.add_argument(
        "--configfile", default=site_config_file, type=str, help="Site Config File"
    )
    args_parser.add_argument("--debug", default=0, type=int, help="debug flag")
    args_parser.add_argument("--location", default="gang", type=str, help="gang|stue default gang")
    args = args_parser.parse_args()
    site_config_file = args.configfile
    if args.debug == 0:
        debug_flag = defaultdebug_flag
    else:
        debug_flag = args.debug
    print("Debug:" + str(debug_flag))
    #
    #  Load config
    #
    all_config = load_site_config(site_config_file)

    # rpig=all_config['siteConfig']
    #
    # Print save URL
    #
    print()
    print("Saving properties to cloud: " + all_config[KEY_SITE_CONFIG][KEY_IOTSTATSCLOUD])
    stats = collect(all_config)
    print_debug("resultat: ", DBG8)
    print_debug(json.dumps(stats), DBG8)
    #
    # Current we have collected the follwing stats
    #
    #  Ipadress from two soruces
    #  temp from applicable sources
    #  tp sockets
    #  collected in the dictionary stats['temp_stats'],['ip_stats'],['tpsockets']
    #
    # process temp_stats
    #
    jsonStats = []
    print_debug(json.dumps(stats[KEY_TEMP_STATS]), DBG8)
    for sensor_name in list(stats[KEY_TEMP_STATS]):
        temp_values = stats[KEY_TEMP_STATS][sensor_name]
        if not (stats[KEY_TEMP_STATS][sensor_name] == False):
            print_debug(
                "name: "
                + sensor_name
                + " time: "
                + temp_values[KEY_TIME]
                + " value: "
                + str(temp_values[KEY_TEMP]),
                DBG8,
            )
            # save_property(sensor_name,stats['temp_stats'][sensor_name])
            save_property(
                sensor_name,
                temp_values[KEY_TIME] + ";" + str(temp_values[KEY_TEMP]),
                all_config[KEY_SITE_CONFIG],
            )
        else:
            print_debug("name: " + sensor_name + "is False", DBG8)

    for ip_name in list(stats[KEY_IP_STATS]):
        ip_values = stats[KEY_IP_STATS][ip_name]
        for key in ip_values:
            print_debug("name: " + ip_name + " " + "ip: " + ip_values[key], DBG8)
            save_property(ip_name, ip_values[key], all_config[KEY_SITE_CONFIG])

    for device_name in list(stats[KEY_TP_SOCKETS]):
        device = stats[KEY_TP_SOCKETS][device_name]
        print_debug(
            "name: "
            + device[KEY_DEVICE]
            + " ipaddress: "
            + device[KEY_IP_ADDRESS]
            + " State: "
            + device[KEY_RELAYSTATE],
            DBG8,
        )
        save_property(
            device[KEY_DEVICE],
            ("ON " if device[KEY_RELAYSTATE] == "1" else "OFF"),
            all_config[KEY_SITE_CONFIG],
        )

    #
    #  Upload to SODA API
    #  Basically copy everything, but coded in case a more selective upload is needed
    #
    jStats = {}
    room_stat=[]
    for room in stats[KEY_TEMP_STATS]:
        room_stat.append({"roomname":room,KEY_TEMP:stats[KEY_TEMP_STATS][room][KEY_TEMP],KEY_TIME:stats[KEY_TEMP_STATS][room][KEY_TIME]})
    print(room_stat)
    jStats[KEY_SITENAME] = "hytta"
    jStats[KEY_TIME_CREATED] = datetime.now(zoneinfo.ZoneInfo("Europe/Oslo")).strftime("%Y-%d-%m %H:%M:%S") 
    jStats[KEY_TEMP] = room_stat
    jStats[KEY_IPADDRESSES] = stats[KEY_IP_STATS]
    jStats[KEY_TP_SOCKETS] = stats[KEY_TP_SOCKETS]
    jStats[KEY_SENSOR_STATS] = stats[KEY_SENSOR_STATS]
    jStats[KEY_ALLSENSOR_STATS] = stats[KEY_ALLSENSOR_STATS]
    print("Save to SODA")
    save_property_soda(jStats, all_config[KEY_SITE_CONFIG])
    print("Saved to SODA OK ")
    print_debug("*********************", DBG8)
    print_debug(json.dumps(stats), DBG8)
    print_debug("*********************", DBG8)


if __name__ == "__main__":
    main()
    # stats={}
    # stats["test1"]="15"
    # stats["test2"]=25
    # saveSoda(stats)
