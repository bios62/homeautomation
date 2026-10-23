#!/bin/bash
ENV=/home/pi/py3env
PYSCRIPT=/home/pi/python-scripts/getds1820V2.py
source $ENV/bin/activate
TEMP_VALUE=`python $PYSCRIPT --tempfile - `
TVALUE=`echo $TEMP_VALUE  | awk '// {print($2)}' | sed 's/,//'`
bash /home/pi/scripts/savesensor_njq.bash 'ds1820-stue' celsius $TVALUE

