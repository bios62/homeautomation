#!/bin/bash
uday=`date '+%u'`
LOGFILE=/u01/iot/savetemp_${uday}.log
date >> $LOGFILE
CURRTEMP=`python /home/pi/python/getonetemp.py`
if [ $? -ne 0 ]
then
 CURRTEMP=3.14
fi
curl -X GET -H 'Content-Type: application/json' -i -k https://revebaasen.no/php/savetemp.php?temp=$CURRTEMP  2>/dev/null >>$LOGFILE
