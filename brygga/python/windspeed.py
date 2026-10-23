import sys
import json
import argparse
import time
from dateutil.tz import gettz
from datetime import datetime
import requests
import urllib3
import random
from const import (
    CONST_CURRENT_SPEED as CURRENT_SPEED,
    CONST_CONFIGFILE as CONFIGFILE,
    CONST_DATE as DATE,
    CONST_DATE_INDEX as DATE_INDEX,
    CONST_DEBUG_LEVEL as DEBUG_LEVEL,
    CONST_DBG_LEVEL_GENERIC as DBG_LEVEL_GENERIC,
    CONST_DBG_LEVEL_LOG as DBG_LEVEL_LOG,
    CONST_DBG_LEVEL_STATS as DBG_LEVEL_STATS,
    CONST_DEVIATION as DEVIATION,
    CONST_DIRECTION_INDEX as DIRECTION_INDEX,
    CONST_HOURS_DAY as HOURS_DAY,
    CONST_INFILE as INFILE,
    CONST_ITERATIONS as ITERATIONS,
    CONST_LOGFILE as LOGFILE,
    CONST_MAX_ERROR as MAX_ERROR,
    CONST_MAX_HOUR_NLU as MAX_HOUR_NLU,
    CONST_MAX_ITER as MAX_ITER,
    CONST_MAX_LAST_DAY as MAX_LAST_DAY,
    CONST_MAX_LAST_HOUR as MAX_LAST_HOUR,
    CONST_MAX_LAST_MINUTE as MAX_LAST_MINUTE,
    CONST_MAX_LAST_SECOND as MAX_LAST_SECOND,
    CONST_MINUTES_HOUR as MINUTES_HOUR,
    CONST_OUTFILE as OUTFILE,
    CONST_POST_INTERVAL as POST_INTERVAL,
    CONST_POST_INTERVAL_SECONDS as POST_INTERVAL_SECONDS,
    CONST_POST_URL as POST_URL,
    CONST_SCAN_TIME as SCAN_TIME,
    CONST_SECONDS_MINUTE as SECONDS_MINUTE,
    CONST_SERIAL_PORT as SERIAL_PORT,
    CONST_SPEED_INDEX as SPEED_INDEX,
    CONST_TIME_INDEX as TIME_INDEX,
)

#
# general doc
# https://www.hwhardsoft.de/english/projects/rs485-shield/
# https://www.hwhardsoft.de/app/download/11541173297/Application+Note+NMEA+0183+Rev+A.pdf?t=1662369499

#
# global values
#
serial_port = "/dev/serial0"

#
#  Globals

config_parameters = [
    [SERIAL_PORT, None, False, "device file serial port"],
    [DEVIATION, None, False, "deviation from North"],
    [DEBUG_LEVEL, None, True, "1 generic, 2 log 4, stats"],
    [POST_URL, None, False, "URL to POST API"],
    [
        ITERATIONS,
        None,
        True,
        "max number of iterations, 0=indefinite",
    ],
    [INFILE, None, False, "if set, runs as simulatior mode"],
    [OUTFILE, None, False, "if set log/debug"],
    [CONFIGFILE, None, False, "configfile"],
    [POST_INTERVAL, None, False, "Post Interval"],
]


# current_value = None

error_wait_time = 5

#
# Data structures:
#
#    hour_records = []  one pr. hour last 24 hours
#    minute_records = []  one pr minute last hour
#    second_records = []  one pr second last minute
#    intermediate_records = []  one last chunk of data
#
#   speed record

##########################################################################
# class MeteringException
##########################################################################


class MeteringException(Exception):
    """MeteringException
    Attributes:
            message -- explanation of the error
    """

    def __init__(self, message="Meetering Exception raised"):
        self.message = message
        print(message)
        super().__init__(self.message)


#######################################################################
#
#  Scan records for highest value
#
#  max_records used for varying sized records, default None
#
#  Return record with hoghets value. Only positive values are regared
#
#######################################################################
def scan_records(records, max_records=None):
    current_max_speed = 0
    current_max_speed_index = 0

    #
    # Find total_records to process
    #
    total_records = (
        len(records) if max_records is None else max_records
    )

    # Loop trhoug all records and find highets value

    for i in range(0, total_records):
        if records[i][SPEED_INDEX] > current_max_speed:
            current_max_speed = records[i][SPEED_INDEX]
            current_max_speed_index = i
    return current_max_speed_index


#######################################################################
#
#  load_config
#
# Parses commandline, reads and loads config file
# Parses configfile, and if successfull, return config dict
#
# If load of configfile fails, exit run
#
#######################################################################
def load_config():

    #
    # Parse command line
    #
    global config_parameters
    args_parser = argparse.ArgumentParser(
        description="Windspeed tracker"
    )
    for arg in config_parameters:
        if not arg[2]:  # str type
            args_parser.add_argument(
                "--" + arg[0], default=arg[1], type=str, help=arg[3]
            )
        else:  # Int type
            args_parser.add_argument(
                "--" + arg[0], default=arg[1], type=int, help=arg[3]
            )
    args = args_parser.parse_args()
    print(args)

    if args.configfile is not None:
        #
        #  load config file
        #
        try:
            config_file = open(args.configfile)
        except Exception as ioError:
            print(
                "Load of configuration file: "
                + args.configfile
                + " failed"
            )
            exit(1)
        try:
            config = json.load(config_file)
            print(config)
            config_file.close()
        except Exception as ConfigError:
            print(
                "JSON Parse of configuration file: "
                + args.configfile
                + " failed"
            )
            exit(1)
    else:
        config = {}
    #
    # Set some defaults
    #
    if OUTFILE not in config:
        config[OUTFILE] = None
    if INFILE not in config:
        config[INFILE] = None
    if DEVIATION not in config:
        config[DEVIATION] = 0
    if POST_INTERVAL not in config:
        config[POST_INTERVAL] = POST_INTERVAL_SECONDS
    if DEBUG_LEVEL not in config:
        config[DEBUG_LEVEL] = 4
    #
    # cmdline overrules config file
    #
    d_args = vars(args)
    for argname in d_args:
        if d_args[argname] is not None:
            config[argname] = d_args[argname]
    return config


"""
#
#  max_last_time
#
#  Scans data as follows:
#  if hour is None scann all for max wind speed, omitt an record older than 24 hours
#  if hour is set, scan only values within the hour
#
def max_last_time(second_records, current_time_epoc, hour_of_day=None):

    max_speed = 0
    max_index = 0

    for i in range(0, MAX_HOUR - 1):
        #
        # Get the hour of current time
        #
        recorded_time = second_records[i][TIME_INDEX]
        recorded_hour = datetime.fromtimestamp(recorded_time).hour
        if recorded_time == 0:  # Skip uninitialized records
            if recorded_time > current_time_epoc - (
                3600 * 24 + 1
            ):  # Skip if record is to old, thisone is within 24 ours
                if hour_of_day is None:
                    if max_speed < second_records[i][SPEED_INDEX]:
                        max_speed = second_records[i][SPEED_INDEX]
                        max_index = i
                elif recorded_hour == hour_of_day:  # Only scan time from a given hour
                    if max_speed < second_records[i][SPEED_INDEX]:
                        max_speed = second_records[i][SPEED_INDEX]
                        max_index = i
    return max_index
"""


def save_property(siteid, property_name, property_value, site_config):
    #
    # Globals
    #
    #
    # Saving to endpoint
    #
    # api-endpoint
    debug_flag = 1
    headers = {"content-type": "application/json"}
    # headers = {"content-type": "application/json", "Authorization": "<auth-key>" }
    payload = {}
    payload["siteid"] = siteid
    payload["logname"] = property_name
    payload["logvalue"] = property_value
    apiURL = site_config["iotstatsURL"]
    if (
        site_config["iotstatscloud"] == "iosp"
        or site_config["iotstatscloud"] == "apex-evry"
        or site_config["iotstatscloud"] == "iosjump"
    ):
        data = json.dumps(payload)
        r = requests.post(apiURL, headers=headers, data=data)
        print_debug(apiURL, debug_flag)
        print_debug(headers, debug_flag)
        print_debug(data, debug_flag)
        print_debug(r.status_code, debug_flag)
        if r.status_code > 201:
            print("Failed with Status code: " + str(r.status_code))
            print(apiURL)
            print("Payload: ")
            print(data)
        else:
            print_debug(
                "Sucessfully saved property: " + str(r.status_code),
                debug_flag,
            )
            print(
                "Sucessfully saved property: "
                + property_name
                + " value: "
                + property_value
                + " http Status: "
                + str(r.status_code)
            )
    elif (
        site_config["iotstatscloud"] == "one.com"
    ):  # Not maintained fro a while......
        apiURL += urllib.parse.urlencode(payload)
        r = requests.get(apiURL, headers=headers)
        print_debug(r.status_code, debug_flag)
        if r.status_code > 200:
            print(r.text)
            print(r.status_code)


def print_debug(mld, dbgflag):
    print("#######################################")
    print(mld)


#
#  Save the data to a SODA structure in one REST call
#
def save_soda(stats, site_config):
    headers = {
        "content-type": "application/json",
        "Authorization": "<auth-key>",
    }
    data = json.dumps(stats)

    #
    #  Post payload with sodaURL
    #
    r = requests.post(
        site_config["sodaURL"],
        headers=headers,
        auth=(site_config["sodauser"], site_config["sodapwd"]),
        data=data,
    )
    print_debug(r.status_code, DBG16)
    if r.status_code > 201:
        print(r.text)
        print(r.status_code)
    else:
        print("SODA POST Success: ")
        print(str(r.text))


#
#  post_results
#  save the results to file
#
#  Need to change, to max_speed, last_min, last _hour, last day
def post_results(
    file_name,
    current_time,
    current_speed_record,
    intermediate_max_speed,
    second_max_speed,
    minute_max_speed,
    hour_max_speed,
    site_config,
):

    result = {}
    result[DATE] = current_time.strftime("%H:%M:%S %d.%m.%Y ")
    result[CURRENT_SPEED] = current_speed_record
    result[MAX_LAST_SECOND] = intermediate_max_speed
    result[MAX_LAST_MINUTE] = second_max_speed
    result[MAX_LAST_HOUR] = minute_max_speed
    result[MAX_LAST_DAY] = hour_max_speed

    """
    if file_name is None:
        print(json.dumps(result, indent=2))
    else:
        f = open(file_name, "a")
        f.write(json.dumps(result, indent=2))
        f.write("\n")
        f.close()
    save_property('brygga','current_speed',current_speed_record[2],site_config)
    save_property('brygga','current_direction',current_speed_record[1],site_config)

    save_property('brygga','max_speed_second',intermediate_max_speed[2],site_config)
    save_property('brygga','max_direction_second',intermediate_max_speed[1],site_config)

    save_property('brygga','max_speed_minute',second_max_speed[2],site_config)
    save_property('brygga','max_direction_minute',second_max_speed[1],site_config)

    save_property('brygga','max_speed_hour',minute_max_speed[2],site_config)
    save_property('brygga','max_direction_hour',minute_max_speed[1],site_config)

    save_property('brygga','max_speed_day',day_max_speed[2],site_config)
    save_property('brygga','max_direction_day',day_max_speed[1],site_config)
    """
    save_property(
        "brygga",
        "current_speed",
        json.dumps(current_speed_record),
        site_config,
    )

    save_property(
        "brygga",
        "max_speed_second",
        json.dumps(intermediate_max_speed),
        site_config,
    )

    save_property(
        "brygga",
        "max_speed_minute",
        json.dumps(second_max_speed),
        site_config,
    )

    save_property(
        "brygga",
        "max_speed_hour",
        json.dumps(minute_max_speed),
        site_config,
    )

    save_property(
        "brygga",
        "max_speed_day",
        json.dumps(hour_max_speed),
        site_config,
    )


#
#
#

init_dir = 0
init_speed = 0


def dummy_data(i):
    global init_dir
    global init_speed

    if init_speed == 0:
        init_dir = random.randint(0, 360)
        init_speed = (random.randint(0, 100)) / 10

    if i % 100 == 0:
        init_dir = random.randint(0, 360)
        init_speed = (random.randint(0, 100)) / 10

    speed_adjust = (random.randint(0, 1000)) / 100
    speed_sign_adjust = random.randint(0, 2)

    if speed_sign_adjust % 2 == 0:
        speed = init_speed + speed_adjust
    else:
        speed = init_speed - speed_adjust

    if speed < 0:
        speed = speed * (-1)

    str_speed = "{:.2f}".format(speed)
    dir_adjust = random.randint(0, 36)

    dir_sign_adjust = random.randint(0, 2)
    if dir_sign_adjust % 2 == 0:
        dir = init_dir + dir_adjust
    else:
        dir = init_dir - dir_adjust
    dir = dir if dir > 0 else 360 - dir
    dir = dir if dir < 360 else dir - 360

    current_metering = (
        "$WIMWV," + str(dir) + ",R," + str_speed + ",N,A*2A"
    )

    return current_metering


#
#  dbg mod 4 hour dump
#  dbg mod 2 = 8 print for each message
#  dbg mod 2 = 0 print for each processing interval
#
def main():
    """main"""
    #
    print("Starting wind sensor")
    #
    # Parse args
    #
    """
    arg_parser = argparse.ArgumentParser(description="Wind speed sensor reader")
    arg_parser.add_argument(
        "--outfile", default=None, type=str, help="file with last sample"
    )
    arg_parser.add_argument(
        "--debuglevel", default=0, type=int, help="file with last sample"
    )
    arg_parser.add_argument(
        "--infile", default=None, type=str, help="inputfile, trigegrs simulation mode"
    )
    arg_parser.add_argument(
        "--iterations", default=None, type=int, help="simulation mode Y/N"
    )
    args = arg_parser.parse_args()
    dbg = args.debuglevel
    """
    config = load_config()
    # print(json.dumps(config, indent=2))
    dbg = config[DEBUG_LEVEL]

    #
    # remove post file
    #
    print(config)
    if not config[OUTFILE] is None:
        f = open(config[OUTFILE], "w")
        f.close()
    #
    #  check for simulation mode
    #
    is_raspberry_pi = config[INFILE] is None
    if is_raspberry_pi:
        if config[SERIAL_PORT] is None:
            print("Serial port is not set, exiting")
            return
        import serial

    #
    # Iterations
    #
    if config[ITERATIONS] is None:
        maximum_iterations = MAX_ITER
    else:
        maximum_iterations = config[ITERATIONS]
    #
    # Deviation
    #
    deviation = int(config[DEVIATION])
    #
    # Data set initalization
    #
    hour_records = []
    minute_records = []
    second_records = []
    intermediate_records = []

    #
    #  initialize 24 hour records
    #
    for i in range(0, HOURS_DAY):
        current_speed_record = [0, 0, 0.0]
        hour_records.append(current_speed_record)
    #
    #  initialize minute records
    #
    for i in range(0, SECONDS_MINUTE):
        current_speed_record = [0, 0, 0.0]
        minute_records.append(current_speed_record)
    #
    #  initialize second records
    #
    for i in range(0, MINUTES_HOUR):
        current_speed_record = [0, 0, 0.0]
        second_records.append(current_speed_record)
    #
    # initialize intermediate_records
    #
    intermediate_records.append([0, 0, 0.0])
    #
    # current timezone
    #
    tz = gettz("Europe/Oslo")

    # current_epoctime = int(time.time())
    # pythonTime = datetime.fromtimestamp(current_epoctime, tz=tz)
    # print(pythonTime.strftime("%Y-%m-%d %H:%M:%S"))

    # Open serial
    # Candidate for try Except
    ser = None
    #
    # with serial.Serial(serial_port, baudrate=4800, timeout=1) as ser:
    #
    # j = 0
    if is_raspberry_pi:
        source = serial.Serial(serial_port, baudrate=4800, timeout=1)
    else:
        source = open(config[INFILE], "r")

    with source as ser:

        # if not is_raspberry_pi:
        #    time.sleep(1)
        #
        # Initialize counters, for time flip
        #
        last_time = 0
        last_minute = 0
        last_hour = 0
        last_second = 0
        error_count = 0
        sec_index = 0
        random_time_counter = 0
        last_post_epoc_time = 0
        intermediate_counter = 0
        total_seconds = 0
        #
        # Initialize current minimums
        #
        #
        #  Process all messages in indefinite loop as follows:
        #  - read the message and sanity check it
        #  - Read time and convert time to timedate
        #  - If the second value has flipped process each second value
        #    Add to second storage second_records
        #  - If the minute value has flipped scan hour and find highest value within 24 hours, and within last hour
        #    Clean out any value older than 24 hours
        #  - If the hour has flipped
        #    Find the maximum value and update the hour in hour_records based on hour number
        #
        i = 0
        start_epoctime_nlu = int(time.time())
        start_index = -1
        current_epoctime = int(time.time())
        if dbg & DBG_LEVEL_LOG:
            logfile = open(LOGFILE, "w")
        while True:
            i += 1
            #
            #  Read the current value
            #
            if is_raspberry_pi:
                #
                #  Collect current timestamp
                #
                current_epoctime = int(
                    time.time()
                )  # Will be epoc time in second, ms is cut off
                new_metering = (
                    ser.readline()
                    .decode("ascii", errors="replace")
                    .strip("\n")
                )
                current_metering = new_metering.split(",")
            else:
                # new_metering = dummy_data(i)
                new_metering = ser.readline().strip("\n")
                current_metering = new_metering.split(",")
                if random_time_counter == 0:
                    random_time_counter = random.randint(0, 7)
                    current_epoctime = current_epoctime + 1
                else:
                    random_time_counter = random_time_counter - 1
            #
            # Get current time in datetime format
            #
            current_time = datetime.fromtimestamp(
                current_epoctime, tz=tz
            )
            if dbg & DBG_LEVEL_LOG:
                logfile.write(
                    current_time.strftime("%Y-%m-%d %H:%M:%S")
                    + " , "
                    + new_metering
                    + "\n"
                )
            #
            # Sanity check reading
            #
            #  Format  $WIMWV,283,R,0,N,A*2A
            #  1 and 3 contain real values
            #
            try:
                #
                #  Verify if valid reading and terminat of number of errors exceeds MAX_ERROR
                #
                if (
                    current_metering is None
                    or len(current_metering) < 6
                ):
                    error_count += 1
                    print(error_count)
                    if error_count > MAX_ERROR:
                        error_count = 0
                        time.sleep(error_wait_time)
                        raise MeteringException(
                            "Exessive read error, sleeping for "
                            + str(error_wait_time)
                            + " seconds"
                        )
                else:  # Error not encountered
                    #
                    # Reset Error Count
                    #
                    error_count = 0
                    #
                    # Check if reading are convertible
                    #
                    try:
                        current_direction = (
                            int(current_metering[1]) + deviation
                        )  # add direction
                        if current_direction > 360:
                            current_direction -= 360
                        if current_direction < 0:
                            current_direction += 360
                        #
                        #  Correct direction for deviation from North
                        #
                        current_speed = float(
                            current_metering[3]
                        )  # add speed
                        current_speed_record = [
                            current_epoctime,
                            current_direction,
                            current_speed,
                        ]
                    except:
                        raise MeteringException(
                            "Number conversion error"
                        )
                    #
                    # Collect max value from from last stream
                    # Prior stream is already collected
                    # if intermediate_counter == 0, start of new collection, 0 is preallocated
                    #
                    if dbg & DBG_LEVEL_LOG == 1:
                        print(json.dumps(current_speed_record))
                    if current_time.second == last_second:
                        #
                        # No second flip
                        #
                        if (
                            len(intermediate_records)
                            <= intermediate_counter
                        ):
                            intermediate_records.append(
                                current_speed_record
                            )
                        else:
                            intermediate_records[
                                intermediate_counter
                            ] = current_speed_record
                        intermediate_counter += 1
                        total_seconds += 1
                    else:
                        #
                        # Second flip
                        #
                        last_second = current_time.second
                        if dbg & DBG_LEVEL_LOG == 1:

                            print("New Second ", end="")
                            print(current_time.hour, end="")
                            print(end=":")
                            print(current_time.minute, end="")
                            print(end=":")
                            print(current_time.second, end="  ")
                            print(current_metering)

                        #
                        # Process prior data
                        #
                        if (
                            current_time.minute != last_minute
                        ):  # New minute reading
                            #
                            #  Flip Minute
                            #
                            # Scan second records to find and record max_speed last_minute
                            #
                            new_max_speed = scan_records(
                                second_records
                            )
                            minute_records[current_time.minute] = (
                                second_records[new_max_speed]
                            )
                            last_minute = current_time.minute
                            # print("Max speed last minute: ", end=" ")
                            # print(minute_records[current_time.minute])
                        if current_time.hour != last_hour:
                            #
                            # Flip Hour
                            #
                            # New hour reading
                            # Scan minute records to find and record max_speed last_minute
                            #
                            new_max_speed = scan_records(
                                minute_records
                            )
                            hour_records[current_time.hour] = (
                                minute_records[new_max_speed]
                            )
                            last_hour = current_time.hour
                            # print("Max speed last hour: ", end=" ")
                            # print(hour_records[current_time.hour])
                        #
                        # Process news second
                        #

                        #
                        # Find highets speed in the intermediate records
                        #

                        current_max_speed = scan_records(
                            intermediate_records, intermediate_counter
                        )
                        #
                        # reset immediate counter
                        #
                        last_intermediate_counter = (
                            intermediate_counter
                        )
                        intermediate_counter = 0
                        #
                        # Preserve the last speed for the last second
                        #
                        second_records[last_second] = (
                            intermediate_records[current_max_speed]
                        )
                        #
                        # Check if data should be posted
                        #
                        if (
                            current_epoctime - last_post_epoc_time
                            > int(config[POST_INTERVAL])
                        ):
                            #
                            # Find max values and current reading
                            #
                            last_post_epoc_time = current_epoctime
                            max_last_second = scan_records(
                                intermediate_records,
                                last_intermediate_counter,
                            )
                            max_last_minute = scan_records(
                                second_records
                            )
                            max_last_hour = scan_records(
                                minute_records
                            )
                            max_last_24hours = scan_records(
                                hour_records
                            )
                            post_results(
                                config[OUTFILE],
                                current_time,
                                current_speed_record,
                                intermediate_records[max_last_second],
                                second_records[max_last_minute],
                                minute_records[max_last_hour],
                                hour_records[max_last_24hours],
                                config,
                            )

            except MeteringException as e:
                print(e)
            # except Exception as e:
            #    print(e)
            #
            #  Terminate "endless loop" if maximum_iterations is non zero
            #
            if (
                maximum_iterations > 0
                and total_seconds >= maximum_iterations
            ):
                break
    #
    # Some stats....
    #
    print("total rows: " + str(i))
    #
    #  Dump results
    #
    if dbg & DBG_LEVEL_LOG:
        logfile.close()
        f = open("result_sec.txt", "w")
        f.write("current record\n")
        f.write(json.dumps(current_speed_record))
        f.write("\n")
        f.write("intermediate records\n")
        intermediates = (
            (intermediate_counter - 1)
            if intermediate_counter > 0
            else 0
        )
        for i in range(0, intermediates):
            f.write(json.dumps(current_speed_record))
            f.write("\n")
        f.write("second records\n")
        f.write(json.dumps(current_speed_record))
        f.write("\n")
        f.write("minute records\n")
        f.write(json.dumps(second_records))
        f.write("\n")
        f.write("hour records\n")

        f.write(json.dumps(minute_records))
        f.write("\n")
        f.write("hour24 records\n")
        f.write(json.dumps(hour_records))
        f.write("\n")

        f.close()
    print("Terminated due to max iterations")


if __name__ == "__main__":
    main()
    seed = int(time.time()) % 1000
    random.seed(seed)
