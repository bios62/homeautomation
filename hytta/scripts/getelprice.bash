#!bin/bash
#
#  added 14.12.24
#  Cleanup logfiles
#  Clean out logfiles older than 6 days
#
uday=`date '+%u'`
LOGDIR=`cat /home/pi/conf/siteconfig.json | jq '.logDirectory' | sed 's/"//g'`
ELPRICEAREA=`cat /home/pi/conf/siteconfig.json | jq '.elPriceArea' | sed 's/"//g'`
ELPRICFILE=`cat /home/pi/conf/siteconfig.json | jq '.elPriceFile' | sed 's/"//g'`
ELPRICEURL=`cat /home/pi/conf/siteconfig.json | jq '.elPriceURL' | sed 's/"//g'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
#
#  Find current year, month and day
#
YEAR=`date +'%Y'`
MND=`date +'%m'`
DAY=`date +'%d'`
URL="$ELPRICEURL/$YEAR/$MDN_$DAY-$ELPRICEAREA"
curl -X GET -o $ELPRICFILE "$ELPRICEURL$YEAR/${MND}-${DAY}_${ELPRICEAREA}.json"

