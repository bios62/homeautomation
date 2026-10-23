#!/bin/bash
#
#  savetemp
#  Changelog
#  12/01-2025 Initial Code
#
#  Script that uses curl to save temp value sto sensorserver
#
# Do sudo to root to execute python script
#
# Input paramerters
#   $1 = SENSOR name
#   $2 = senortag
#   $3 = value
#
SCRIPT=`basename $0 |cut -f 1 -d '.'`
uday=`date '+%u'`
APICONFIG="/home/pi/conf/apiserver.json"
SITECONFIG=/home/pi/conf/siteconfig.json
#IPADDRESS=`cat $APICONFIG | jq '.ipaddress' -r`
IPADDRESS=`cat $APICONFIG | grep ipaddress | cut -d ':' -f 2 | sed 's/"//g' | sed 's/,//'`
#PORTNUMBER=`cat $APICONFIG | jq '.portnumber' -r`
PORTNUMBER=`cat $APICONFIG | grep portnumber | cut -d ':' -f 2 | sed 's/"//g' | sed 's/,//'`
#HOSTNAME=`cat $APICONFIG | jq '.hostname' -r`
HOSTNAME=`cat $APICONFIG | grep hostname | cut -d ':' -f 2 | sed 's/"//g' | sed 's/,//'`
#APIURI=`cat $APICONFIG | jq '.sensoruri' -r`
APIURI=`cat $APICONFIG | grep sensoruri | cut -d ':' -f 2 | sed 's/"//g' | sed 's/,//'`
HTTP='http://'
#LOGDIR=`cat $SITECONFIG | jq '.logDirectory' -r`
LOGDIR=`cat $SITECONFIG | grep logDirectory | cut -d ':' -f 2 | sed 's/"//g' | sed 's/,//'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
date >> $LOGFILE
#
# Validate input parameters
#
if [ $# -ne 3 ]
then
   echo "Usage: " $SCRIPT " sensorname sensortag value"
   exit 1
fi
#
# Create payload
#
if [[ "$HOSTNAME" == "" || "$HOSTNAME" == null ]]
then
    USEHOST=$IPADDRESS
else
    USEHOST=$HOSTNAME
fi
URL=${HTTP}${USEHOST}":"${PORTNUMBER}${APIURI}
PAYLOAD='{"objecttag":"'$1'","sensors":[{"sensortag":"'$2'","sensorvalue":"'$3'"}]}'
HTTP_CODE=`curl -X POST -d $PAYLOAD -s -o /dev/null -w "%{http_code}" $URL`
STATUS_CODE=$?
if [[ $STATUS_CODE -eq 0 ]]
then
  echo "HTTP_CODE: "$HTTP_CODE
else
  echo "Error Code: "$STATUS_CODE
fi

