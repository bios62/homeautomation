#
#  Code for Autonomous Workshop
#
# (c) Inge Os Oracle, 2025
#
# Under Gnu GPL
#
import gc
import wifi  # should be first to reduce of memory issues
import time
import alarm
import time
import board
import neopixel
import ssl
import socketpool
import adafruit_requests
import adafruit_ahtx0
import adafruit_ntp
import supervisor
import microcontroller
import os
import json



#########################################################
#
# Constants
#
#########################################################

MEMORY_THRESHOLD = 2006000
MAX_ITERATIONS_BEFORE_RESTART = 1000

#
# Debug flags
#
PRINT_ERROR = 1
PRINT_DEBUG = 2
PRINT_INFO = 4
DEFAULT_DEBUG_LEVEL=PRINT_INFO

# Color and blink
AZURE=(0,255,255)
YELLOW=(255,255,0)
ORANGE=(255,64,0)
BLUE=(0,0,255)
WHITE=(255,255,255)
GREEN=(0,255,0)
RED=(255,0,0)
PURPLE=(255,0,255)
DARK=(0,0,0)
#
# Timing, duration of light
#
LIGHT0=0
LIGHT2=2
LIGHT5=5
LIGHT8=8
LIGHT10=10
LIGHT20=20
BRIGHTNES_FULL=255
BRIGHTNES_HALF=128
#
# Config Parameters
#
NET1_WIFI_SSID="net1_wifi_ssid"
NET1_WIFI_PASSWORD="net1_wifi_password"
NET2_WIFI_SSID="net2_wifi_ssid"
NET2_WIFI_PASSWORD="net2_wifi_password"
REST_URI = "rest_uri"
USE_NTP='use_ntp'
SENSOR_API= "sensor_API"
SENSOR_NAME = "objecttag"
SENSOR_TEMP='mC'
SENSOR_HUM='Humidity'
SENSOR_TIME='timestamp'
#SENSOR_TAG='sensortag'
SENSOR_VALUE='sensorvalue'
NETWORKS='networks'
NTP_SERVER="ntp_server"
DEFAULT_NTP_SERVER="no.pool.ntp.org"
DEFAULT_TIMESTAMP='01.01.1970 00:00:00'
DEBUG_LEVEL="debug_level"
LOOP_SLEEP_TIME = "loop_sleep_time"
DARK_MODE="dark_mode"

VERSION = "131125 V3.0"


#########################################################
#
#  Global values
#
#########################################################

ntp=None            # Global ntp object
debug_level=DEFAULT_DEBUG_LEVEL  # Set globally to preserve memory
config=None          # Set globally to preserve memory
pixel= None         # Set globally to preserve memory

#########################################################
#
# cleanup_memory
#
# Calls garbage collector,
# if debug flag is set, prints
# memfree before and anter GC call
#
# Parameters:
#   text    Label to be printed, no lable if None
#
#########################################################
def cleanup_memory(text=None):

    global debug_level

    if text is not None:
        print_debug("Memfree label: " + text,PRINT_DEBUG,supress=True)
    pregc_freemem = gc.mem_free()
    gc.collect()
    postgc_freemem = gc.mem_free()
    #if debug_level is not None and debug_level > 0:
    #    print(
    #        "Pre gc mem: " + str(pregc_freemem) + " post gc mem: " + str(postgc_freemem)
    #    )
    print_debug("Pre gc mem: " + str(pregc_freemem) + " post gc mem: " + str(postgc_freemem),PRINT_DEBUG)
    return postgc_freemem

#########################################################
#
# print_debug
#
# print depending of debug level
# if global config[DARK_MODE] is True, do nothing
#
# Parameters:
#   msg,        Message to be printent for a given debug_level
#   debug_level, defaults to PRINT_DEBUG, level for printing messgage
#                    Always print message for PRINT_ERROR
#   supress,    if True, don't print NL
# Globals
#   config[DARK_MODE],  Only print anyting if False
#########################################################
def print_debug(msg,level=PRINT_DEBUG,supress=False):

    # Do nothing if config[DARK_MODE]

    if config[DARK_MODE]:
        return
    
    # print '\n' if supress != true

    end_line='' if supress else '\n'

    if level == PRINT_ERROR:
        print(msg,end=end_line)
    elif level >= PRINT_DEBUG:
        print(msg,end=end_line)
    elif level >= PRINT_INFO:
        print(msg,end=end_line)


#########################################################
#
# post_to_rest
#
# Calls ORDS rest API hosted at Autonomous
# Using HTTPS POST, postin JSON payload
# The circiut python API has limited header support,
# Header Content-Type is not set
# The POST will not work if Content-Type application/JSON is required
#
# temperature value is in millicelcius from the device
#
# Parameters:
#   config,   DICT wih configuration data, including URL
#   sensorvalues,    DICT with value to be added to payload
#
#########################################################
def post_to_rest(config,sensorvalues):

    #
    # Create JSON payload
    #
    apiURL=apiURL=config[REST_URI].rstrip('/')+config[SENSOR_API]
    #
    #  Format #\payload = '{"objecttag":' + "{:.2f}".format(millicelsius / 1000) + "}"
    # payload = '{ "objecttag" :  "ESP32:Feather:031" , "sensors" : [ { "sensortag" : "mC", "sensorvalue" : "' + str(millicelsius) + '" }, { "sensortag" : "Humidity", "sensorvalue" : "' + str(hum) + '"}, { "sensortag" : "KMH", "sensorvalue" : "' + str(kmh) + '"} ] }'
    payload = '{"'+SENSOR_NAME+'":"'+config[SENSOR_NAME]+'","sensors" :'+json.dumps(sensorvalues)+'}'
    
    #
    # Clean memory before allocating socket resources
    #
    cleanup_memory()
    try:
        pool = socketpool.SocketPool(wifi.radio)
        requests = adafruit_requests.Session(pool, ssl.create_default_context())

    except:
        print_debug("\nrequests error - exception - 101",PRINT_ERROR)
        return -1
    #
    # Execute POST if request was successfully allocated
    #
    # Two types of error may occur, eiter a exception is thrown (network error)
    # or HTTP Error (HTTP-400 - HTTP-500)
    #
    print_debug('Posting to: '+ apiURL,PRINT_DEBUG)
    print_debug (payload,PRINT_DEBUG)
    try:
        # application/json
        headers = {"Content-Type": "application/json"}
        print_debug(("-" * 40),PRINT_DEBUG)
        response = requests.post(apiURL, headers=headers, data=payload)
        if response.status_code <=201:
            print_debug('Posted sucsessfully '+str(response.status_code),PRINT_INFO)
    except Exception as e:
        print_debug("\n HTTPS POST Exception",PRINT_DEBUG)
        print_debug(e,PRINT_DEBUG)
        return -1
    print_debug ("return from post",PRINT_DEBUG)
    return response.status_code


#########################################################
#
# connect_to_wifi
#
# Loops throug dictionary with list of possible
# Wifis and try them, If no one connects, returns False
#
#  Based on clobal variable wifi_networks
#
# Globals_
#   pixel, LED driver
#   config,  DICT with current config
#
#########################################################
def connect_to_wifi():

    global config
    global pixel

    wifi_networks=config[NETWORKS]
    wifi_found = False
    for wifi_net in wifi_networks:
        print_debug(
            "\n Connecting to Wi Fi network  "+wifi_networks[wifi_net]['wifinamename']+' '+wifi_networks[wifi_net]['ssid'],PRINT_INFO
        )
        try:
            wifi.radio.connect(
                wifi_networks[wifi_net]["wifinamename"], wifi_networks[wifi_net]["ssid"]
            )
            print_debug(f"\n Successfully connected to : {wifi_net}",PRINT_INFO)
            print_debug(f" Allocated IP address: {wifi.radio.ipv4_address}",PRINT_INFO)
            wifi_found = True
            break
        except Exception as e:
            print_debug("\n Connect to network - failed",PRINT_ERROR)
            print_debug(" Wifi Connect error:", PRINT_ERROR)
            print_debug(e,PRINT_ERROR)
        cleanup_memory()
    if not wifi_found:
        print_debug(" No able to connect to any Wifi\n Available WiFi networks:",PRINT_ERROR)
        printWifi()

    return wifi_found


#########################################################
#
# printWifi
#
# Prints visible SSIDs
#
#########################################################
def printWifi():
    for network in wifi.radio.start_scanning_networks():
        print(
            "\t%s\t\tRSSI: %d\tChannel: %d"
            % (str(network.ssid, "utf-8"), network.rssi, network.channel)
        )
    wifi.radio.stop_scanning_networks()

#########################################################
#
# set_color
#
# Based on the offset value the brightness of the color is reduced.
# Normally the clour component value are 255
# Get dark when done, if duration >0
#
# Parameters:
#   color,          tuple with RGB
#   brightness,     255 is max brightness, 0 is off 255-brightness is used to dim
#   duration,       sec, as float if duration == 0#
# Globals:
#   pixel, LED driver
#   config[DARK_MODE], if set do nothing
#########################################################
def set_color(color,duration,brightness=255):

    global pixel
    global config

    #
    # If dark mode is set, do nothing
    #
    if config[DARK_MODE] == True:
        return
    #
    # If black, turn off led
    #
    if color == DARK:
        pixel.fill(DARK)
        return
    
    # 
    # Adjust brightness
    #
    tlist=list(color)
    if brightness >0 :  # As we wxit with DARK, do nothing else if brightness = 0
        for i in range(len(tlist)):
            if tlist[i] >0:
                tlist[i]=tlist[i]-(255-brightness) if  tlist[i]-(255-brightness)>0 else 0
        color_adjusted=tuple(tlist)
        pixel.fill(color_adjusted)
        if duration == 0:
            return  # No go dark
        time.sleep(duration)
    #
    # Time expired, turn off
    #
    pixel.fill(DARK)


#########################################################
#
# blink_color, toggles between two colors
#
# Input variables: 
#
#   color1 and color2 to toggle, to have a dark blink effect, set color2 to DARK
#   brihtness, max light or dimmed. 0 = max light
#   the last stays on if stay_on=True
#
# Parameters:
#   color1,      first blink color
#   color2,      2. blink color
#   brightness,  brightness of blink
#   flash_time,  duration of each color
#   total_flashes,  total number of sequences with both lights
# Globals:
#   pixel,      LED driver
#       
#########################################################
def blink_color(color1,color2,brightness,flash_time,total_flashes, stay_on=False):
    #
    #  togle color total_flashes times
    #
    for i in range(0,total_flashes):
        set_color(color1,flash_time,brightness)
        set_color(color2,flash_time,brightness)
    if not stay_on: # Go dark
        set_color(DARK, 0, 0)

#########################################################
#
# init_pixel
#
# creates a pixel type object, required for working with the LED
#
#########################################################
def init_pixel():

    return neopixel.NeoPixel(board.NEOPIXEL, 1)

#########################################################
#
# get_config
#
# Read config from settings.toml
#
# Throws exception if config is missing
# and turns on  AZURE Blink
#
# Globals:
#   pixel,  LED driver
#   config, DICT with current config
#   debug_level
#
#########################################################
def get_config():

    global pixel
    global config
    global debug_level
    #
    #  Read Wifi setting for mandatory WiFi 
    #
    wifi_networks={}
    config={}
    #
    # Get network config , iterate and generate names. max 9 names
    #
    for i in range (1,9):
        wifi_ssid_label=NET1_WIFI_SSID.replace('1',str(i))
        wifi_password_label=NET1_WIFI_PASSWORD.replace('1',str(i))
        wifi_ssid = os.getenv(wifi_ssid_label)
        wifi_password = os.getenv(wifi_password_label)
        if wifi_ssid is None or wifi_password is None:
            break
        network_label='Net-'+str(i)
        wifi_networks[network_label]={"wifinamename": wifi_ssid, "ssid":wifi_password }
    if wifi_networks == {} :
        print_debug("Wifi SSID and Password not found in settings.toml",PRINT_ERROR)
        blink_color(AZURE,WHITE,BRIGHTNES_HALF,1.5,10,False)
        raise ValueError
    #
    #  Read additional wifsettings
    #
    wifi_ssid = os.getenv(NET2_WIFI_SSID)
    wifi_password = os.getenv(NET2_WIFI_PASSWORD)
    #
    #  Skip is either ssid or password is missing for 2. net
    #
    if not (wifi_ssid is None or wifi_password is None):
        wifi_networks['NET2']={"wifinamename": wifi_ssid, "ssid":wifi_password }
    config[NETWORKS]=wifi_networks
    #
    # Get REST URL 
    #
    config[REST_URI]=os.getenv(REST_URI)
    config[SENSOR_API]= os.getenv(SENSOR_API)
    config[SENSOR_NAME] = os.getenv(SENSOR_NAME)
    config[NTP_SERVER] = os.getenv(NTP_SERVER)
    config[LOOP_SLEEP_TIME] = os.getenv(LOOP_SLEEP_TIME)
    config[DEBUG_LEVEL] = os.getenv(DEBUG_LEVEL)
    dark_mode_param = os.getenv(DARK_MODE)
    use_ntp_param= os.getenv(USE_NTP)
    #
    #  Set default values for non mandatory marameters
    #

    # debug level

    if config[DEBUG_LEVEL] is None:
        config[DEBUG_LEVEL]=DEFAULT_DEBUG_LEVEL
    
    # Dark mode

    if dark_mode_param   is not None and dark_mode_param .upper() == 'TRUE':
        config[DARK_MODE]=True
    else:
        config[DARK_MODE]=False
    if config [NTP_SERVER] is None:
        config[NTP_SERVER] = DEFAULT_NTP_SERVER
    
    # use NTP
    if use_ntp_param is not None and use_ntp_param.upper() == 'ENABLED':
        config[USE_NTP]=True
    else:
        config[USE_NTP]=False
    
    # ntp_server

    if config [NTP_SERVER] is None:
        config[NTP_SERVER] = DEFAULT_NTP_SERVER
    #
    # Verify that all values are set
    #
    for config_key in config:
        if config[config_key] is None:
            print_debug("Mandatory setting "+config_key+" missing in settings.toml",PRINT_ERROR)
            blink_color(AZURE,WHITE,BRIGHTNES_HALF,1.5,10,False)
            raise ValueError   

#########################################################
#
# zero_pad
# Replacement for .zfill, missing in circiut python
# left pads string with '0'
#
# Parameters:
#   src,     Source string to be left padded with '0'
#   lenght,  total length of string to be padded. If string lenght 
#           equals or exceeds lenght, do nothing
#########################################################
def zero_pad(src,length=2):
    newstr=''
    for i in range(length-len(src)):
        newstr=newstr+'0'
    newstr=newstr+src
    return newstr

#########################################################
#
# get_NTP_time
#
# Globals:
#   ntp    global ntp object, initialized if None
#   config,  contains NTP server
# Returns:
#   ntp time in UTC, in format TIME_FORMAT='%d.%m.%Y %H:%M:%S'
#
#########################################################
def get_NTP_time():
    global ntp
    global config

    if config[USE_NTP] is False:
        return DEFAULT_TIMESTAMP
    try:
        pool = socketpool.SocketPool(wifi.radio)
        ntp = adafruit_ntp.NTP(pool, server=config[NTP_SERVER],tz_offset=0, cache_seconds=3600)
    
        current_time=ntp.datetime
        if current_time is None:
            return '01.01.1970 00:00:00'
        str_current_time=zero_pad(str(current_time.tm_mday))+'.'+ \
            zero_pad(str(current_time.tm_mon))+'.'+ \
            zero_pad(str(current_time.tm_year))+' '+ \
            zero_pad(str(current_time.tm_hour))+':'+ \
            zero_pad(str(current_time.tm_min))+':'+ \
            zero_pad(str(current_time.tm_sec))
    except Exception as e:
        print_debug("NTP failed",PRINT_ERROR)
        print_debug(e,PRINT_ERROR)
        str_current_time=DEFAULT_TIMESTAMP
    return str_current_time

#########################################################
#
# main
#
# Main procedure
# Endles loop, but runs until MAX_ITERATIONS_BEFORE_RESTART
# is reached. Reboot device when this threshold is met
#
# Globals:
#   ntp     global ntp object, initialized if None
#   config, contains NTP server
#   debug_level global debug level
#
#########################################################
def main():

    global pixel
    global debug_level
    global config

    # Default debug level, might be overridden by config file

    debug_level=DEFAULT_DEBUG_LEVEL   # default

    # print header info

    print(f"\nStart: Program version {VERSION} Microcontroller Device: ", end=" ")
    hostname = "QTPY" + str(int.from_bytes(microcontroller.cpu.uid, "little") >> 29)
    print(f"{hostname}")
    #
    # Initialize LED
    #
    pixel=init_pixel()

    #
    # Get config from settings.toml
    #
    get_config()    # config variable is set globally

    # Initial Boot messages, the device prints boot message post header 

    print_debug("\nDevice boot complete",PRINT_INFO)
    blink_color(WHITE,GREEN,BRIGHTNES_HALF,0.5,5,False)

    #
    # Set initial values
    #
    sleep_time=int(config[LOOP_SLEEP_TIME])
    debug_level=config[DEBUG_LEVEL]
    restartCnt = 0
    #
    # Initial memory cleanup
    #
    cleanup_memory()
    #
    # Collect and print board MAC address, if set
    #
    MACaddress = [hex(i) for i in wifi.radio.mac_address]
    print_debug(f"Device MAC address: {MACaddress}",PRINT_INFO)
    #
    #  Connect to wifi, reload if it fails
    #
    print_debug(f"Connecting to WiFi",PRINT_INFO)
    set_color(BLUE,LIGHT0,BRIGHTNES_HALF)  # Don't switch off
    connectWiFi = connect_to_wifi()
    if not connectWiFi:
        
        # No Wifi Connection
        
        print_debug("Connect to Wifi Network failed, review WiFi configuration",PRINT_ERROR)
        
        # The device will be relaoded, display available WiFi network
        
        printWifi()
        
        # Switch led deep sleep for 10 sec. and reload
        
        print_debug("\nNo Wifi Connection - no IP - RED - Sleep 10 sec and reboot",PRINT_ERROR)
        set_color(RED,LIGHT10,BRIGHTNES_FULL)
        print_debug("\nEnter deep Sleep for 10 sec",PRINT_ERROR)
        time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 10)
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)
        print_debug("\nDeep Sleep complete, reload",PRINT_ERROR)
        cleanup_memory()
        supervisor.reload()
    #
    #  Wifi OK
    #
    blink_color(BLUE,PURPLE,BRIGHTNES_HALF,0.5,5,False)
    #
    # Loop until reload
    #
    while True:

        # Message for each loop

        print_debug("\nLoop Start",PRINT_DEBUG)
        blink_color(WHITE,YELLOW,BRIGHTNES_HALF,2,5,False)  # Cause 10 sec. sleep
        current_memory = cleanup_memory()
        #
        # Everything is OK, go dark
        #
        set_color(DARK,0,0)
        #
        # If Current memory is below memor Threashold, continue
        # Otherwise reboot
        #
        if current_memory < MEMORY_THRESHOLD:
            print_debug(f"\nMemory restart ",PRINT_INFO)
            #
            # Restart device
            #
            blink_color(RED,YELLOW,BRIGHTNES_FULL,0.5,5,False)
            supervisor.reload()
        #
        #  If max number of iterations is reached, reboot
        #
        restartCnt = restartCnt + 1
        print_debug(f"restartCnt: {restartCnt} ",PRINT_DEBUG)
        if restartCnt > MAX_ITERATIONS_BEFORE_RESTART:
            print_debug("Max iterations reached, restart - restartCnt wait 20 sec",PRINT_INFO)
            cleanup_memory()
            set_color(WHITE,LIGHT2,BRIGHTNES_FULL)
            supervisor.reload()
        #
        # No reboot continue
        # Collect temp and hum from sensor
        # reboot in case of sensor failure
        #
        sensor_values=[]  
        try:
            i2c = board.STEMMA_I2C()
            aht20 = adafruit_ahtx0.AHTx0(i2c)
            sensor_values.append({SENSOR_TAG:SENSOR_TEMP,SENSOR_VALUE:str(int(aht20.temperature*1000))}) # Chop off after .
            sensor_values.append({SENSOR_TAG:SENSOR_HUM,SENSOR_VALUE:str(aht20.relative_humidity)})
            #
            # Append time if NTP is enabled
            #
            if config[USE_NTP]:
                sensor_values.append({SENSOR_TAG:SENSOR_TIME,SENSOR_VALUE:get_NTP_time()})
            print_debug('Temperature: '+str(aht20.temperature), PRINT_DEBUG)
            print_debug('Humidity: '+str(aht20.relative_humidity),PRINT_DEBUG)
        except Exception as e:
            print_debug("Collection of sensor values failed\n Rebooting",PRINT_ERROR)
            print_debug(e,PRINT_ERROR)
            blink_color(RED,YELLOW,BRIGHTNES_HALF,1.5,10,True)
            supervisor.reload()
        #
        # Post result over REST to apiserver
        #
        print_debug(("-" * 40),PRINT_INFO)
        cleanup_memory("Before Post To REST")
        post_status = post_to_rest(config,sensor_values)
        print_debug(f"HTTP Code after POST for TEMP: {str(post_status)}",PRINT_INFO)

        cleanup_memory("After Post to REST\n")
        print_debug(("-" * 40),PRINT_INFO)

        #
        #  Prosess POST status
        #

        if post_status == -1:  #  Generates relaod
            #
            #  Post generated Exception
            #
            print_debug("\nPost to IOT API - Exception ",PRINT_ERROR)
            cleanup_memory()
            set_color(RED,LIGHT20,BRIGHTNES_FULL)
            print_debug("\n Enter Deep Sleep",PRINT_ERROR)
            time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 5)
            alarm.exit_and_deep_sleep_until_alarms(time_alarm)
            print_debug("\n Deep Sleep complete",PRINT_ERROR)
            supervisor.reload()
        if post_status == 201 or post_status == 200:
            #
            # Post Successfull
            #
            print_debug(f"Post IOT API - OK - Sleeping {sleep_time} sec",PRINT_DEBUG)
            cleanup_memory()
            set_color(GREEN,LIGHT2,BRIGHTNES_FULL)
        else:
            #
            #  REST HTTP_STATUS != 200 or 201
            #
            print_debug("\nPost to IOT API with HTTP error: {post_status}",PRINT_ERROR)
            set_color(ORANGE,LIGHT10,BRIGHTNES_FULL)
            cleanup_memory()
        #
        # Set dark
        #
        set_color(DARK,0,0)
        time.sleep(sleep_time)
    # End While


##########################################
#  Main Entrypoint
#
##########################################
if __name__ == "__main__":
    main()

    