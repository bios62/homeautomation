#!/bin/bash
ENV=/home/pi/py3env
PYSCRIPT=/home/pi/python-scripts/getds1820.py
source $ENV/bin/activate
TVALUE=`python /home/pi/python-scripts/getds1820.py --tempfile -  | awk '// {print($2)}' | sed 's/,//'`
bash /home/pi/scripts/savesensor_njq.bash 'ds1820-stue' TEMP $TVALUE

