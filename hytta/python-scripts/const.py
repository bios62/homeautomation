"""Shared constants for the Hytta Python programs."""

CONST_DEFAULT_TIME_ZONE = "Europe/Oslo"
CONST_DEFAULT_TIME_FORMAT = "%d.%m.%Y %H:%M:%S"
CONST_DEFAULT_NTP_SERVER = "no.pool.ntp.org"
CONST_DEFAULT_TIMESTAMP = "01.01.1970 00:00:00"
CONST_DEFAULT_HOSTNAME = ""
CONST_DEFAULT_IPADDRESS = ""
CONST_DEFAULT_PORT_NUMBER = 8080
CONST_DEFAULT_SENSOR_URI = "/sensor"
CONST_GET_SENSOR_URI = "/sensordata"
CONST_ISALIVE_URI = "/isalive"
CONST_SENSORDB_FILENAME = "sensorfile"
CONST_SENSOR_FUNCTION = "sensorfuntion"
CONST_SENSOR_HUM = "Humidity"
CONST_SENSOR_ID = "sensorid"
CONST_SENSOR_NAME = "objecttag"
CONST_SENSOR_TAG = "sensortag"
CONST_SENSOR_TEMP = "Temp"
CONST_SENSOR_TIME = "timestamp"
CONST_SENSOR_URI = "sensoruri"
CONST_SENSOR_VALUE = "sensorvalue"
CONST_SENSOR_VALUES = "sensors"
CONST_SERVER_HOSTNAME = "hostname"
CONST_SERVER_IPADDRESS = "ipaddress"
CONST_SERVER_NTP_SERVER = "ntp_server"
CONST_SERVER_PORT_NUMBER = "portnumber"
CONST_SERVER_TIME_FORMAT = "time_format"
CONST_SERVER_TIME_ZONE = "time_zone"
CONST_SIMPLE_SERVER_NAME = "Simple API Server"
CONST_SIMPLE_SERVER_VERSION = "120125 V1"
CONST_DEBUG_FLAG_COMMON = 0
CONST_DBG0 = 0b00000000
CONST_DBG1 = 0b00000001
CONST_DBG2 = 0b00000010
CONST_DBG4 = 0b00000100
CONST_DBG8 = 0b00001000
CONST_DBG16 = 0b00010000
CONST_DBG32 = 0b00100000
CONST_DBG64 = 0b01000000
CONST_DEVICE_GLOB = "28*"
CONST_DEVICE_FILE_NAME = "w1_slave"
CONST_LINUX_TEMP_FILE = "/u01/iot/localtempfile"
CONST_SENSOR_BASE_DIR = "/sys/bus/w1/devices/"
CONST_WINDOWS_TEMP_FILE = "g:\\demo_projects\\pi\\hytta\\config.json"
CONST_SODA_PASSWORD = "Mercedes450sl"
CONST_SODA_QUERY_BODY = (
    '{"$query":{},"$orderby":{"created_on":-1}}'
)
CONST_SODA_QUERY_URL = (
    "https://tn1tv18ynzxubz5-iosp.adb.eu-frankfurt-1."
    "oraclecloudapps.com/ords/iot/soda/latest/jiotlogs?"
    "action=query&limit=1&fields=all"
)
CONST_SODA_USERNAME = "iot"
