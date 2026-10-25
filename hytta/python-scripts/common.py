import sqlite3
import time
import platform
import json
import os
import requests
from datetime import datetime

# from rpiglobals import rpiInitVariables

#
#  Version: 14.08.2023
#
# Change 14/8-2023:  removed rpiglobals added load_config_from_file
#
# globals
#
DEBUG_FLAG_COMMON = 0
DBG0 = 0b00000000
DBG1 = 0b00000001
DBG2 = 0b00000010
DBG4 = 0b00000100
DBG8 = 0b00001000
DBG16 = 0b00010000
DBG32 = 0b00100000
DBG64 = 0b01000000
DEBUG_SENSORDB=False

#
# Generic Constants
#
KEY_ADJUSTEDTEMP        = "adjustedtemp"
KEY_ALLSENSOR_STATS     = "allsensorstats"
KEY_BACKUP_GROUP        = "backupgroup"
KEY_CURRENTIPURL        = "currentipURL"
KEY_DEVICE              = "device"
KEY_ERR_CODE            = "err_code"
KEY_GET_SYSINFO         = "get_sysinfo"
KEY_GROUPNAME           = "groupname"
KEY_GROUPS              = "groups"
KEY_HIGHTEMP            = "hightemp"
KEY_INUSE               = "inuse"
KEY_IP                  = "ip"
KEY_IP_ADDRESS          = "ipAddress"
KEY_IP_STATS            = "ipStats"
KEY_IPADDRESS_FROM_CLOUD1 = "ipaddressFromCloud1"
KEY_IPADDRESSES         = "ipaddresses"
KEY_ITEMS               = "items"
KEY_LOGNAME             = "logname"
KEY_LOGVALUE            = "logvalue"
KEY_LOWTEMP             = "lowtemp"
KEY_MEMBERS             = "members"
KEY_MEMBERNAME          = "membername"
KEY_NAME                = "name"
KEY_NOK_PER_KWH         = "NOK_per_kWh"
KEY_PRIORITY            = "priority"
KEY_RELAYSTATE          = "relay_state"
KEY_SCALE               = "scale"
KEY_SELECTEDTEMP        = "selectedtemp"
KEY_SENSOR_STATS        = "sensorstats"
KEY_SENSORTAG           = "sensortag"
KEY_SENSORVALUE         = "sensorvalue"
KEY_SET_RELAYSTATE      = "set_relay_state"
KEY_SITE_CONFIG         = "siteConfig"
KEY_SITENAME            = "sitename"
KEY_SOCKETNAME          = "socketname"
KEY_SYSTEM              = "system"
KEY_TEMP                = "temp"
KEY_TEMP_STATS          = "tempStats"
KEY_TIME_CREATED        = "creationtime"
KEY_TIME                = "time"
KEY_TIME_START          = "time_start"
KEY_TIME_END            = "time_end"
KEY_TIMESTAMP           = "timestamp"
KEY_TP_SOCKETS          = "tpSockets"
KEY_USETERMOSTAT        = "usetermostat"
#
# Constants related to siteconfig file
#
KEY_DESIREDTEMPFILE     = "desiredtempfile"
KEY_EL_PRICE_AREA       = "elPriceArea"
KEY_EL_PRICE_FILE       = "elPriceFile"
KEY_EL_PRICE_URL        = "elPriceURL"
KEY_GETMYIP1URL         = "getmyip1URL"
KEY_GETMYIP2URL         = "getmyip2URL"
KEY_GROUP_CONFIG_FILE   = "groupConfigFile"
KEY_GROUP_CONFIG_URL    = "groupConfigURL"
KEY_IOT_DIRECTORY       = "iotDirectory"
KEY_IOTSTATSCLOUD       = "iotstatscloud"
KEY_IOTSTATSURL         = "iotstatsURL"
KEY_LOCAL_TEMP_FILE     = "localtempfile"
KEY_LOG_DIRECTORY       = "logDirectory"
KEY_MAX_AGE             = "maxAgeInHours"
KEY_MEMBERS_URL         = "membersURL"
KEY_REMOTE_TEMP_FILE    = "remotetempfile"
KEY_SENSORCONFIG        = "sensorconfig"
KEY_SENSORDB            = "sensordatabase"
KEY_SENSORTAGS          = "sensortags"
KEY_SITEID              = "siteid"
KEY_SOCKET_CONFIG_FILE  = "socketConfigFile"
KEY_SODAPWD             = "sodapwd"
KEY_SODAURL             = "sodaURL"
KEY_SODAUSER            = "sodauser"
KEY_TEMP_SETTING_URL    = "tempSettingURL"
KEY_USE_SENSORDB        =  "use_sensordb"
KEY_WEEWX_FILE          = "weewxfile"
#
# List of mandatory parmeters
#

param_list = [
    KEY_DESIREDTEMPFILE,
    KEY_EL_PRICE_AREA,
    KEY_EL_PRICE_FILE,
    KEY_EL_PRICE_URL,
    KEY_GETMYIP1URL,
    KEY_GETMYIP2URL,
    KEY_GROUP_CONFIG_FILE,
    KEY_GROUP_CONFIG_URL,
    KEY_IOT_DIRECTORY,
    KEY_IOTSTATSCLOUD,
    KEY_IOTSTATSURL,
    KEY_LOCAL_TEMP_FILE,
    KEY_LOG_DIRECTORY,
    KEY_MAX_AGE,
    KEY_MEMBERS_URL,
    KEY_REMOTE_TEMP_FILE,
    KEY_SENSORCONFIG,
    KEY_SENSORDB,
    KEY_SENSORTAGS,
    KEY_SITEID,
    KEY_SOCKET_CONFIG_FILE,
    KEY_SODAPWD,
    KEY_SODAURL,
    KEY_SODAUSER,
    KEY_TEMP_SETTING_URL,
    KEY_USE_SENSORDB,
    KEY_WEEWX_FILE
]

#
#
class MissingConfigError(Exception):
    """Generic Exception for clean close of resoruces.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Value missing in configuration"):
        self.message = message
        super().__init__(self.message)


#
#
# Debug
# DEBUG_FLAG_COMMON == 2, debug print read_DS1820_json
# DEBUG_FLAG_COMMON == 4, debug print get_temp_for_group
#
def print_debug_common(text, dbg):
    if (DEBUG_FLAG_COMMON & dbg) > 0:
        print(text)


#
# verify_file_age()
#
# Verifies the age of the file, and if it is older than max_age_in_hours, return false
#
#  Convert to int and compare to 3600 sek * max_age_in_hours
#
def verify_file_age(file_name, max_age_in_hours):
    mod_time_since_epoc = int(os.path.getmtime(file_name))
    if int(time.time()) > mod_time_since_epoc + (max_age_in_hours * 3600):
        return False
    return True


#
#  Read DS1802 return lines
#
#  Verify Age of file,return False if to old
#  return False if any I/O error occurs
#
def read_DS1820_file(file_name, max_age_in_hours):
    try:
        if verify_file_age(file_name, max_age_in_hours) is False:
            print(
                "File: "
                + file_name
                + " is older than: "
                + str(max_age_in_hours)
                + " hours"
            )
            return False
        device_file = open(file_name, "r")
        lines = device_file.readlines()
        device_file.close()
        return lines
    except Exception as e:
        print("read_DS1820_file Error:")
        print(e)
        return False


#
#  read_DS1820_raw
#  Iterates max_loops time to attempt to fetch value
#
# !!!!! THE LOGIC HERE MUST BE WRONG
#
def read_DS1820_raw(site_config, group, max_loops, max_age_in_hours):
    loop_count = 0
    lines = False
    parameter_name = group["sensorconfig"]
    file_name = site_config[parameter_name]
    while (
        loop_count < max_loops
    ):  # Need to loop in case we are just in a sensor read cycle
        lines = read_DS1820_file(file_name, max_age_in_hours)
        if not lines:  # Max loops
            time.sleep(0.2)
            # lines = read_DS1820_file(file_name, max_age_in_hours)
            loop_count += 1
        elif lines[0].strip()[-3:] != "YES":  # File not ready
            time.sleep(0.2)
            # lines = read_DS1820_file(file_name, max_age_in_hours)
            loop_count += 1
        else:
            break
            #
            # If loop ends with cloopCount=20 we did not succseed in readin the file
            #
    if loop_count < max_loops:
        equal_pos = lines[1].find("t=")
        if equal_pos != -1:
            temp_string = lines[1][equal_pos + 2 :]
            temp_c = float(temp_string) / 1000.0
            return temp_c
        else:
            print(
                "getTempForGorup error: Group: "
                + group["groupName"]
                + " wrong format in file"
            )
            print(lines)
            return False
    else:
        print(
            "getTempForGorup error: Group: " + group["groupName"] + " File Read Error"
        )
        return False


#
#  Read DS1802 in json format
# Assumes external script (getds1820V2.py) is run by crontab
#
def read_DS1820_json(site_config, group, max_age_in_hours):
    print_debug_common("ds1820 debug", DBG2)
    print_debug_common(json.dumps(group), DBG2)
    parameter_name = group["sensorconfig"]
    file_name = site_config[parameter_name]
    print_debug_common(
        "file_name: " + file_name + " parameter Name: " + parameter_name, DBG2
    )
    #
    # Read the raw lines from file
    #
    lines = read_DS1820_file(file_name, max_age_in_hours)
    #
    # Parse JSON file
    #
    if lines is False:
        return False
    try:
        temp_json = json.loads(lines[0])
    except Exception as e:
        print("read_DS1820_json error:")
        print(e)
        return False
    return temp_json


#
#  Reading indoor temp from local Weewx sqlite database
#  inout 'indoor' or 'outdoor'
#
def read_weewx(site_config, group, inout):
    #
    # read from sqlite
    #
    conn = None
    #
    #  Set up a sqllite connection to a target
    #
    conn = create_connection(site_config[group["sensorconfig"]])
    if conn is False:
        print(
            "read_weewx error: Group: "
            + group["groupname"]
            + " could not open sqllite db"
        )
        return False  # Exit if connection fails
    #
    # Read the temp from the weewk db
    #

    cur = conn.cursor()
    if inout == "indoor":
        sqlstmt = "select ifnull(inTemp,-99),datetime from archive  where datetime="
        sqlstmt = sqlstmt + "(select max(datetime) from archive)"
    elif inout == "outdoor":
        sqlstmt = "select ifnull(outTemp,-99),datetime from archive  where datetime="
        sqlstmt = sqlstmt + "(select max(datetime) from archive)"
    else:
        print("Eror: read_weewx: inout paramter illeagl: " + str(inout))
        return False
    try:
        cur.execute(sqlstmt)
        rows = cur.fetchall()
        temp = {}
        temp[KEY_TEMP] = ((rows[0])[0] - 32) / 1.8
        temp["time"] = rows[0][1]
    except Exception as sql_exception:
        print("SQL Statement failed: " + sqlstmt)
        print(str(sql_exception))
        return False
    return temp


def create_connection(db_file):
    """create a database connection to a SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # print(sqlite3.version)
    except Exception as sqlite_error:
        print("sqllite open error:")
        print(sqlite_error)
        return False
    return conn

#
# Verifies site_config values of sensorconfig and sensordb
# and retrieves all values for the given sensors with get_group_temperatures_sensordb 
# get_group_temperatures_sensordb processes max_age from site_config and backup values from sensor_config
#
# If no valid reading is available, the backup temperature is fetched.
# In case no valid temp is available, it returns false for the group
#
def get_all_sensordb(site_config):
    #
    # Open files in a robust way
    #
    # Open and get config data from sensor_config file
    #
    try:
        with open(site_config[KEY_SENSORCONFIG],"r") as sensor_file:
            sensor_config=json.loads(sensor_file.read())
    except Exception as e:
        print(f'Error when open sensorconfig file: {site_config[KEY_SENSORCONFIG]}')
        print(e)
        return(False)
    #
    # Open and get current sensordb
    #
    try:
        with open(site_config[KEY_SENSORDB],"r") as sensordb:
            sensor_values=json.loads(sensordb.read())
    except Exception as e:
        print(f'Error when open sensor databasefile: {site_config[KEY_SENSORDB]}')
        print(e)
        return(False)
    #
    # Fetch all temperatures
    #
    return get_group_temperatures_sensordb(site_config, sensor_config, sensor_values)



#
# Fetches the temp for a given group, from the sensors, based on groupname, and metadata/file
# ds1820 type devices read temp from line 2 of a specific file, temp is coded without .
#
# weewx reads from sqlite db
#
#  Caller is responsible for veriyfing that group is active
#
#  Return fetched temp in a dict as follows['sensorname']['time']['temp']
#  If temp reading for som reason is not possible, return False
#
def get_temp_for_group(site_config, group):
    #
    # initial settings
    #  
    max_file_age_in_hours = int(site_config[KEY_MAX_AGE])
    #
    # Verify if inuse is set to Y
    #
    if group["inuse"] != "Y":
        print_debug_common(
            "getTempForGorup error: Group: "
            + group["groupname"]
            + " has not set inuse flag",
            DBG4,
        )
        return False
    #
    #  Split on sensor type
    #  ds1820 reads from a file
    #
    if group["sensortype"] == "ds1820":
        # ds1820 type, read from file
        max_loops = 20
        return read_DS1820_raw(site_config, group, max_loops, max_file_age_in_hours)
    elif group["sensortype"] == "weewx":
        return read_weewx(site_config, group, "indoor")
    elif group["sensortype"] == "weewx-outdoor":
        return read_weewx(site_config, group, "outdoor")
    elif group["sensortype"] == "json":
        return read_DS1820_json(site_config, group, max_file_age_in_hours)
    else:
        print("getTempForGorup error: Group: " + group["groupname"] + " have no defined temp sensors")
        return False
    return False


#
# load_config_from_file
#
#  Loads config, amd verifies mandatory parameters
#
#  Input parameter
#   site_config_file_name, full filepath to configfile
# Globals:
#   parameter_list, list of all mandatory parameters
# Output:
#   dict with all mandatory cnfig parameters
#
# Exception
#   throws configErrorException if mandatory parameter is missing
#
def load_config_from_file(site_config_file_name):
    config = {}

    # Open and process config file
    #
    try:
        fp = open(site_config_file_name, "r")
        params = json.loads(fp.read())
        fp.close()
    except Exception as e:
        print(" Process of config file failed")
        print(str(e))
        raise MissingConfigError("Processing of " + site_config_file_name + "failed")
    #
    config = {}
    # Iterate over all mandatory parameters
    for param_name in param_list:
        if param_name in params:
            config[param_name] = params[param_name]
        else:
            config[param_name] = None
            raise MissingConfigError(
                "Mandatory parameter: "
                + param_name
                + " Is not found in : "
                + site_config_file_name
            )
    return config


#
# get_groups
def get_groups(site_config):
    #
    #  Fetch all groups
    #
    headers = {"content-type": "application/json"}
    g = requests.get(site_config["groupConfigURL"], headers=headers)
    local_config = []
    if g.ok:
        #
        # Fetch memerships
        #
        m = requests.get(site_config["membersURL"], headers=headers)
        if m.ok:
            all_groups = g.json()["items"]
            all_members = m.json()["items"]
            #
            # Iterate through and add member array
            #
            for group in list(all_groups):
                #
                # iterate through all memers of a group
                #
                members = []
                for member in list(all_members):
                    if member["groupname"] == group["groupname"]:
                        members.append(member["membername"])
                group["members"] = members
                local_config.append(group)
            group_config_file_pointer = open(site_config["groupConfigFile"], "w")
            group_config_file_pointer.write(json.dumps(local_config))
            group_config_file_pointer.close()
            return local_config
        else:
            print("API call for members failed: " + str(m.status_code))
            return False
    else:
        print("API call for groups failed: " + str(g.status_code))
        return False


#
# Loads site local configuration
#
# loads group memer configuration from file, assumes changes are rare
# if the file is not found, loads from iot service
#
def load_site_config(site_config_file):
    #
    # Load master config file to get groupConfigFile path,
    # confURL, for static group membership
    # tempConfigURL for dynamic temp setting
    # groupconfig, contains statig gruop names and group sensor setup
    #
    all_config = {}
    # site_config = rpiInitVariables(site_configFile)
    site_config = load_config_from_file(site_config_file)

    # temp_setting_url = site_config["tempSettingURL"]
    group_config_file_name = site_config["groupConfigFile"]
    socket_config_file_name = site_config["socketConfigFile"]
    #
    # Load static membership,
    # if file exists, load local file
    # if not fetch form OT database
    #
    if os.path.isfile(group_config_file_name):
        try:
            config_file = open(group_config_file_name, "r")
            strconfig = config_file.read()
            groups = json.loads(strconfig)
            config_file.close()
        except IOError:
            print(
                "Member Config File"
                + group_config_file_name
                + " exists but is not accessible"
            )
            return False
    else:
        #
        # Group Config did not exists need to fetch it from iot database
        #
        groups = get_groups(site_config)
    #
    # Read the socket input file and add it to a dict
    # File is in host format  ip name
    # stored as an array  the config json
    all_sockets = []
    try:
        socket_file = open(socket_config_file_name)
        line = socket_file.readline().strip("\n")
        all_sockets = []
        while line:
            pos = line.find(" ")
            ip = line[:pos]
            host = line[pos + 1 :].lstrip()
            sockets = {}
            sockets["socketname"] = host
            sockets["ip"] = ip
            all_sockets.append(sockets)
            line = socket_file.readline().strip("\n")
    except IOError:
        print(
            "Socket Config File "
            + socket_config_file_name
            + " exists but is not accessible"
        )
        return False
    #
    # build dics result
    #

    all_config["groups"] = groups
    all_config["siteConfig"] = site_config
    all_config["tpSockets"] = all_sockets
    # all_config["rpig"] = site_config
    return all_config


def get_all_temperatures(sensordb):
    """
    Converts sensordb to a list ov sensors name,values,timesatmt in converted format
    
    Args:
        sensordb (list): List of dictionaries containing sensor readings.
        
    Returns:
        list: A list of dictionary {sensorname: temperature_value:timestamp} timestamp in format "%m/%d/%Y, %H:%M:%S"
    """
    allSensors=[]
    for i in range(0,len(sensordb)):
        sensordb_entry=sensordb[i]
        sensorname=list(sensordb_entry.keys())[0]
        sensor_values=list(sensordb_entry.values())[0]
        #valid_sensortags=siteconfig[SENSORTAGS]
        sensorvalue=None
        timestamp='1970-01-01 00:00:00'
        for i  in range(0,len(sensor_values)):
            sensorentry=sensor_values[i]
            print('**************************')
            print(sensorentry)
            print('**************************')
            if 'sensortag' in sensorentry and sensorentry['sensortag'] == 'mC':
                sensorvalue=int(sensorentry['sensorvalue'])/1000
            elif 'sensortag' in sensorentry and sensorentry['sensortag'] == 'TEMP':
                sensorvalue=float(sensorentry['sensorvalue'])
            elif 'sensortag' in sensorentry and sensorentry['sensortag'] == 'celsius':
                sensorvalue=float(sensorentry['sensorvalue'])    
            elif 'timestamp' in sensorentry:
                timestamp=convert_timestamp(sensorentry['timestamp'])
        allSensors.append({"sensorname":sensorname,KEY_TEMP:sensorvalue,"time":timestamp})
    return allSensors

def get_group_temperatures_sensordb(site_config, sensor_config, sensordb):

    """
    Calculates the temperature per group based on sensor priority.
    
    Args:
        sensor_config (list): List of dictionaries defining groups and member priorities.
        sensordb (list): List of dictionaries containing sensor readings.
        
    Returns:
        dict: A dictionary {groupname: temperature_value} or {groupname: False}.
    """
    
    # Flatten the sensordb for easier lookup. 
    # The input is a list of single-key dicts: [{'sensorname': ["sensorvalue":..,"sensorvalue":..,"timestamp"]}, {'id2': [...]}]
    # We convert this to: {'sensorname': ["sensorvalue":..,"sensorvalue":..,"timestamp"]}, {'id2': [...]}
    sensor_data_map = {}
    for entry in sensordb:
        sensor_data_map.update(entry)
    # Define valid tags for temperature readings
    # Note: Added "TEMP" to support the 'ds1820-gang' example in your data
    valid_tags = site_config[KEY_SENSORTAGS]
    
    results = {}
    max_age_in_hours=int(site_config[KEY_MAX_AGE])

    # Loop though all groups
    for group in sensor_config:
        group_name = group[KEY_GROUPNAME]
        # Sort members by priority (converting string priority to int)
        # Assumes lower number = higher priority (e.g., 1 comes before 2)
        sorted_members = sorted(
            group[KEY_MEMBERS], 
            key=lambda x: int(x[KEY_PRIORITY])
        )
        # 3. Iterate through members to find the first available valid reading
        for sensor in sorted_members:
            if DEBUG_SENSORDB:
                print(f"Processing group: {group_name} Sensor: {sensor[KEY_NAME]}")
            sensor_name = sensor[KEY_NAME]
            scale = float(sensor[KEY_SCALE])

            # Check if this sensor exists in our current data
            if sensor_name in sensor_data_map:
                readings = sensor_data_map[sensor_name]
                if DEBUG_SENSORDB:
                    print(f'sensor_name: {sensor_name}',end=' ')
                    #print(readings)
                # Iterate through the list of reading dicts for this sensor
                # Typical structure of readings:
                # [{'sensortag': 'currenttemp', 'sensorvalue': '10187'}, {'timestamp': '23.10.2025 16:30:03'}]
                temp_found=False
                time_within_limit=False
                current_finding=None
                current_sensor=None
                # 
                # Loop trhoug all readings from one sensor
                #
                for reading in readings:
                    # We look for specific tags
                    if reading.get(KEY_SENSORTAG) in valid_tags:
                        try:
                            raw_value = float(reading[KEY_SENSORVALUE])
                            # Apply scaling
                            current_finding = raw_value / scale
                            temp_found=True
                            current_sensor=reading.get(KEY_SENSORTAG)
                            #break # Found valid tag for this sensor
                        except (ValueError, TypeError):
                            continue  
                    elif 'timestamp' in reading:
                        timestamp=convert_timestamp(reading[KEY_TIMESTAMP])
                        time_within_limit = is_timestamp_valid(reading[KEY_TIMESTAMP],max_age_in_hours)
                if DEBUG_SENSORDB:
                    print("current_sensor: ",end= ' ')
                    print(current_sensor,end= ' ')
                    print("sensor_name: ",end= ' ')
                    print(sensor_name,end= ' ')
                    print("temp found: ",end= ' ')
                    print(temp_found,end= ' ')
                    print("current_finding: ",end= ' ')
                    print(current_finding,end= ' ')
                    print("timestamp: ",end= ' ')
                    print(timestamp,end= ' ')
                    print("time_within_limit: ",end= ' ')
                    print(time_within_limit)
                # If we found a value for this high-priority sensor, 
                # stop looking at lower priority sensors for this group.
                # When found both temp value and valid time, add entry and skip to next group
                if time_within_limit and temp_found:
                    results[group_name]={KEY_TEMP:current_finding,KEY_TIMESTAMP:timestamp,KEY_TIMESTAMP:sensor_name}
                    break
                if not (time_within_limit and temp_found):
                    results[group_name]={KEY_TEMP:None}

    return results

def process_backup_groups(all_group_temp,sensor_config):
    for group_key in all_group_temp:
        #
        # Look up sensor config to find backup
        #
        print(group_key+' temp: '+str(all_group_temp[group_key][KEY_TEMP]))
        if all_group_temp[group_key][KEY_TEMP] is None:
            backup_sensor=None
            for sensors in sensor_config:
              if sensors[KEY_GROUPNAME] == group_key:
                   backup_sensor=sensors[KEY_BACKUP_GROUP]
                   break
            print(f"Using backup sensor {backup_sensor} for group: {group_key}")
            if backup_sensor is None:
                print(f"No backup sensor found for {group_key}")
            else:
                all_group_temp[group_key][KEY_TEMP]=all_group_temp[backup_sensor][KEY_TEMP]
                all_group_temp[group_key]=all_group_temp[backup_sensor]

def get_temp_from_sensordb(site_config, getAll=False):
    """
    opens sensor db amd returns temeratures in format:

    Returns all temperatures if getAll=True, else returns value based on priority within time
    """

    try:
            # Open and parse Config File
        with open(site_config[KEY_SENSORCONFIG], 'r') as f_config:
            sensor_config = json.load(f_config) 

        # Open and parse Sensor DB File
        with open(site_config[KEY_SENSORDB], 'r') as f_db:
            sensordb_data = json.load(f_db)
    except FileNotFoundError as e:
        return f"Error: Could not find file. {e}"
    except json.JSONDecodeError as e:
        return f"Error: Failed to decode JSON. Check file formatting. {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
        raise
    # Call the core logic
    if getAll:
        return get_all_temperatures(sensordb_data)
    else:
        max_age_int=int(site_config[KEY_MAX_AGE])
        return get_group_temperatures_sensordb(site_config,sensor_config,sensordb_data)
    

def convert_timestamp(timestamp_str):
    """
    Converts a timestamp from 'DD.MM.YYYY HH:MM:SS' 
    to 'MM/DD/YYYY, HH:MM:SS'.
    """
    try:
        # Parse the original format
        dt_object = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M:%S")
        
        # Format to the new style
        return dt_object.strftime("%m/%d/%Y, %H:%M:%S")
    except ValueError:
        print("convert_timestamp, value error")
        return None 
    
def is_timestamp_valid(ts_string, max_age_hours):
    """
    Checks if a timestamp is within the specified max age in hours relative to the current time.

    Args:
        timestamp_struct (dict): A dictionary containing the timestamp string.
                                 Example: { "timestamp": "19.11.2025 17:39:25" }
        max_age_hours (float): The maximum allowed age in hours.

    Returns:
        bool: True if the timestamp is more recent than max_age_hours, False otherwise.
              Returns False if parsing fails.
    """
    try:
        # Define the format matching "19.11.2025 17:39:25"
        # %d = Day, %m = Month, %Y = Year (4 digits), %H = Hour (24h), %M = Minute, %S = Second
        fmt = "%d.%m.%Y %H:%M:%S"
        
        # Parse the string into a datetime object
        ts_datetime = datetime.strptime(ts_string, fmt)
        
        # Get current time
        current_time = datetime.now()
        
        # Calculate the difference
        age = current_time - ts_datetime
        
        # Convert age to hours
        age_in_hours = age.total_seconds() / 3600

        # Check if age is negative (timestamp is in the future) or within the limit
        if age_in_hours < 0:
            print(f"Warning: Timestamp is in the future by {abs(age_in_hours):.2f} hours.")
            return True # Technically valid as it hasn't expired, or treat as invalid depending on needs
        return age_in_hours <= float(max_age_hours)

    except ValueError as e:
        print(f"Error parsing date: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred (is_timestamp_valid): {e}")
        return False
