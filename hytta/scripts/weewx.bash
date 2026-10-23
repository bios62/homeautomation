#!/bin/sh
#
# Set up log
#
uday=`date '+%u'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
CONFIGFILE=/home/pi/conf/siteconfig.json
LOGDIR=`cat $CONFIGFILE | jq '.logDirectory' | sed 's/"//g'`
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
TMPFILE=${LOGDIR}/curltmp
PASSWD=`cat $CONFIGFILE | jq '.weewxtargetpwd'| sed 's/"//g'`
WEEWXSSHURL=`cat $CONFIGFILE | jq '.weewxtargetsshurl'| sed 's/"//g'`
WEEWXURL=`cat $CONFIGFILE | jq '.weewxtargetwgetURL'| sed 's/"//g'`
HTML_ROOT=`cat $CONFIGFILE | jq '.weewxhtmlroot'| sed 's/"//g'`
IOTDIR=`cat $CONFIGFILE | jq '.iotDirectory'| sed 's/"//g'`
date >>$LOGFILE
#
# Set up wget and propagate filename
#
weetime=`date +'%m%d%H'`
#wgetURL='https://revebaasen.no/php/savepropertyV2.php?siteid=weewx&propertyname=weatherid&propertyvalue='${weetime}
wgetURL=$WEEWXURL'?siteid=weewx&propertyname=weatherid&propertyvalue='${weetime}
echo $wgetURL
echo $PASSWD
echo $WEEWXSSHURL
curl -i -k -H 'Content-Type: application/json' $wgetURL >$TMPFILE 2>/dev/null
grep 'HTTP/1.1 200 OK' $TMPFILE >/dev/null
if [ $? -ne 0 ] 
then
  cat $TMPFILE >>$LOGFILE
else
  echo "curl HTTP/1.1 200 OK" >>$LOGFILE
fi
#
# Build archive for transfer
#
cd  $HTML_ROOT
tar -czvf $IOTDIR/weewx.tar.gz *
#
# Transfer and set directory acordingly
#
sshpass -p $PASSWD scp ${IOTDIR}/weewx.tar.gz $WEEWXSSHURL:/www/vaer/weewx.tar.gz
sshpass -p $PASSWD ssh $WEEWXSSHURL "cd /www/vaer/;rm weewx.tar 2>/dev/null;gunzip weewx.tar.gz;mkdir weewx${weetime};cd weewx${weetime};tar -xvf ../weewx.tar"


