import argparse
import glob
import json
import os
import platform
import time
from datetime import datetime

from const import (
    CONST_DEVICE_FILE_NAME,
    CONST_DEVICE_GLOB,
    CONST_LINUX_TEMP_FILE,
    CONST_SENSOR_BASE_DIR,
    CONST_WINDOWS_TEMP_FILE,
)

os.system("modprobe w1-gpio")
os.system("modprobe w1-therm")

temp_stat = {}
device_folder = glob.glob(CONST_SENSOR_BASE_DIR + CONST_DEVICE_GLOB)[
    0
]
device_file = device_folder + "/" + CONST_DEVICE_FILE_NAME


def write_temp_local(filename, temperature_status):
    with open(filename, "w") as output_file:
        output_file.write(temperature_status)


def read_temp_raw(raw_temp_file):
    try:
        with open(raw_temp_file, "r") as input_file:
            return input_file.readlines()
    except Exception as error:
        print(error)
        return False


def read_temp(filename):
    lines = read_temp_raw(filename)
    while lines[0].strip()[-3:] != "YES":
        time.sleep(0.2)
        lines = read_temp_raw(filename)
    equals_pos = lines[1].find("t=")
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2 :]
        return float(temp_string) / 1000.0


def get_default_temp_file():
    if platform.system().lower() == "linux":
        return CONST_LINUX_TEMP_FILE
    return CONST_WINDOWS_TEMP_FILE


def parse_args():
    parser = argparse.ArgumentParser(
        description="DS1820 temperature fetching program"
    )
    parser.add_argument(
        "--tempfile",
        default=get_default_temp_file(),
        type=str,
        help="File to store result",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    temp_stat["temp"] = read_temp(device_file)
    temp_stat["time"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    if args.tempfile != "-":
        write_temp_local(args.tempfile, json.dumps(temp_stat))
    print(json.dumps(temp_stat))


if __name__ == "__main__":
    main()
