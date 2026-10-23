import glob
import os
import time

from const import (
    CONST_DEVICE_FILE_NAME,
    CONST_DEVICE_GLOB,
    CONST_SENSOR_BASE_DIR,
    CONST_TEMP_OFFSET,
)

os.system("modprobe w1-gpio")
os.system("modprobe w1-therm")

device_folder = glob.glob(CONST_SENSOR_BASE_DIR + CONST_DEVICE_GLOB)[
    0
]
device_file = device_folder + "/" + CONST_DEVICE_FILE_NAME


def read_temp_raw():
    with open(device_file, "r") as input_file:
        return input_file.readlines()


def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != "YES":
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find("t=")
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2 :]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c + CONST_TEMP_OFFSET, temp_f


def main():
    current_temp = read_temp()
    print(current_temp[0])


if __name__ == "__main__":
    main()
