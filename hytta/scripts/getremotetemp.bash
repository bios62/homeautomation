#!/bin/bash
#
# Updated: 22/8-2022
#
#  Downloads static groupconfig from cloud
#
uday=`date '+%u'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
CONFIGFILE=/home/pi/conf/siteconfig.json
FILE=`cat /home/pi/conf/siteconfig.json | jq '.remotetempfile' | sed 's/"//g'`
PYSCRIPT=getds1820.py
date >> $LOGFILE
PWD=`cat $CONFIGFILE | jq '.stuepipwd' | sed 's/"//g'`
#
# setup environment
#
REMTEMP=`sshpass -p $PWD ssh pi@stue-pi "bash /home/pi/scripts/gettemp.bash 2>/dev/null"`
if [ $? -ne 0 ]
then
  rm $FILE >>$LOGFILE
  echo "Remote command failed" >>$LOGFILE
  exit $?
fi
#JSONTEMP=`echo '{"temp":"'${REMTEMP}'"}'`
#echo $JSONTEMP>>$FILE
#echo "Captured "${JSONTEMP} >>$LOGFILE
echo ${REMTEMP} >>$LOGFILE
echo $REMTEMP>$FILE

