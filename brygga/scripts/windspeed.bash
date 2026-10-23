#!/bin/bash
#
#  Source py env
#
source /home/pi/py311/bin/activate
# 
#  Get config param
#
uday=`date '+%u'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
#SCRIPT=`echo $0 | cut -f 1 -d '.'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
date >> $LOGFILE
echo "starting windspeed" >>$LOGFILE
ps -ef | grep python | grep windspeed.py >/dev/null
if [ "$?" -ne "0" ] 
then
  nohup python /home/pi/python/windspeed.py --configfile /home/pi/conf/siteconfig.json >/dev/null 2>>$LOGFILE &
fi

