#!/bin/bash
#
#  Same for hytta and brygga
# derives siteid from config file
#
uday=`date '+%u'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
IPURL=`cat /home/pi/conf/siteconfig.json | jq '.getmyip2URL' | sed 's/"//g'`
SITEID=`cat /home/pi/conf/siteconfig.json | jq '.siteid' | sed 's/"//g'`
IOTSTATSURL=`cat /home/pi/conf/siteconfig.json | jq '.iotstatsURL' | sed 's/"//g'`
#SCRIPT=`echo $0 | cut -f 1 -d '.'`
SCRIPT=`basename $0 |cut -f 1 -d '.'` 
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
date >> $LOGFILE
echo 'fecth ip getmyip1URL' >>$LOGFILE
curl -i -k -H 'Content-Type: application/json' https://revebaasen.no/php/saveipV3.php?siteid=$SITEID  2>/dev/null| grep '89.' >>$LOGFILE
#
#  Build payload for getip from getmyip2URL
#
IPRESULT=`curl -s -k -o - http://ip-api.com/json/ | jq '.query' | sed 's/"//g'`
PAYLOAD='{"logname":"ipaddress(ip-api.com)","siteid":"'${SITEID}'","logvalue":"'${IPRESULT}'"}'
echo 'fecth ip getmyip2URL' >>$LOGFILE
echo $PAYLOAD >>$LOGFILE
curl -X POST -i -k -o - -d $PAYLOAD -H 'Content-Type: application/json' $IOTSTATSURL  2>/dev/null | grep 'HTTP' >>$LOGFILE
#curl -X POST -v -k -o - -d $PAYLOAD -H 'Content-Type: application/json' $IOTSTATSURL  
