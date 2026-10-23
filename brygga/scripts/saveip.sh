#!/bin/bash
uday=`date '+%u'`
LOGFILE=/u01/iot/saveip_${uday}.log
date >> $LOGFILE
#curl -H 'Content-Type: application/json' -k -i https://revebaasen.no/php/saveipV2.php?siteid=brygge2  2>/dev/null| grep '89.' >>$LOGFILE
curl -i -k -H 'Content-Type: application/json' https://revebaasen.no/php/saveipV3.php?siteid=brygge2  2>/dev/null| grep '89.' >>$LOGFILE
