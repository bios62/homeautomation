import json
import logging
import sys
import re
import argparse
import urllib
import traceback
from datetime import datetime

from http.server import BaseHTTPRequestHandler, HTTPServer

#
#   pip install datetime
#   pip unsatll ntplib
#   pip3 install python-dateutil
#
#  Import Sensor post function
#
from apiPostFunction import *
from const import (
    CONST_DEFAULT_HOSTNAME as DEFAULT_HOSTNAME,
    CONST_DEFAULT_IPADDRESS as DEFAULT_IPADDRESS,
    CONST_DEFAULT_NTP_SERVER as DEFAULT_NTP_SERVER,
    CONST_DEFAULT_PORT_NUMBER as DEFAULT_PORT_NUMBER,
    CONST_DEFAULT_SENSOR_URI as DEFAULT_SENSOR_URI,
    CONST_DEFAULT_TIME_FORMAT as DEFAULT_TIME_FORMAT,
    CONST_DEFAULT_TIME_ZONE as DEFAULT_TIME_ZONE,
    CONST_GET_SENSOR_URI as GET_SENSOR_URI,
    CONST_ISALIVE_URI as ISALIVE_URI,
    CONST_SENSOR_FUNCTION as SENSOR_FUNCTION,
    CONST_SENSOR_URI as SENSOR_URI,
    CONST_SENSORDB_FILENAME as SENSORDB_FILENAME,
    CONST_SERVER_HOSTNAME as SERVER_HOSTNAME,
    CONST_SERVER_IPADDRESS as SERVER_IPADDRESS,
    CONST_SERVER_NTP_SERVER as SERVER_NTP_SERVER,
    CONST_SERVER_PORT_NUMBER as SERVER_PORT_NUMBER,
    CONST_SERVER_TIME_FORMAT as SERVER_TIME_FORMAT,
    CONST_SERVER_TIME_ZONE as SERVER_TIME_ZONE,
    CONST_SIMPLE_SERVER_NAME as SIMPLE_SERVER_NAME,
    CONST_SIMPLE_SERVER_VERSION as SIMPLE_SERVER_VERSION,
)

default_server_config = {
    SERVER_HOSTNAME: DEFAULT_HOSTNAME,
    SERVER_IPADDRESS: DEFAULT_IPADDRESS,
    SERVER_PORT_NUMBER: DEFAULT_PORT_NUMBER,
    SENSOR_URI: DEFAULT_SENSOR_URI,
    SERVER_TIME_ZONE: DEFAULT_TIME_ZONE,
    SERVER_TIME_FORMAT: DEFAULT_TIME_FORMAT,
    SERVER_NTP_SERVER: DEFAULT_NTP_SERVER,
    SENSOR_FUNCTION: None,
    SENSORDB_FILENAME: None,
}
#
# Globals
#
config = {}


#########################################################
#
# parse_config_file
#
#  Parses config file, expect JSON Format
#  creates global config, and adds default parameters missing from config file
#
# Parameters:
#
# Globals:
#   default_server_config
#
# Returns:
#   api-server_config, Dict with configuration parameters
#
#########################################################
def parse_config_file(filename, logging):
    #
    #  Open config file and load as json
    #
    with open(filename, "r") as cfile:
        config_from_file = json.loads(cfile.read())
    #
    #  Get list of config parameters
    #
    api_server_config = default_server_config
    #
    #  Add sensor funtion
    #
    api_server_config[SENSOR_FUNCTION] = sensorSave
    #
    # Iterate over config and add nonmandatory parameters
    #
    for config_name in default_server_config:
        if config_name in config_from_file:
            api_server_config[config_name] = config_from_file[
                config_name
            ]
    #
    # Iterate and call out if any parameters still are None
    #
    for config_name in api_server_config:
        if api_server_config[config_name] is None:
            print("Config Key: " + config_name + " is not set")
            return None
    return api_server_config


#########################################################
#
# start_http_server
#
# Parameters:
#   site_config  all config parameters loaded
#   logging, logging class from calling script
#
# Globals:
#   config,  global config dict
#
# Returns:
#
#########################################################
def start_http_server(site_config, logging):
    global config

    config = site_config

    if (
        config[SERVER_IPADDRESS] == ""
        and config[SERVER_HOSTNAME] == ""
    ):
        server = HTTPServer(
            ("", int(config[SERVER_PORT_NUMBER])), HTTPRequestHandler
        )
    elif config[SERVER_IPADDRESS] == "":
        server = HTTPServer(
            (
                config[SERVER_HOSTNAME],
                int(config[SERVER_PORT_NUMBER]),
            ),
            HTTPRequestHandler,
        )
    else:
        server = HTTPServer(
            (
                config[SERVER_IPADDRESS],
                int(config[SERVER_PORT_NUMBER]),
            ),
            HTTPRequestHandler,
        )
    logging.info(
        "Starting httpd at "
        + config[SERVER_HOSTNAME]
        + ":"
        + config[SERVER_PORT_NUMBER]
        + "\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    logging.info("Stopping httpd...\n")


#########################################################
#
# HTTPRequestHandler
#   implementation of BaseHTTPRequestHandler
#
#   Implemens do_POST and do_GET
#
# Globals:
#   config inherits config dict from calling script
#
#########################################################
class HTTPRequestHandler(BaseHTTPRequestHandler):

    global config

    #########################################################
    #
    #  Prosess POST API
    #
    #
    # Parameters:
    #   self
    #
    # Globals:
    #
    # Returns:
    #
    #########################################################
    def do_POST(self):

        #
        # Any Exception not catched will generate HTTP 500
        #
        try:
            #
            # Based on post URI, process the POST requests
            #
            if re.search(config[SENSOR_URI], self.path):
                #
                # Process sensorapi POST
                #
                # The format of the payload is {"sensorid":{"valuename1":"value","valuename2"":"value"...,"valuenameN"":"value"}"}
                # Example record: {"sensor2":{"values":"456","time":"13/12-24"}}
                #                 {"segment1_track2":{"operation":"start","timestamp":"07:56:23.456"}}
                # The post funtion only sanity checks the payload for JSON conformance
                #

                #
                # Read the payload
                #
                length = int(self.headers.get("content-length"))
                data = self.rfile.read(length).decode("utf8")
                logging.info("POST OP")
                logging.info("Payload: %s", data)
                #
                # Convert the payload to dict
                #
                try:
                    sensor_payload = json.loads(data)

                except Exception as e:
                    print(e)
                    logging.info("Payload not valid json")
                    logging.info(traceback.format_exc())
                try:
                    #
                    #  Valid JSON payload, call the function that processes the sensor values
                    #
                    status = config[SENSOR_FUNCTION](
                        config, sensor_payload, logging
                    )
                    if status == True:
                        logging.info("Successfully posted")
                        self.send_response(200, "Successfully posted")
                    else:
                        logging.info(
                            "Post failed with code: " + str(status)
                        )
                        self.send_response(
                            500,
                            "Post failed with code: " + str(status),
                        )
                except Exception as e:
                    print(e)
                    logging.info("Internal error in post")
                    logging.info(traceback.format_exc())
                    self.send_response(500, "Internal error in post")
                self.end_headers()
        except Exception as e:
            logging.error("Generic error handler")
            logging.error(traceback.format_exc())
            self.send_response(
                500, "Internal error in POST, view log for details"
            )
            self.end_headers()

    #########################################################
    #
    # do_GET
    #   Processes GEToperations, list all values stored in datastore
    #
    # Parameters:
    #   self
    # Globals:
    #
    # Returns:
    #
    #
    #########################################################
    def do_GET(self):
        #
        if re.search(ISALIVE_URI, self.path):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp_obj = {"Status": "ok"}
            self.wfile.write(
                bytes(
                    json.dumps(resp_obj, ensure_ascii=False), "utf-8"
                )
            )
        elif re.search(GET_SENSOR_URI, self.path):
            sensorDB = get_sensor_db(config, logging)
            if sensorDB is not None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    bytes(
                        json.dumps(sensorDB, ensure_ascii=False),
                        "utf-8",
                    )
                )
            else:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(403)
        self.end_headers()


#########################################################
#
#
# Main function
#
# Parameters:
#
# Globals:
#
#
#########################################################
def main():

    arg_parser = argparse.ArgumentParser(
        description=SIMPLE_SERVER_NAME
    )

    arg_parser.add_argument(
        "--config",
        default="apiserver.json",
        type=str,
        help="JSON format configfile",
    )
    arg_parser.add_argument(
        "--logfile",
        default=None,
        type=str,
        help="Log file for dumping results",
    )
    args = arg_parser.parse_args()
    #
    # Configure logfile
    #
    if not args.logfile is None:
        logging.basicConfig(
            filename=args.logfile,
            filemode="w",
            format="%(name)s → %(levelname)s: %(message)s",
        )
    else:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    #
    # Parse config file
    #
    config = parse_config_file(args.config, logging)
    if config is None:
        #
        # Parse failed
        #
        print(
            "Config file is not in correct JSON format, or parameter is missing"
        )
        return 1
    #
    #  Start the server
    #
    print("Starting Simple API server")
    start_http_server(config, logging)


#
# Main entry pint if started from commandline
#
if __name__ == "__main__":
    print(SIMPLE_SERVER_NAME + " " + SIMPLE_SERVER_VERSION)
    main()
