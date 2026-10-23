import json
import os
from datetime import datetime

# from common import *

sensordb = None


def get_temp_for_groupV2(site_config, group, max_age_in_hours):

    global sensordb
    #
    if sensordb is None:
        try:
            # Open and parse Config File
            with open(config_filename, "r") as f_config:
                config_data = json.load(f_config)

            # Open and parse Sensor DB File
            with open(sensordb_filename, "r") as f_db:
                sensordb_data = json.load(f_db)
        except FileNotFoundError as e:
            return f"Error: Could not find file. {e}"
        except json.JSONDecodeError as e:
            return f"Error: Failed to decode JSON. Check file formatting. {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"
    #
    # Sensordb is now initialized with proper values
    #


def get_all_temperatures(sensordb):
    """
    Converts sensordb to a list ov sensors name,values,timesatmt in converted format

    Args:
        sensordb (list): List of dictionaries containing sensor readings.

    Returns:
        list: A list of dictionary {sensorname: temperature_value:timestamp} timestamp in format "%m/%d/%Y, %H:%M:%S"
    """
    allSensors = []
    for i in range(0, len(sensordb)):
        sensordb_entry = sensordb[i]
        sensorname = list(sensordb_entry.keys())[0]
        sensor_values = list(sensordb_entry.values())[0]
        valid_sensortags = ["mC", "TEMP", "currenttemp"]
        sensorvalue = None
        timestamp = "1970-01-01 00:00:00"
        for i in range(0, len(sensor_values)):
            sensorentry = sensor_values[i]
            if (
                "sensortag" in sensorentry
                and sensorentry["sensortag"] == "mC"
            ):
                sensorvalue = int(sensorentry["sensorvalue"]) / 1000
            elif (
                "sensortag" in sensorentry
                and sensorentry["sensortag"] == "TEMP"
            ):
                sensorvalue = float(sensorentry["sensorvalue"])
            elif (
                "sensortag" in sensorentry
                and sensorentry["sensortag"] == "currenttemp"
            ):
                sensorvalue = int(sensorentry["sensorvalue"]) / 1000
            elif "timestamp" in sensorentry:
                timestamp = convert_timestamp(
                    sensorentry["timestamp"]
                )
        allSensors.append(
            {
                "sensorname": sensorname,
                "temp": sensorvalue,
                "time": timestamp,
            }
        )
    return allSensors


def get_group_temperaturesV2(
    sensor_config, sensordb, max_age_in_hours
):
    """
    Calculates the temperature per group based on sensor priority.

    Args:
        sensor_config (list): List of dictionaries defining groups and member priorities.
        sensordb (list): List of dictionaries containing sensor readings.

    Returns:
        dict: A dictionary {groupname: temperature_value} or {groupname: False}.
    """

    # 1. Flatten the sensordb for easier lookup.
    # The input is a list of single-key dicts: [{'id1': [...]}, {'id2': [...]}]
    # We convert this to: {'id1': [...], 'id2': [...]}
    sensor_data_map = {}
    for entry in sensordb:
        sensor_data_map.update(entry)

    # Define valid tags for temperature readings
    # Note: Added "TEMP" to support the 'ds1820-gang' example in your data
    valid_tags = ["mC", "currenttemp"]

    results = {}

    for group in sensor_config:
        group_name = group["groupname"]

        # 2. Sort members by priority (converting string priority to int)
        # Assumes lower number = higher priority (e.g., 1 comes before 2)
        sorted_members = sorted(
            group["members"], key=lambda x: int(x["priority"])
        )

        final_value = False
        # 3. Iterate through members to find the first available valid reading
        for member in sorted_members:
            sensor_name = member["name"]
            scale = float(member["scale"])

            # Check if this sensor exists in our current data
            if sensor_name in sensor_data_map:
                readings = sensor_data_map[sensor_name]
                # Iterate through the list of reading dicts for this sensor
                timestamp = "xxxx-xx-xx xx:xx:xx"
                for reading in readings:
                    # We look for specific tags
                    if reading.get("sensortag") in valid_tags:
                        try:
                            raw_value = float(reading["sensorvalue"])
                            # Apply scaling
                            final_value = raw_value / scale

                            # break # Found valid tag for this sensor
                        except (ValueError, TypeError):
                            continue
                    elif "timestamp" in reading:
                        timestamp = convert_timestamp(
                            reading["timestamp"]
                        )
            # If we found a value for this high-priority sensor,
            # stop looking at lower priority sensors for this group.
            if final_value is not False:
                break
            final_values = {"temp": final_value, "time": timestamp}
        results[group_name] = final_values

    return results


def process_temperature_files(
    config_filename, sensordb_filename, getAll=False
):
    """
    Wrapper: Opens files, parses JSON, and calls the calculation logic.
    """
    try:
        # Open and parse Config File
        with open(config_filename, "r") as f_config:
            config_data = json.load(f_config)

        # Open and parse Sensor DB File
        with open(sensordb_filename, "r") as f_db:
            sensordb_data = json.load(f_db)
    except FileNotFoundError as e:
        return f"Error: Could not find file. {e}"
    except json.JSONDecodeError as e:
        return f"Error: Failed to decode JSON. Check file formatting. {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
        # Call the core logic
    if getAll:
        return get_all_temperatures(sensordb_data)
    else:
        return get_group_temperatures(config_data, sensordb_data)


def convert_timestamp(timestamp_str):
    """
    Converts a timestamp from 'DD.MM.YYYY HH:MM:SS'
    to 'MM/DD/YYYY, HH:MM:SS'.
    """
    try:
        # Parse the original format
        dt_object = datetime.strptime(
            timestamp_str, "%d.%m.%Y %H:%M:%S"
        )

        # Format to the new style
        return dt_object.strftime("%m/%d/%Y, %H:%M:%S")
    except ValueError:
        return None


# --- Test Execution with provided data ---
def test_data():
    # Configuration Data
    config_data = [
        {
            "groupname": "gang",
            "members": [
                {"name": "ds1820-gang", "priority": "1", "scale": 1},
                {"name": "weewx", "priority": "3", "scale": 1},
                {"name": "ESP32_BAD", "priority": "2", "scale": 1000},
            ],
        },
        {
            "groupname": "stue",
            "members": [
                {"name": "temp-stue", "priority": "2", "scale": 1000},
                {
                    "name": "arduino-stue",
                    "priority": "1",
                    "scale": 1000,
                },
            ],
        },
    ]

    # Sensor Data
    sensor_db_data = [
        {
            "ds1820-gang": [
                {"sensortag": "TEMP", "sensorvalue": "10.125"},
                {"timestamp": "19.11.2025 17:39:05"},
            ]
        },
        {
            "arduino-stue": [
                {"sensortag": "currenttemp", "sensorvalue": "10187"},
                {"timestamp": "24.10.2025 16:30:03"},
            ]
        },
        {
            "ESP32_BAD": [
                {"sensorvalue": "12397", "sensortag": "mC"},
                {"sensorvalue": "40.8065", "sensortag": "Humidity"},
                {"timestamp": "19.11.2025 17:39:36"},
            ]
        },
        {
            "temp-stue": [
                {"sensorvalue": "4375", "sensortag": "mC"},
                {"sensorvalue": "47.9675", "sensortag": "Humidity"},
                {"timestamp": "19.11.2025 17:39:25"},
            ]
        },
    ]

    # Run the function
    output = get_group_temperatures(config_data, sensor_db_data)
    print(output)


def main():
    tempvalues = process_temperature_files(
        "/Users/ingeos/temp/config.json",
        "/Users/ingeos/temp/sensordb.json",
        False,
    )
    print(json.dumps(tempvalues, indent=""))
    tempvalues = process_temperature_files(
        "/Users/ingeos/temp/config.json",
        "/Users/ingeos/temp/sensordb.json",
        True,
    )
    print(json.dumps(tempvalues, indent=""))
    # test_data()


if __name__ == "__main__":
    main()
