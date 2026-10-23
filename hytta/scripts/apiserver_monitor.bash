#!/bin/bash
#
# Updated: 22/8-2022
#
#  Downloads static groupconfig from cloud
#
function verify_server() {
  CURRENT_PID=$1
  #
  #  Check if the pid is alive
  #
  ps -ef | grep $CURRENT_PID | grep -v grep >/dev/null
  if [[ $? -eq 0 ]]
  then
    #
    # Check if the server responds
    #
    HTTPSTATUS=`curl -X GET -s -o $APIOUTPUTFILE -w "%{http_code}" --max-time 3 $APIURL`
    STATUSCODE=$?
    if [[ $HTTPSTATUS -eq 200 ]]
    then
      echo -n "API server is alive: ">>$LOGFILE
      cat $APIOUTPUTFILE >>$LOGFILE
      return 0      
    else
      echo "API server responded with: $HTTPSTATUS $STATUSCODE" >>$LOGFILE
      echo "Killing the server" >>$LOGFILE
      kill -9 $CURRENT_PID
      return 1
    fi
  else
    echo "The PID $1 is no longer alive" >>$LOGFILE
    return 2
  fi
}
#
# Restart function
#
function restart_server () {
  if [[ -f $PIDFILE ]]
  then
    CUR_PPID=`cat $PIDFILE`
    echo "killing $CUR_PPID for restart" >>$LOGFILE
    kill -9 $CUR_PPID
  fi
  #
  #  check if a server seems to be alive
  #
  ps -ef | grep $PYTHONSCRIPT  | grep -v grep >/dev/null
  if [[ $? -eq 0 ]]
  then
    echo "server is still running" >> $LOGFILE
    return 1
  else
    echo "restarting server" >>$LOGFILE
    start_server
  fi
}
#
#  Funtion start_Server
#
function start_server () {
  #
  #  Activate correct python envrionmentn and start with nohup
  #  Collect the pid
  source $HOME/$PYTHONENV/bin/activate
  echo "Starting server " >>$LOGFILE
  nohup python $SITEHOME/python-scripts/$PYTHONSCRIPT --config $SITEHOME/conf/apiserver.json >$LOGDIR/apiserver.out 2>$LOGDIR/apiserver.err &
  NEW_PPID=$!
  echo $NEW_PPID >$PIDFILE
  #
  # Verify if it is running
  #
  sleep 10
  verify_server $NEW_PPID
  if [[ $? -ne 0 ]]
  then
    echo "server restart failed " >>$LOGFILE
  fi

}

uday=`date '+%u'`
SCRIPT=`basename $0 |cut -f 1 -d '.'`
SITEHOME=${HA_HOME:-/home/pi}
APICONFIG=${SITEHOME}"/conf/apiserver.json"
SITECONFIG=${SITEHOME}"/conf/siteconfig.json"
if ! [[ -f  $SITECONFIG ]]
then
  echo "HA_HOME not set or config dir $SITECONFIGDIR missing"
  exit 1
fi
PYTHONENV=`cat $SITECONFIG | jq '.pythonvenvdir' -r`
IPADDRESS=`cat $APICONFIG | jq '.ipaddress' -r`
PORTNUMBER=`cat $APICONFIG | jq '.portnumber' -r`
SERVER_HOSTNAME=`cat $APICONFIG | jq '.hostname' -r`
LOGDIR=`cat $SITECONFIG | jq '.logDirectory' -r `
APIURI='/isalive'
APIOUTPUTFILE=$LOGDIR/apiserver_alive.json
HTTP='http://'
APIURL=${HTTP}${IPADDRESS}':'${PORTNUMBER}${APIURI}
LOGFILE=${LOGDIR}/${SCRIPT}_${uday}.log
PIDFILE=$LOGDIR/apiserver.pid
PYTHONSCRIPT=apiserver.py
date >> $LOGFILE
#
#  If restart is on the commandline, restart server
#
if [[ $1 == "restart" ]]
then
  restart_server
  exit $?
fi
#
# Verify if PID file exists and if restart i issued, kill it.
#
if [[ -f $PIDFILE ]]
then
  CUR_PPID=`cat $PIDFILE`
  verify_server $CUR_PPID
  SERVER_STATUS=$?
  if [[ $SERVER_STATUS -eq 0 ]];then
     echo "Server is healthy" >>$LOGFILE
     exit 0
  fi
else 
  echo "PID file is missing, server is not running" >>$LOGFILE
fi
#
# In anycase restart the server
#
start_server
#
# Verify if it is running
#
sleep 10
verify_server $NEW_PPID
if [[ $? -ne 0 ]]
then
  echo "server restart failed " >>$LOGFILE
fi
