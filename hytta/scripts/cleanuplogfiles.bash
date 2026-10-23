#!bin/bash
#
#  added 14.12.24
#  Cleanup logfiles
#  Clean out logfiles older than 6 days
#
uday=`date '+%u'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
FILES=`find $LOGDIR -name '*log' -mtime +4`
for I in $FILES
do 
    ls -l $I >>$LOGFILE
    rm $I >> $LOGFILE
done
