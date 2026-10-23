# ha_hytta

Home automation and monitoring for three sites:

- `hytta` — the main cabin installation
- `brygga` — the pier/boathouse installation
- `stua` — the living-room installation

Each site has its own directory directly below the project root. Site-specific
configuration, Python programs, and shell scripts belong inside that site's
directory rather than in shared root-level `conf/`, `python-scripts/`, or
`scripts/` directories.

## Project structure

```text
ha_hytta/
├── hytta/
│   ├── conf/             # Site configuration
│   ├── python-scripts/   # Python services and utilities
│   └── scripts/          # Shell scripts and cron entry points
├── brygga/
│   ├── conf/
│   ├── python/           # Python programs for brygga
│   ├── scripts/
│   └── docs/             # Site-specific documentation
├── stua/
│   ├── conf/
│   ├── python-scripts/
│   └── scripts/
├── devices/              # Microcontroller/device source shared by the sites
├── php/                  # Web pages and dashboards
├── ords/                 # Oracle REST Data Services definitions and notes
├── sql/                  # Database scripts
└── API_INVENTORY.md      # Outbound APIs used by project source files
```

The three site directories follow the same logical organization. A site may
contain only the files it needs; for example, `brygga` also has local
documentation and currently names its Python directory `python/`.

When adding or changing site-specific functionality, work in the matching site
directory. Commands in later sections that use paths such as
`/home/pi/scripts` describe the historical Raspberry Pi deployment layout. In
this repository, the equivalent source is under `<site>/scripts`, for example
`hytta/scripts/termostat.bash`.

## Changelog

31/7-26: reorganized configuration, Python, and shell sources by site

2/1-24: removed py2 requirement

## Connections

Autonomous DB:

  ---------------------------------------------------------
  Usename   Password     Connect string   tenant
  --------- ------------ ---------------- -----------------
  iot       450lclcl   Iosp\_low        Ios62
                                          
                                          Gmail/82Q\#\#\#
  ---------------------------------------------------------

Python2 in addition to python 3

Python3

sudo apt-get install python

python2
As of October 2023, Python2 is no longer required

curl [https://bootstrap.pypa.io/pip/2.7/get-pip.py --output
get-pip.py](https://bootstrap.pypa.io/pip/2.7/get-pip.py%20--output%20get-pip.py)

python2 get-pip.py

pip2 install virtualenv

sudo apt-get install python3

virtualenv -p /usr/bin/python2 tplink\_venv

## PIP Installs 
pip install pytz
pip install requests
pip install --upgrade pip

## OS Install

WiFi config


VNC install



sudo apt-get sshpass
vi /etc/hosts     
192.168.0.110   stue-pi rpistue
192.168.0.108   rpigang


Enable Serial device for windpeed


DS1820 temp sensor

1\. At the command prompt, enter sudo nano /boot/config.txt, then add
(later versions /boot/firmware/config.txt)
this to the bottom of the file:

dtoverlay=w1-gpio

2\. Exit Nano, and reboot the Pi with sudo reboot

3\. Log in to the Pi again, and at the command prompt enter 

sudo modprobe w1-gpio

4\. Then enter sudo modprobe w1-therm

https://www.circuitbasics.com/raspberry-pi-ds18b20-temperature-sensor-tutorial/


Linux RAM Disk
==============
/etc/fstab
tmpfs /u01/iot tmpfs nodev,nosuid,size=1000M 0 0

mkdir -p /u01/iot
mount -a



Data modell
===========

Configuration tables

CREATE TABLE "IOT"."TEMPGROUPMEMBERS"

( "TGMID" NUMBER(\*,0),

"GROUPID" NUMBER(\*,0),

"MEMBERNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

PRIMARY KEY ("TGMID")

CREATE TABLE "IOT"."TEMPGROUPS"

( "GROUPID" NUMBER(\*,0),

"GROUPNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"LOWTEMP" NUMBER(5,2),

"HIGHTEMP" NUMBER(5,2),

"SELECTEDTEMP" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"INUSE" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"SENSORTYPE" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

"SENSORCONFIG" VARCHAR2(100 BYTE) COLLATE "USING\_NLS\_COMP",

"USETERMOSTAT" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP",

"ADJUSTED\_LOW" NUMBER(7,2),

CONSTRAINT "CHK\_INUSE" CHECK (upper(inuse) in ('Y','N')) ENABLE,

CONSTRAINT "CHK\_SELECTEDTEMP" CHECK (upper(selectedtemp) in ('H','L'))
ENABLE,

PRIMARY KEY ("GROUPID")

Logging

CREATE TABLE "IOT"."IOTLOGS"

( "ID" NUMBER(\*,0) NOT NULL ENABLE,

"LOGNAME" VARCHAR2(100 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"LOGTIME" TIMESTAMP (6) DEFAULT CURRENT\_TIMESTAMP,

"SITEID" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"LOGVALUE" VARCHAR2(60 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

CONSTRAINT "IOTLOGS\_PK" PRIMARY KEY ("ID")

CREATE TABLE "IOT"."JIOTLOGS"

( "ID" VARCHAR2(255 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"CREATED\_ON" TIMESTAMP (6) DEFAULT sys\_extract\_utc(SYSTIMESTAMP) NOT
NULL ENABLE,

"LAST\_MODIFIED" TIMESTAMP (6) DEFAULT sys\_extract\_utc(SYSTIMESTAMP)
NOT NULL ENABLE,

"VERSION" VARCHAR2(255 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"JSON\_DOCUMENT" BLOB,

CHECK ("JSON\_DOCUMENT" is json format oson (size limit 32m)) ENABLE,

PRIMARY KEY ("ID")

CREATE TABLE "IOT"."TEMPGROUPMEMBERS"

( "TGMID" NUMBER(\*,0),

"GROUPID" NUMBER(\*,0),

"MEMBERNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

PRIMARY KEY ("TGMID")

CREATE TABLE "IOT"."TEMPGROUPS"

( "GROUPID" NUMBER(\*,0),

"GROUPNAME" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"LOWTEMP" NUMBER(5,2),

"HIGHTEMP" NUMBER(5,2),

"SELECTEDTEMP" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL
ENABLE,

"INUSE" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP" NOT NULL ENABLE,

"SENSORTYPE" VARCHAR2(20 BYTE) COLLATE "USING\_NLS\_COMP",

"SENSORCONFIG" VARCHAR2(100 BYTE) COLLATE "USING\_NLS\_COMP",

"USETERMOSTAT" VARCHAR2(1 BYTE) COLLATE "USING\_NLS\_COMP",

"ADJUSTED\_LOW" NUMBER(7,2),

CONSTRAINT "CHK\_INUSE" CHECK (upper(inuse) in ('Y','N')) ENABLE,

CONSTRAINT "CHK\_SELECTEDTEMP" CHECK (upper(selectedtemp) in ('H','L'))
ENABLE,

PRIMARY KEY ("GROUPID")

Rest API
========

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  URL                                                    HTTP Method                    USAGE                                            SQL
  ------------------------------------------------------ ------------------------------ ------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  currentsetting/                                        GET                            Fetch current tempconfiguration setting          select groupname,lowtemp,hightemp,selectedtemp,nvl(adjusted\_low,lowtemp) adjustedtemp from tempgroups

  groupconfig/                                           GET                            Fetch current sensor configuration setting       select groupid,groupname,inuse,sensortype,sensorconfig,usetermostat,lowtemp,hightemp from tempgroups

  groupconfigall                                         GET                            NOT IN USE, replaced by currentsetting           select groupid,groupname,inuse,sensortype,sensorconfig,usetermostat,lowtemp,hightemp,selectedtemp from tempgroups

  Iotstats/                                              GET                            Fetch all stats for a site **In use????**        select l.logname name,l.logvalue value,l.logtime logtime from iotlogs l where l.siteid=:siteid and l.logtime = (select max(l2.logtime) from iotlogs l2 where l2.logname = l.logname)

  Iotstats/                                              POST                           Inserts one statistics                           declare
                                                                                                                                         
                                                         Payload:                                                                        id iotlogs.id%type;
                                                                                                                                         
                                                         {"siteid": "hytta",                                                             BEGIN
                                                                                                                                         
                                                         "logname": "hytte\_sov4",                                                       INSERT INTO iotlogs(logname, logtime, siteid, logvalue)
                                                                                                                                         
                                                         "logvalue": "OFF"}                                                              VALUES (:logname,sysdate,:siteid,:logvalue)
                                                                                                                                         
                                                                                                                                         RETURNING ID INTO id;
                                                                                                                                         
                                                                                                                                         :status := 201;
                                                                                                                                         
                                                                                                                                         END;

  Iotstats/:siteid                                       GET                            Fetch all stats for a site **In use????**        select l.logname name,l.logvalue value,to\_char(l.logtime,'DD/mm-yy hh24:mi:ss') logtime from iotlogs l where l.siteid=:siteid and l.logtime = (select max(l2.logtime) from iotlogs l2 where l2.logname = l.logname
                                                                                                                                         
                                                                                                                                         and l2.logtime&gt;(sysdate-(to\_number(to\_char(sysdate,'hh24'))/24)))

  members/                                               GET                            Fetch all members of a temp group, static info   select t.groupname,m.membername from tempgroups t,tempgroupmembers m where m.groupid=t.groupid

  setrange/                                              POST                           Updates static temp settings                     begin setrange(:groupname,:lowtemp,:hightemp,:p\_status);commit; end;
                                                                                                                                         
                                                         Payload: groupname,hightemp,                                                    
                                                                                                                                         
                                                         lowtemp                                                                         

  settemp/                                               POST                           Activates high or low temp, based on groupid     begin settemp(:groupid,:selectedtemp,:p\_status);commit; end;
                                                                                                                                         
                                                         Payload:                                                                        
                                                                                                                                         
                                                         Groupid, selectedtemp                                                           

  settempbyname/                                         POST                           Activates high or low temp, based on groupname   begin settempbyname(:groupname,:selectedtemp,:p\_status);commit; end;
                                                                                                                                         
                                                         Payload:                                                                        
                                                                                                                                         
                                                         Groupid, selectedtemp                                                           

  soda/latest/jiotlogs                                   POST                           Uploads collection of stats to json table        

  soda/latest/jiotlogs                                   PUT                            Creates JSON table                               

  https://revebaasen.no/php/saveipV3.php ?siteid=hytta   GET                            Saves current IP to one.com                      
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Scripts

The table below describes the `hytta` scripts. Corresponding site-specific
scripts live under `brygga/scripts/` and `stua/scripts/`.

  hytta/scripts/getlocaltemp.bash            Run as Bash; uses elevated access for the device file and calls `hytta/python-scripts/getds1820.py`
  ----------------------------------------- ------------------------------------------------------------------------------------------------------------------------
  hytta/scripts/saveip.bash                 Saves the current IP address through the configured REST API
  hytta/scripts/getsocketstate.bash         Gets the status of active TP-Link sockets and saves it in the socket file
  hytta/scripts/updategroupconfig.bash      Downloads static group configuration through REST; calls `hytta/python-scripts/updategroupconfig.py`

ORDS
=========
Siste versjon iotv1      
ords_271223_v1_only.sql    

For authentiserte brukere, byttet skjema til iotv2

Cron Jobs
=========

4,9,14,19,24,29,34,39,44,49,54,59 \* \* \* \*
/home/pi/scripts/saveip.bash

\* \* \* \* \* bash /home/pi/scripts/getlocaltemp.bash

15,45 \* \* \* \* bash /home/pi/scripts/getsocketIP.bash

15,45 \* \* \* \* bash /home/pi/scripts/updategroupconfig.bash

\#3,18,33,48 \* \* \* \* date &gt;&gt;/home/pi/logs/tpstatus;bash
/home/pi/scripts/termostat.bash &gt;&gt;/home/pi/logs/tpstatus

\#15,45 \* \* \* \* /home/pi/scripts/wee\_start.sh
# homeautomation
