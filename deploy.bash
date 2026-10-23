#!/bin/bash
#
# (c) Inge Os 1.01.25
#
if [[ $1 == "hytta" ]]
then
  SOURCE_DIR=/home/pi/projects/ha_hytta
  TARGET_DIR=/home/pi
elif [[ $1 == "oci" ]]
then
  SOURCE_DIR=/home/ios/projects/ha_hytta
  TARGET_DIR=/home/ios/ha_dev
elif [[ $1 == "hjemme" ]]
then
  SOURCE_DIR=/home/pi/projects/ha_hytta
  TARGET_DIR=/home/pi
elif [[ $1 == "stua" ]]
then
  SOURCE_DIR=/home/pi/projects/ha_hytta
  TARGET_DIR=/home/pi
elif [[ $1 == "brygga" ]]
then
  cp /home/pi/ha_hytta/brygga/python/* /home/pi/python/.
  cp /home/pi/ha_hytta/brygga/scripts/* /home/pi/scripts/.
  diff /home/pi/conf/siteconfig.json  /home/pi/ha_hytta/brygga/conf/siteconfig.json
  return 0
else
  echo "no deployment set, options: hjemme, stua, brygga, oci, hytta"
  exit 1
fi
set python-scripts scripts
for DDIR in $*
do
  TDIR=$TARGET_DIR/$DDIR
  if [ -d $TDIR ]; then echo $TDIR exists; else mkdir $TDIR;echo $TDIR created; fi
  echo ""
  pwd
  ls $TDIR
  echo ""
  echo -n "Continue? "
  read RESPONSE
  if [[ ${RESPONSE:0:1} == 'Y' ]] || [[ ${RESPONSE:0:1} == 'y' ]]
  then
    echo deleting $TDIR/*
    #rm $TDIR/*
    cp $SOURCE_DIR/$DDIR/* $TDIR/.
  else
     echo "deployment cancelled"
  fi
  echo "deployment complete"
done

